# Jobeas AI platform

This document describes how AI is organized in Jobeas today, where it is heading, and how features such as **resume–job evaluation** fit into the product.

For legacy OpenAI parsing/assistant notes, see [`../README.md`](../README.md). This file is the source of truth for **configurable prompts**, **model catalog**, and **structured Gemini outputs**.

---

## Table of contents

1. [Vision](#vision)
2. [Architecture overview](#architecture-overview)
3. [Data model](#data-model)
4. [Model and temperature resolution](#model-and-temperature-resolution)
5. [Multi-provider roadmap](#multi-provider-roadmap)
6. [Resume–job evaluation](#resumejob-evaluation)
7. [Structured output schema](#structured-output-schema)
8. [Product use cases (including dashboard)](#product-use-cases-including-dashboard)
9. [Admin and operations](#admin-and-operations)
10. [Adding a new AI task](#adding-a-new-ai-task)
11. [Configuration reference](#configuration-reference)
12. [Testing and calibration](#testing-and-calibration)

---

## Vision

**Goal:** Every AI capability in Jobeas should be driven from the database—not hardcoded prompts or model names in application code.

| Layer | Purpose | Today | Direction |
|-------|---------|-------|-----------|
| **AIService** | Named product capability (`cover_letter`, `resume_job_evaluation`, …) | Partially adopted | All new AI features register a service slug |
| **AIPromptConfiguration** | Versioned system prompts + default model/temperature per variant | Used for cover letter, optimization, evaluation | A/B prompts, strict vs pragmatic evaluators |
| **AIModel** | Catalog of provider + `model_id` (e.g. `gemini-2.5-pro`, `gpt-4o`) | Gemini + OpenAI enum; runtime is Gemini-first for eval | Claude and others; provider-specific clients |
| **Structured output** | Pydantic schemas validated before persist | `ResumeJobEvaluationPayload` (Gemini) | One schema module per structured task |
| **Run records** | Audit trail + user-facing history | `ResumeJobEvaluation` (admin playground) | User-scoped runs linked to applications |

**Principle:** Code wires *how* to call AI (client, schema, persistence). Admins and seeds define *what* to say (prompt) and *which* model to use (catalog + prompt FK).

---

## Architecture overview

```mermaid
flowchart TB
    subgraph admin [Django Admin]
        AIModelAdmin[AI Models]
        PromptAdmin[AI Prompt Configurations]
        EvalAdmin[Resume-job evaluations playground]
    end

    subgraph db [Database]
        AIService[(AIService)]
        AIPrompt[(AIPromptConfiguration)]
        AIModel[(AIModel)]
        ResumeEval[(ResumeJobEvaluation)]
    end

    subgraph code [Python modules]
        PromptUtils[prompt_utils.get_ai_prompt]
        GenConfig[generation_config.resolve_generation_config]
        EvalSvc[resume_job_evaluation.evaluate_resume_against_job]
        GeminiClient[gemini_client / gemini_service]
        Schema[gemini_schema.ResumeJobEvaluationPayload]
    end

    subgraph future [Planned]
        OpenAIClient[OpenAI client adapter]
        ClaudeClient[Anthropic client adapter]
        UserDashboard[User fit dashboard]
    end

    AIModelAdmin --> AIModel
    PromptAdmin --> AIPrompt
    PromptAdmin --> AIService
    PromptAdmin --> AIModel
    EvalAdmin --> ResumeEval

    EvalSvc --> GenConfig
    GenConfig --> AIPrompt
    GenConfig --> AIModel
    EvalSvc --> PromptUtils
    EvalSvc --> GeminiClient
    GeminiClient --> Schema
    EvalSvc --> ResumeEval

    AIPrompt --> AIService
    AIPrompt --> AIModel
    ResumeEval --> AIPrompt
    ResumeEval --> AIModel

    UserDashboard -.-> ResumeEval
    OpenAIClient -.-> AIPrompt
    ClaudeClient -.-> AIPrompt
```

**Request flow (resume–job evaluation):**

1. Load `AIPromptConfiguration` for `AIService.slug = resume_job_evaluation` (or admin-selected variant).
2. `resolve_generation_config(prompt_config)` → `model_id`, `temperature`, `ai_model_id`.
3. Build user message from job description + resume plain text.
4. Call Gemini with `response_schema=ResumeJobEvaluationPayload`.
5. Pydantic-validate response; on success, persist to `ResumeJobEvaluation` (denormalized columns + full `evaluation_json`).

---

## Data model

### `AIService`

Represents a **product-level AI capability**.

| Field | Role |
|-------|------|
| `name` | Display name |
| `slug` | Stable code identifier (e.g. `resume_job_evaluation`, `cover_letter`) |
| `description` | What the service does |
| `is_active` | Soft kill switch |

**Convention:** Application code imports a constant slug (e.g. `RESUME_JOB_EVALUATION_SERVICE_SLUG`) and never magic-strings prompts in views.

### `AIPromptConfiguration`

A **versioned prompt variant** for one service.

| Field | Role |
|-------|------|
| `service` | FK → `AIService` |
| `name` / `slug` | Human name + code id (`v1-0`, `v1-1-strict`, …) |
| `system_prompt` | Full system instruction sent to the model |
| `ai_model` | FK → `AIModel` (default model for this variant) |
| `temperature` | Optional override (0–2) |
| `is_default` | One default per service (enforced on save) |
| `is_active` | Hide without deleting |

**Comparing models:** Duplicate the prompt row, change `ai_model` to `gemini-2.5-flash` vs `gemini-2.5-pro`, keep the same `system_prompt` to isolate model behavior.

**Comparing instructions:** Duplicate the row, change `slug` and `system_prompt` (see `eval_prompts.py` for source text to seed).

### `AIModel`

**Provider-agnostic model catalog.**

| Field | Role |
|-------|------|
| `provider` | `gemini` \| `openai` (extend for `anthropic`, etc.) |
| `model_id` | Provider API id (`gemini-2.5-flash`, `gpt-4o`, …) |
| `display_name` | Admin/UI label |
| `default_temperature` | Suggested default when prompt leaves temperature blank |
| `is_active` / `sort_order` | Admin dropdown ordering |

Seeded by:

```bash
python manage.py setup_ai_models
```

### `ResumeJobEvaluation`

Persisted **evaluation run** (admin playground today; user-facing runs later).

| Field group | Fields |
|-------------|--------|
| **Labeling** | `name`, `description`, `conclusion` (conclusion auto-filled from `proceed_reasoning` on successful save) |
| **Inputs** | `job_description`, `resume_text`, `prompt_config` |
| **Run snapshot** | `ai_model`, `gemini_model`, `temperature_used`, `instruction_slug` |
| **Denormalized results** | `succeeded`, `recommendation`, `overall_score`, `optimization_potential`, `error_message` |
| **Full payload** | `evaluation_json`, `raw_response_text` |

Denormalized fields power list views and simple queries; `evaluation_json` is the canonical structured result for dashboards and APIs.

---

## Model and temperature resolution

Implemented in `ai_service/generation_config.py`.

**Precedence (highest wins):**

1. Per-run overrides (future user/API params; admin preview may add these later)
2. `AIPromptConfiguration.ai_model` + `temperature`
3. `AIModel.default_temperature`
4. Django settings / env fallbacks (`GEMINI_RESUME_JOB_EVAL_MODEL`, `GEMINI_RESUME_JOB_EVAL_TEMPERATURE`) — **optional**; omit in production when prompts are linked in admin

```python
from ai_service.generation_config import resolve_generation_config

gen = resolve_generation_config(prompt_config)
# gen.model_id, gen.temperature, gen.ai_model_id, gen.ai_model_display_name
```

**Important:** Resume–job evaluation currently **executes only through the Gemini client**. The catalog already stores OpenAI rows for other services; a future `ProviderRouter` will select `gemini_client` vs `openai_client` based on `AIModel.provider`.

---

## Multi-provider roadmap

### Today

| Provider | Catalog (`AIModel`) | Structured tasks | Prompt DB |
|----------|---------------------|------------------|-----------|
| **OpenAI** | Yes | Resume parsing, cover letter, optimization, assistant (`open_ai.py`, `structured_resume.py`) | `setup_ai_prompts` |
| **Google Gemini** | Yes | Resume–job evaluation | `setup_resume_job_evaluation` |

### Target shape

```text
evaluate_task(service_slug, prompt_slug, user_payload, *, ai_model_id=None)
    → prompt_config = load_prompt(service_slug, prompt_slug)
    → gen = resolve_generation_config(prompt_config, ai_model_id=...)
    → client = get_client_for_provider(prompt_config.ai_model.provider)
    → schema = SCHEMA_REGISTRY[service_slug]  # optional
    → return client.generate_structured(...) or client.generate_text(...)
```

**Adding Claude (example):**

1. Add `anthropic` to `AIModel.Provider`.
2. Implement `anthropic_client.py` with the same interface as `gemini_generate_structured_sync` where possible.
3. Seed models (`claude-sonnet-4-…`) via `setup_ai_models`.
4. Point a new or existing `AIPromptConfiguration` at that `AIModel`.

No change to `AIService` / prompt versioning model—only the execution layer branches by provider.

---

## Resume–job evaluation

### Purpose

**Pre-flight fit check** before resume optimization or cover letter generation: “Should this candidate pursue this role honestly, given only what is on the resume?”

- Impartial analyst; must not invent experience.
- Distinguishes **surface optimization** (wording, framing) from **foundational gaps** (wrong role family, missing hard requirements).

### Service identity

| Constant | Value |
|----------|--------|
| `RESUME_JOB_EVALUATION_SERVICE_SLUG` | `resume_job_evaluation` |
| Default prompt slug | `v1-0` |
| Instruction source | `ai_service/eval_prompts.py` → `EVALUATOR_INSTRUCTION_V1_0` (seeded into DB) |

### Code entry points

| Function | Module | Use |
|----------|--------|-----|
| `evaluate_resume_against_job(job_description, resume_text, prompt_config=…)` | `resume_job_evaluation.py` | Run Gemini + validate |
| `persist_resume_job_evaluation_result(pk, result, …)` | `resume_job_evaluation.py` | Write DB after success |
| `parse_pending_evaluation_result(raw)` | `resume_job_evaluation.py` | Admin Save with hidden JSON |
| `conclusion_from_evaluation(eval_data)` | `resume_job_evaluation.py` | Extract `proceed_reasoning` for `conclusion` field |

### Bootstrap

```bash
python manage.py setup_ai_models
python manage.py setup_resume_job_evaluation
# optional: refresh system_prompt text
python manage.py setup_resume_job_evaluation --force
```

`entrypoint.sh` runs both when `SKIP_BOOTSTRAP_DATA` is not set (deploy).

### Recommendation labels

`Strong Fit` · `Good Fit` · `Moderate Fit` · `Weak Fit` · `Poor Fit`

**Calibration notes (from production testing):**

- **Poor Fit (~25):** Wrong role family (e.g. macOS endpoint engineer vs Python web resume)—trust this; do not mass-apply.
- **Weak Fit (~40):** Right lane, bar too high (senior + React when resume is mid-level Django)—stretch apply or target lower bar.
- **Strong Fit (~90+):** Rare near-perfect stack/seniority match.

Use the **same prompt slug** when comparing models; use **different prompt slugs** when comparing instruction versions.

---

## Structured output schema

Defined in `ai_service/gemini_schema.py` as **`ResumeJobEvaluationPayload`** (Pydantic).

Gemini receives this class as `response_schema`; the server **always re-validates** with Pydantic before treating a run as successful. Prompts must stay aligned with these fields (documented in `eval_prompts.py`).

### Top-level fields

| Field | Type | Meaning |
|-------|------|---------|
| `overall_score` | int 0–100 | Aggregate fit |
| `recommendation` | enum | Strong/Good/Moderate/Weak/Poor Fit |
| `optimization_potential` | int 0–100 | How much resume *wording* could help (not inventing skills) |
| `confidence` | High / Medium / Low | Confidence in the judgment (not “confidence you’ll get hired”) |
| `strengths` | string[] | Evidence-backed positives |
| `gaps` | string[] | Missing or weak areas |
| `hard_requirement_analysis` | object[] | Per-requirement breakdown |
| `transferable_skills` | object[] | Adjacent skills with evidence |
| `risk_level` | Low / Moderate / High | Hiring risk if proceeding |
| `dimension_summaries` | object | Narrative dimensions + `proceed_reasoning` |

### `hard_requirement_analysis[]`

| Field | Description |
|-------|-------------|
| `requirement` | Text from job posting |
| `match_status` | `met` \| `partially_met` \| `transferable` \| `missing` \| `unclear` \| `unrecoverable` |
| `evidence_quote` | Quote from resume (empty if none) |
| `notes` | Analyst notes |

### `dimension_summaries`

| Key | Focus |
|-----|--------|
| `core_competency_match` | Stack, tools, platforms |
| `seniority_match` | Years, ownership, level |
| `domain_match` | Industry / problem domain |
| `operational_experience_match` | Prod, on-call, CI/CD, reliability |
| `optimization_surface_vs_foundational_notes` | Wording vs real qualification gaps |
| `proceed_reasoning` | **Action summary** — copied to `ResumeJobEvaluation.conclusion` on persist |

### Example (minimal)

```json
{
  "overall_score": 72,
  "recommendation": "Moderate Fit",
  "optimization_potential": 65,
  "confidence": "Medium",
  "strengths": ["Production Django on GCP"],
  "gaps": ["No React listed"],
  "hard_requirement_analysis": [
    {
      "requirement": "2+ years Python backend",
      "match_status": "met",
      "evidence_quote": "TravelTAF Platform 2023-09 — Present",
      "notes": ""
    }
  ],
  "transferable_skills": [],
  "risk_level": "Moderate",
  "dimension_summaries": {
    "core_competency_match": "Strong Python web overlap.",
    "seniority_match": "",
    "domain_match": "",
    "operational_experience_match": "",
    "optimization_surface_vs_foundational_notes": "",
    "proceed_reasoning": "Worth a tailored apply if willing to ramp on React."
  }
}
```

---

## Product use cases (including dashboard)

The structured payload is designed so the **UI never has to parse free text**.

### Suggested user dashboard (not built yet)

For a saved job application or a “compare to job” action:

| UI section | JSON source |
|------------|-------------|
| Fit score gauge | `overall_score`, `recommendation` |
| “Should I apply?” | `dimension_summaries.proceed_reasoning`, `risk_level` |
| Requirements checklist | `hard_requirement_analysis` (filter `missing` / `partially_met`) |
| Strengths to lead with | `strengths` |
| Honest gaps to address | `gaps` |
| Resume tips only | High `optimization_potential` + `optimization_surface_vs_foundational_notes` |
| Stretch skills | `transferable_skills` |

**Implementation sketch:**

1. Add `user` FK and optional `job_application` FK on `ResumeJobEvaluation` (or a thin `UserJobFitReport` model copying denormalized fields).
2. Call `evaluate_resume_against_job` from dashboard view/API after user pastes job description.
3. Render templates from `evaluation_json` — no second LLM call for display.
4. Gate expensive flows: if `recommendation` is `Poor Fit` and `confidence` is `High`, suggest skipping optimization unless user overrides.

### Other services (same platform pattern)

| Service slug (examples) | Output style | Schema home |
|-------------------------|--------------|-------------|
| `resume_job_evaluation` | Structured JSON | `gemini_schema.py` |
| `cover_letter` | Text | — |
| `resume_optimization` | Text / JSON (legacy) | — |
| Future: `interview_prep` | Structured Q&A | TBD |

Each new structured task: add Pydantic model → document in prompt → seed `AIService` + `AIPromptConfiguration` → implement `*_service.py` runner → persist run row.

---

## Admin and operations

### Where to configure

| Task | Location |
|------|----------|
| Edit evaluator instructions | **AI Prompt Configurations** → service “Resume-to-Job Evaluation” |
| Change default model/temperature | Same row → `ai_model`, `temperature` |
| Add Gemini/OpenAI catalog entries | **AI models** |
| Run manual tests | **Resume-job evaluations** (playground) |

**Deploy verification:** `entrypoint.sh` runs `python manage.py check_ai_platform`. In Cloud Logging, look for `check_ai_platform: OK`. Admin header shows `AI platform <build>` (see `ai_service/platform_version.py`). Under **AI SERVICE** you should see four models including **AI models** and **Resume-job evaluations**.

### Playground workflow

1. Set **Name** / **Description** so list rows are identifiable.
2. Paste job description + resume text; choose prompt config.
3. **Get evaluation** (AJAX; no save required).
4. **Save** — persists inputs + last successful preview; fills **Conclusion** from `proceed_reasoning`.

List columns: name, recommendation, score, model, truncated description/conclusion, succeeded, created_at.

### Labeling test runs (examples)

| Name | Description |
|------|-------------|
| `Northbridge Senior — Pro` | Test resume v1 vs fictional senior Django/React JD; gemini-2.5-pro |
| `Harborline Mid — Pro` | Tailored mid-level Django/GCP match test |

---

## Adding a new AI task

Checklist for a **new structured Gemini task** (adjust for OpenAI-only tasks):

1. **Define schema** — Add Pydantic model to `gemini_schema.py` (or a dedicated `*_schema.py`).
2. **Write instruction** — Module like `eval_prompts.py` with versioned constants.
3. **Register service** — `AIService` row + management command `setup_*`.
4. **Seed prompt** — `AIPromptConfiguration` with `system_prompt`, `ai_model`, `temperature`, `slug`.
5. **Implement runner** — `evaluate_*` function: resolve config → call client → validate → return dict.
6. **Persist** — Model for audit/history (optional user FK).
7. **Admin** — Playground or inline if internal-only.
8. **Tests** — Schema validation + persist path (see `ai_service/tests.py`).

For **text-only** tasks, existing pattern applies: `get_ai_prompt(service_slug)` from `prompt_utils.py` + `open_ai.py` (migrate to `resolve_generation_config` over time).

---

## Configuration reference

### Environment variables

**Production (minimum for Gemini evaluation):** set **one** of `GEMINI_API_KEY` or `GOOGLE_API_KEY`. Model and temperature are **not** env-driven in normal operation—they come from admin after `setup_ai_models` and `setup_resume_job_evaluation`.

| Variable | Required? | Purpose |
|----------|-----------|---------|
| `GEMINI_API_KEY` or `GOOGLE_API_KEY` | **Yes** (one) | Gemini API authentication |
| `OPENAI_API_KEY` | For OpenAI features | Resume parsing, cover letter, optimization, assistant |
| `GEMINI_RESUME_JOB_EVAL_MODEL` | No | Code fallback if prompt has no `ai_model` linked |
| `GEMINI_RESUME_JOB_EVAL_TEMPERATURE` | No | Code fallback if prompt/model leave temperature unset |

Change evaluation model or temperature in **AI Prompt Configurations** (and **AI models**) without redeploying.

See `.env.example`.

### Key modules

| Module | Responsibility |
|--------|----------------|
| `models.py` | `AIService`, `AIPromptConfiguration`, `AIModel`, `ResumeJobEvaluation` |
| `generation_config.py` | Model/temperature resolution |
| `prompt_utils.py` | Load prompt text by service slug |
| `eval_prompts.py` | Versioned evaluator instructions (source for seeds) |
| `gemini_schema.py` | Pydantic schemas for Gemini structured output |
| `gemini_client.py` | Low-level sync Gemini calls |
| `gemini_service.py` | Higher-level Gemini helpers |
| `resume_job_evaluation.py` | Evaluation orchestration + persist |
| `admin.py` | Admin UX for models, prompts, playground |

---

## Testing and calibration

```bash
python manage.py test ai_service.tests.ResumeJobEvaluationSchemaTests
python manage.py test ai_service.tests.ResumeJobEvaluationPersistOnSaveTests
python manage.py test ai_service.tests.GenerationConfigResolverTests
python manage.py test ai_service.tests.ConclusionFromEvaluationTests
```

**Model calibration workflow:**

1. Fix resume text and job description.
2. Duplicate prompt config with different `ai_model` rows OR change only `system_prompt` slug.
3. Label runs with **Name** / **Description** / review **Conclusion**.
4. Compare scores only within the same `instruction_slug`; compare models only with the same prompt text.

**Known behavior:**

- `gemini-2.5-pro` is stricter on role-family mismatch than `gemini-2.5-flash`.
- `gemini-2.5-flash-lite` tends toward optimistic triage—use for cheap first pass, not final gate.

---

## Related documentation

- [`../README.md`](../README.md) — Resume parsing (RISEN), OpenAI assistant, legacy flows
- [`../eval_prompts.py`](../eval_prompts.py) — Evaluator instruction v1.0 source text
- [`../gemini_schema.py`](../gemini_schema.py) — Payload types and literals

---

*Last updated: 2026-05 — aligns with `ResumeJobEvaluation` label fields, `AIModel` catalog, and `generation_config` resolver.*
