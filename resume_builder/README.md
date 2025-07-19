# Resume Builder App

## Overview

The Resume Builder app allows both authenticated and anonymous users to create professional resumes using a step-by-step form interface. Users can choose from multiple templates, preview their resumes, and download them in various formats (PDF).

## Architecture

### Frontend Components

#### ResumeBuilder Class (`resume_builder.js`)
- **Purpose**: Handles anonymous user resume creation workflow
- **Location**: `resume_builder/static/resume_builder/resume_builder.js`
- **Status**: Currently handles only anonymous users - **TODO: Integrate with authenticated user flow**

**Key Features:**
- Step-by-step form validation
- Template selection with real-time updates
- Data collection and storage in sessionStorage
- Preview functionality for anonymous users

**Methods:**
- `nextToExperience()`, `nextToEducation()`, `nextToSkills()`, `nextToAdditional()`: Step navigation
- `finalizeStep()`: Final validation
- `getResumeData()`: Returns complete resume data with current template selection
- `updateTemplate()`: Updates template selection in real-time
- `initializeTemplateListeners()`: Sets up template change event listeners

#### Form Template (`create_resume_form.html`)
- **Purpose**: Main form interface for both authenticated and anonymous users
- **Location**: `resume_builder/templates/resume_builder/create_resume_form.html`
- **Features**: 
  - 5-step form process (Personal Info, Experience, Education, Skills, Additional)
  - Template selection
  - Real-time validation
  - Preview and save functionality

### Backend Views

#### Core Views
- `create_resume()`: Main form view
- `save_personal_info()`, `save_experience()`, `save_education()`, `save_skills()`, `save_additional()`: Step-by-step saving
- `finalize_resume()`: Completes resume creation
- `view_resume()`: Displays saved resumes
- `download_resume_file()`: Handles file downloads

#### Anonymous User Views
- `preview_anonymous_resume()`: Renders preview for anonymous users
- `create_resume_from_data()`: Creates resume from JSON data after authentication
- `create_resume_after_auth()`: Handles post-authentication resume creation

## Workflows

### Authenticated User Workflow

1. **Form Completion**: User fills out 5-step form
2. **Step-by-Step Saving**: Each step saves to database via AJAX
3. **Finalization**: User clicks "Save Resume" or "Preview/Download"
4. **Preview**: Opens in new tab (prevents losing form progress)
5. **Save**: Redirects to "My Resumes" page

**Key Features:**
- Real-time saving at each step
- Template selection updates in real-time
- Preview opens in new tab for better UX
- Direct redirect to my-resumes after saving

### Anonymous User Workflow

1. **Form Completion**: User fills out 5-step form using ResumeBuilder class
2. **Data Collection**: Resume data stored in ResumeBuilder instance
3. **Preview**: Opens preview in new tab via `preview_anonymous_resume` view
4. **Save Attempt**: Triggers registration dialog
5. **Authentication**: User registers/logs in
6. **Data Transfer**: Resume data passed via sessionStorage
7. **Resume Creation**: `create_resume_after_auth` view handles post-auth creation
8. **Redirect**: User redirected to "My Resumes" page

**Key Features:**
- No database interaction until authentication
- SessionStorage for data persistence
- Seamless transition from anonymous to authenticated
- Direct redirect to my-resumes after authentication

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

### File Downloads
- **Multiple Formats**: PDF, HTML, Word documents
- **Anonymous Support**: Anonymous users can download without saving
- **Authenticated Support**: Saved resumes can be downloaded anytime

## Future Improvements

### ResumeBuilder Class Integration
**Current State**: ResumeBuilder class handles only anonymous users
**Goal**: Integrate with authenticated user flow for consistency

**Benefits:**
- Single codebase for both user types
- Consistent validation logic
- Easier maintenance
- Better user experience

**Implementation Plan:**
1. Modify authenticated user flow to use ResumeBuilder class
2. Update step navigation to use class methods
3. Unify validation logic
4. Maintain existing save functionality for authenticated users

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
│   └── resume_builder.js          # ResumeBuilder class
├── templates/resume_builder/
│   ├── create_resume_form.html    # Main form template
│   ├── create_resume_after_auth.html  # Post-auth template
│   └── view_resume.html           # Resume display template
├── templates/resume_templates/    # Resume template files
├── views.py                       # Backend views
├── urls.py                        # URL patterns
└── models.py                      # Resume model
```

## Dependencies

- **Frontend**: CKEditor 5, Flatpickr, Tailwind CSS
- **Backend**: Django, xhtml2pdf (PDF generation)
- **Optional**: html2docx (Word document generation)
- **Optional**: pdf_generator (Enhanced PDF generation)




Resume assistant Architecture



┌─────────────────┐    WebSocket Connection    ┌─────────────────┐
│   Frontend      │◄──────────────────────────►│   Backend       │
│   (Browser)     │                            │   (Django)      │
└─────────────────┘                            └─────────────────┘
         │                                              │
         │ 1. User sends message                       │
         │    "Switch to modern template"              │
         │                                              │
         ▼                                              │
┌─────────────────┐                            ┌─────────────────┐
│ WebSocket       │                            │ AI Assistant    │
│ Consumer        │                            │ Manager         │
└─────────────────┘                            └─────────────────┘
         │                                              │
         │                                              ▼
         │                                    ┌─────────────────┐
         │                                    │ Function        │
         │                                    │ Handler         │
         │                                    │ switch_template │
         │                                    └─────────────────┘
         │                                              │
         │                                              ▼
         │                                    ┌─────────────────┐
         │                                    │ Event Emitter   │
         │                                    │ (Django Channels)│
         │                                    └─────────────────┘
         │                                              │
         │                                              ▼
         │                                    ┌─────────────────┐
         │                                    │ WebSocket       │
         │                                    │ Group Send      │
         │                                    └─────────────────┘
         │                                              │
         ▼                                              │
┌─────────────────┐                            ┌─────────────────┐
│ Frontend        │◄───────────────────────────┤ Event Received  │
│ Event Handler   │                            │ "template_changed"│
│ Updates UI      │                            └─────────────────┘
└─────────────────┘