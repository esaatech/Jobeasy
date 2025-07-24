# Resume Builder App

## Overview

The Resume Builder app allows both authenticated and anonymous users to create professional resumes using a step-by-step form interface. Users can choose from multiple templates, preview their resumes, and download them in various formats (PDF).

## Architecture

### Frontend Components

#### ResumeBuilder Class (`resume_builder.js`)
- **Purpose**: Handles **anonymous user only** resume creation workflow
- **Location**: `resume_builder/static/resume_builder/resume_builder.js`
- **Status**: **ONLY for anonymous users** - authenticated users use different flow

**Key Features:**
- Step-by-step form validation (more lenient for anonymous users)
- Template selection with real-time updates
- Data collection and storage in memory (not sessionStorage)
- Preview functionality for anonymous users

**Methods:**
- `nextToExperience()`, `nextToEducation()`, `nextToSkills()`, `nextToAdditional()`: Step navigation
- `finalizeStep()`: Final validation for additional info
- `collectSummary()`: Collects summary data in Step 6
- `getResumeData()`: Returns complete resume data with current template selection
- `updateTemplate()`: Updates template selection in real-time
- `initializeTemplateListeners()`: Sets up template change event listeners

**Validation Differences for Anonymous Users:**
- **Step 1 (Personal Info)**: Only requires `resume_name`, `fullName`, `title`, `email` (no summary)
- **Step 2 (Experience)**: Requires company and position only (dates and descriptions optional for preview)
- **Step 3 (Education)**: Requires institution and degree only (dates optional for preview)
- **Step 6 (Summary)**: Optional - collected via `collectSummary()` method

#### Form Template (`create_resume_form.html`)
- **Purpose**: Main form interface for both authenticated and anonymous users
- **Location**: `resume_builder/templates/resume_builder/create_resume_form.html`
- **Features**: 
  - 6-step form process (Personal Info, Experience, Education, Skills, Additional, Summary)
  - Template selection
  - Real-time validation
  - Preview and save functionality
  - **Two different JavaScript flows based on authentication status**

**Authenticated User JavaScript (Embedded in HTML):**
- Individual `saveX()` functions: `savePersonalInfo()`, `saveExperience()`, `saveEducation()`, etc.
- Step-by-step database saving via `@login_required` endpoints
- Strict validation for all fields
- Summary validation in Step 6 via `validateSummary()` and `saveSummary()`

**Anonymous User JavaScript:**
- Uses `ResumeBuilder` class from `resume_builder.js`
- Client-side data collection only (no database interaction)
- Lenient validation for preview purposes
- Summary collected in Step 6 via `collectSummary()` method

### Backend Views

#### Core Views
- `create_resume()`: Main form view (no `@login_required`)
- `save_personal_info()`, `save_experience()`, `save_education()`, `save_skills()`, `save_additional()`: Step-by-step saving (`@login_required`)
- `save_summary()`: Saves summary data (`@login_required`)
- `finalize_resume()`: Completes resume creation (`@login_required`)
- `view_resume()`: Displays saved resumes (`@login_required`)
- `download_resume_file()`: Handles file downloads
- `resume_templates()`: Displays template gallery page (no `@login_required`)
- `preview_template()`: Renders template previews with sample data (no `@login_required`)

#### Anonymous User Views
- `preview_anonymous_resume()`: Renders preview for anonymous users (`@csrf_exempt`)
- `create_resume_from_data()`: Creates resume from JSON data after authentication (`@login_required`)
- `create_resume_after_auth()`: Handles post-authentication resume creation (`@login_required`)

## Workflows

### Authenticated User Workflow

1. **Form Completion**: User fills out 6-step form
2. **Step-by-Step Saving**: Each step saves to database via AJAX using individual `saveX()` functions
3. **Validation**: Strict validation for all fields including summary in Step 6
4. **Finalization**: User clicks "Save Resume" or "Preview/Download"
5. **Preview**: Opens in new tab (prevents losing form progress)
6. **Save**: Redirects to "My Resumes" page

**Key Features:**
- Real-time saving at each step via `@login_required` endpoints
- Template selection updates in real-time
- Preview opens in new tab for better UX
- Direct redirect to my-resumes after saving
- **Uses embedded JavaScript functions, NOT ResumeBuilder class**

### Anonymous User Workflow

1. **Form Completion**: User fills out 6-step form using ResumeBuilder class
2. **Data Collection**: Resume data stored in ResumeBuilder instance (memory only)
3. **Lenient Validation**: Only basic fields required for preview
4. **Preview**: Opens preview in new tab via `preview_anonymous_resume` view
5. **Save Attempt**: Triggers registration dialog
6. **Authentication**: User registers/logs in
7. **Data Transfer**: Resume data passed via sessionStorage
8. **Resume Creation**: `create_resume_after_auth` view handles post-auth creation
9. **Redirect**: User redirected to "My Resumes" page

**Key Features:**
- No database interaction until authentication
- SessionStorage for data persistence through auth flow
- Seamless transition from anonymous to authenticated
- Direct redirect to my-resumes after authentication
- **Uses ResumeBuilder class for all data collection and validation**

### Post-Authentication Resume Creation Flow

1. **Authentication Success**: User completes login/registration
2. **Redirect**: User redirected to `create_resume_after_auth` view
3. **JavaScript Execution**: Dashboard template checks for pending resume data
4. **Data Retrieval**: Resume data retrieved from sessionStorage
5. **API Call**: POST to `create_resume_from_data` endpoint
6. **Resume Creation**: Backend creates Resume object from JSON data
7. **Redirect**: User redirected to "My Resumes" page
8. **Cleanup**: sessionStorage cleared

**Code Flow:**
```javascript
// In dashboard template
const pendingResumeData = sessionStorage.getItem('pendingResumeData');
if (pendingResumeData) {
    // POST to create_resume_from_data endpoint
    // Redirect to my-resumes on success
}
```

## Data Flow

### Field Name Mapping
- **Frontend**: Uses camelCase (`fullName`, `title`, `email`)
- **Backend**: Maps to snake_case (`full_name`, `title`, `email`)
- **Templates**: Expects snake_case (`resume_data.personal_info.full_name`)

### Template Selection
- **Real-time Updates**: Template changes immediately update ResumeBuilder instance
- **Form Integration**: `getResumeData()` always gets current template from form
- **Event Listeners**: Template radio buttons trigger `updateTemplate()` method

## Key Features

### Preview Functionality
- **New Tab Opening**: Both authenticated and anonymous users get preview in new tab
- **No Progress Loss**: Original form tab remains open with all data intact
- **Template Support**: Preview uses selected template
- **Download Options**: Preview page includes download buttons

### Template System
- **Multiple Templates**: Professional, Modern, Creative
- **Real-time Switching**: Template changes update immediately
- **Consistent Rendering**: Same templates used for preview and final output

### Resume Templates Gallery
- **Dedicated Page**: `/resume/resume_templates/` - Standalone template gallery
- **Template Cards**: Visual cards with template screenshots and descriptions
- **Preview Functionality**: Uses same backend endpoint as create_resume_form (`preview_template`)
- **Modal Interface**: Consistent modal design with template navigation tabs
- **Backend Integration**: Fetches real template HTML from `preview_template` view
- **Use Template**: Direct redirect to create_resume with selected template

**Features:**
- **Template Navigation**: Switch between templates within the modal
- **Real Template Rendering**: Uses actual template files (professional.html, modern.html, creative.html)
- **Sample Data**: Displays realistic resume content with localized sample data
- **Responsive Design**: Works on desktop and mobile devices
- **Keyboard Support**: ESC key closes modal, click outside to close
- **Consistent UX**: Same preview experience as create_resume_form

### File Downloads
- **Multiple Formats**: PDF, HTML, Word documents
- **Anonymous Support**: Anonymous users can download without saving
- **Authenticated Support**: Saved resumes can be downloaded anytime

## Technical Implementation Details

### JavaScript Flow Differences

**Authenticated Users:**
```javascript
// In create_resume_form.html
async function nextStep() {
    if (window.isAuthenticated) {
        // Uses individual saveX() functions
        switch (currentStep) {
            case 1:
                isValid = validatePersonalInfo();
                isSaved = await savePersonalInfo();
                break;
            // ... other cases
        }
    }
}
```

**Anonymous Users:**
```javascript
// In create_resume_form.html
async function nextStep() {
    if (!window.isAuthenticated) {
        // Uses ResumeBuilder class methods
        let valid = false;
        if (currentStep === 1) valid = window.resumeBuilder.nextToExperience();
        if (currentStep === 2) valid = window.resumeBuilder.nextToEducation();
        // ... other steps
    }
}
```

### Validation Differences

**Authenticated Users (Strict):**
- All fields required including summary
- Dates must be properly formatted
- Descriptions required for experience entries

**Anonymous Users (Lenient):**
- Basic fields only (name, title, email for Step 1)
- Dates optional for preview
- Descriptions optional for preview
- Summary optional and collected in Step 6

### Summary Field Handling

**Authenticated Users:**
- Summary validated in Step 6 via `validateSummary()`
- Saved via `saveSummary()` function to `save_summary` endpoint

**Anonymous Users:**
- Summary not validated in Step 1 (removed from `validatePersonalInfo()`)
- Collected in Step 6 via `collectSummary()` method
- Added to `personalInfo` object for preview

## Future Improvements

### Code Consolidation
**Current State**: Two separate JavaScript flows for authenticated vs anonymous users
**Potential Goal**: Unify the flows for easier maintenance

**Benefits:**
- Single codebase for both user types
- Consistent validation logic
- Easier maintenance
- Better user experience

**Implementation Considerations:**
- Maintain existing save functionality for authenticated users
- Keep lenient validation for anonymous users
- Ensure backward compatibility

### Additional Features
- Resume templates library expansion
- ATS optimization features
- Resume sharing capabilities
- Version history for saved resumes
- Bulk operations for multiple resumes

## Technical Notes

### SessionStorage Usage
- **Purpose**: Persist anonymous user data through authentication
- **Key**: `pendingResumeData`
- **Cleanup**: Cleared after successful resume creation
- **Fallback**: URL parameters for data transfer (alternative approach)

### CSRF Protection
- **Authenticated Users**: CSRF tokens required for all POST requests
- **Anonymous Users**: `@csrf_exempt` decorator for preview endpoints
- **Security**: Proper validation and sanitization of all inputs

### Error Handling
- **Network Errors**: Graceful fallbacks for API failures
- **Validation Errors**: User-friendly error messages
- **Authentication Errors**: Proper redirects and messaging

## File Structure

```
resume_builder/
├── static/resume_builder/
│   └── resume_builder.js          # ResumeBuilder class (anonymous users only)
├── templates/resume_builder/
│   ├── create_resume_form.html    # Main form template (both user types)
│   ├── create_resume_after_auth.html  # Post-auth template
│   └── view_resume.html           # Resume display template
├── templates/resume_templates/    # Resume template files
│   ├── resume_templates.html      # Template gallery page
│   ├── professional.html          # Professional template
│   ├── modern.html               # Modern template
│   └── creative.html             # Creative template
├── views.py                       # Backend views
├── urls.py                        # URL patterns
└── models.py                      # Resume model
```

## Dependencies

- **Frontend**: CKEditor 5, Flatpickr, Tailwind CSS
- **Backend**: Django, xhtml2pdf (PDF generation)
- **Optional**: html2docx (Word document generation)
- **Optional**: pdf_generator (Enhanced PDF generation)