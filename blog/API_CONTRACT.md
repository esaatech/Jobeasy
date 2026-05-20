# Blog API contract

Base path (included at site root): `/api/blog/`

All responses are JSON. Datetimes are ISO 8601 (UTC when `USE_TZ` is true).

---

## Public (no auth)

### List categories

`GET /api/blog/categories/`

```json
[
  {
    "id": 1,
    "name": "Career Tips",
    "slug": "career-tips",
    "description": "Advice for job seekers",
    "post_count": 12
  }
]
```

### Category detail

`GET /api/blog/categories/{slug}/`

Same object shape as one list item.

### List posts

`GET /api/blog/posts/`

| Query param | Description |
|-------------|-------------|
| `category`  | Filter by category slug |
| `tag`       | Posts whose `tags` JSON array contains this string (substring match) |
| `q`         | Search `title`, `excerpt`, `body` |

```json
[
  {
    "id": 1,
    "title": "How to tailor your resume",
    "slug": "how-to-tailor-your-resume",
    "excerpt": "Short plain-text summary…",
    "featured_image": "/media/blog/featured/hero.jpg",
    "category": { "id": 1, "name": "Career Tips", "slug": "career-tips", "description": "…", "post_count": 12 },
    "author_name": "Joel",
    "tags": ["resume", "ats"],
    "reading_time_minutes": 5,
    "published_at": "2026-05-01T10:00:00Z",
    "meta_title": "",
    "meta_description": ""
  }
]
```

### Post detail (includes related)

`GET /api/blog/posts/{slug}/`

List fields plus:

```json
{
  "body": "<p>HTML from CKEditor…</p>",
  "related_posts": [ /* same shape as list items, max 4 */ ],
  "created_at": "2026-04-28T08:00:00Z",
  "updated_at": "2026-05-01T10:00:00Z"
}
```

**Related posts logic**

1. If `related_posts` are set in admin → those published posts (newest first).
2. Else → up to 4 other **published** posts in the **same category**.

---

## Staff / AI (Django admin user, `IsAdminUser`)

Use session auth or token auth configured for your deployment. These endpoints are intended for:

- Admin tooling
- Future AI agents that draft posts via structured JSON

### Create post

`POST /api/blog/posts/manage/`

`Content-Type: application/json` or `multipart/form-data` (if uploading `featured_image`).

| Field | Required | Notes |
|-------|----------|-------|
| `title` | yes | |
| `body` | yes | HTML string (CKEditor output) |
| `category_slug` | yes | Must match an **active** category |
| `slug` | no | Auto-generated from title if omitted |
| `excerpt` | no | Plain text; recommended for SEO/listings |
| `status` | no | `draft` (default), `published`, `archived` |
| `tags` | no | `["resume", "interview"]` |
| `meta_title` | no | |
| `meta_description` | no | |
| `reading_time_minutes` | no | integer |
| `related_post_slugs` | no | `["other-post-slug"]` |
| `featured_image` | no | file upload |
| `published_at` | no | Set automatically when status becomes `published` |

**Example (AI draft)**

```json
{
  "title": "5 Resume Mistakes to Avoid",
  "excerpt": "Small fixes that improve ATS and recruiter readability.",
  "body": "<h2>Introduction</h2><p>…</p>",
  "category_slug": "career-tips",
  "status": "draft",
  "tags": ["resume", "ats"],
  "meta_title": "5 Resume Mistakes | Jobeas",
  "meta_description": "Avoid these common resume errors before you apply."
}
```

**Response:** `201` with write serializer fields echoed; use `GET /api/blog/posts/{slug}/` after publish for public shape.

### Update post

`PATCH /api/blog/posts/manage/{slug}/`

Same fields as create (all optional on PATCH). `category_slug` and `related_post_slugs` can be updated.

### Publish post

`POST /api/blog/posts/manage/{slug}/publish/`

Sets `status` to `published` and `published_at` if not already set. Returns full **public** detail shape.

### Manage categories

`GET /api/blog/categories/manage/` — all categories (including inactive)

`POST /api/blog/categories/manage/`

```json
{
  "name": "Interview Prep",
  "slug": "interview-prep",
  "description": "Optional",
  "is_active": true
}
```

---

## Django admin

`/admin/blog/` — create categories and posts with **CKEditor 5** (`body` field). Upload images inside the editor (requires `ckeditor5/` URL). Set manual **Related posts** or rely on same-category fallback on the API.

---

## AI integration notes

1. **BlockNote** is React-only; this stack uses **CKEditor 5** via `django_ckeditor_5` — store HTML in `body`.
2. Prefer **`excerpt`** as plain text for cards and LLM summaries; keep **`body`** as HTML.
3. Workflow: `POST manage/` with `status: "draft"` → human review in admin → `POST …/publish/` or set `status: "published"` via PATCH.
4. Use **`category_slug`** and **`related_post_slugs`** so agents do not need database IDs.
