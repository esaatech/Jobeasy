# Job Service App

## Recent Changes (2024-07)

### Major Updates

- **Multi-step Job Application Form**: The job application form is now modular, with steps for job details, location, and contact info.
- **Location Step Redesign**:
  - Users can select multiple countries and states using a dialog-based picker (REST Countries API).
  - City is now a plain text input (always visible).
  - Distance preference is now a slider (0–200 miles).
  - States dropdown prepends "Remote" and "Hybrid" options.
- **Frontend Robustness**:
  - Dialog is re-created each time to avoid DOM reuse bugs.
  - Debugging and logging added for dialog and country selection.
  - Selected countries, states, city, and distance are serialized into hidden fields for backend submission.
- **Backend Model Changes**:
  - `JobApplicationRequest` model now includes:
    - `countries` (JSONField) for multiple countries/states
    - `city` (CharField) for user-entered city
    - `distance` (IntegerField) for slider value
  - Old location fields are kept for compatibility but marked as deprecated.
- **Form and View Updates**:
  - `JobApplicationForm` and `start_job_application` view updated to handle new fields and validation.
  - Form validation improved for city, salary range, and "other" reason.
- **Cancel Application Flow**:
  - Cancel button now uses a custom Alert dialog for confirmation (not browser confirm).
  - On cancel, user is redirected to the main dashboard app (`dashboard:dashboard`).
- **Bug Fixes**:
  - Fixed issues with dialog not appearing after first open.
  - Fixed city field always being a text input.
  - Fixed dashboard redirect after cancel to avoid missing template errors.

---

# Job Service Language Files

This directory contains translation files specifically for the `job_service` app's internationalization (i18n) system.

## Structure

```
job_service/static/job_service/lang/
├── en.json          # English translations for job_service
├── fr.json          # French translations for job_service
├── es.json          # Spanish translations for job_service
└── README.md        # This file
```

## App-Specific Organization

This follows Django's app-based static file organization:
- **Each app** has its own language files in `app_name/static/app_name/lang/`
- **Makes management easier** - each app's translations are self-contained
- **Follows Django conventions** - similar to how static files are organized
- **Scalable** - easy to add new apps with their own translations

## Adding New Languages

To add a new language to job_service:

1. **Create a new JSON file** (e.g., `de.json` for German)
2. **Copy the structure** from `en.json`
3. **Translate all values** to the target language
4. **Update the navigation** in `templates/navigation.html` to include the new language option
5. **Update the i18next initialization** in `templates/base.html` to load the new language

## Adding New Translation Keys

When adding new UI text that needs translation in job_service:

1. **Add the key to all language files** (`en.json`, `fr.json`, `es.json`)
2. **Use the key in templates** with `data-i18n="key_name"`
3. **Follow the naming convention**: lowercase with underscores (e.g., `job_title`, `email_address`)

## Variable Replacement

For dynamic content, use variable placeholders:

```json
{
  "resume_ready_desc": "We'll use your most recent resume: __resume_name__",
  "resume_count": "You have __count__ resumes available"
}
```

In templates, pass variables via `data-` attributes:
```html
<p data-i18n="resume_ready_desc" data-resume_name="John's Resume"></p>
<span data-i18n="resume_count" data-count="3"></span>
```

## Current Translation Keys

### Job Application Form
- `start_job_search` - Main heading
- `start_job_search_sub` - Subheading
- `job_details`, `location`, `contact` - Step titles
- `what_job`, `where_work`, `contact_info` - Section headings
- `job_title`, `email_address`, `phone_number` - Field labels
- `previous`, `next`, `submit_application` - Navigation buttons

### Resume Status
- `resume_ready`, `resume_required` - Status messages
- `resume_ready_desc`, `resume_required_desc` - Descriptions
- `manage_resumes`, `create_resume` - Action buttons

### Form Help Text
- `job_title_help`, `why_applying_help` - Help text for form fields

## Best Practices

1. **Keep keys descriptive** and organized by feature
2. **Use consistent naming** across all language files
3. **Test translations** with native speakers when possible
4. **Keep translations concise** while maintaining meaning
5. **Use proper punctuation** for each language
6. **Keep app-specific** - only include translations relevant to this app

## Technical Notes

- **File format**: JSON with UTF-8 encoding
- **Loading**: Files are loaded via Django's static file system from job_service app
- **Initialization**: i18next loads all languages on page load
- **Caching**: Language preference is stored in localStorage
- **Fallback**: English is used as fallback for missing translations
- **App-specific**: These translations are specific to the job_service app

## For Other Apps

When creating language files for other apps, follow the same pattern:

### Example: Resume Builder App
```
resume_builder/static/resume_builder/lang/
├── en.json
├── fr.json
├── es.json
└── README.md
```

### Example: Authentication App
```
authentication/static/authentication/lang/
├── en.json
├── fr.json
├── es.json
└── README.md
```

### Example: Dashboard App
```
dashboard/static/dashboard/lang/
├── en.json
├── fr.json
├── es.json
└── README.md
```

### Loading Multiple App Languages

In `base.html`, you can load languages from multiple apps:

```javascript
// Load languages from multiple apps
const [jobServiceEn, resumeBuilderEn, authEn] = await Promise.all([
    fetch('{% static "job_service/lang/en.json" %}').then(res => res.json()),
    fetch('{% static "resume_builder/lang/en.json" %}').then(res => res.json()),
    fetch('{% static "authentication/lang/en.json" %}').then(res => res.json())
]);

// Merge all translations
const allTranslations = {
    ...jobServiceEn,
    ...resumeBuilderEn,
    ...authEn
};
```

This keeps each app's translations organized and manageable while allowing for easy combination when needed. 