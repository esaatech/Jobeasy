# AI Service Module

## Overview

The `ai_service` module provides AI-powered functionality for the Jobeas resume builder platform. It handles resume parsing, content generation, and optimization using OpenAI's GPT models with structured output formatting.

## Architecture

### Core Components

#### 1. Structured Resume Parser (`structured_resume.py`)
- **Purpose**: Extracts structured data from raw resume text
- **Framework**: Uses RISEN (Role, Instruction, Step, Endgoal, Narrowing) framework for consistent parsing
- **Models**: Pydantic models for type-safe data validation
- **Temperature**: 0.0 for maximum consistency

#### 2. OpenAI Integration (`open_ai.py`)
- **Purpose**: Handles various AI content generation tasks
- **Features**: Professional summary generation, cover letter creation, content optimization
- **Error Handling**: Network timeout, connection, and generic error handling

## Data Models

### Resume Data Structure

```python
class PersonalInfo(BaseModel):
    full_name: str
    email: str
    phone: str
    location: str
    linkedin: str
    summary: str
    title: str

class Experience(BaseModel):
    title: str
    company: str
    start_date: str  # YYYY-MM format
    end_date: str    # YYYY-MM or "Present"
    description: str # HTML formatted
    achievements: List[str]

class Education(BaseModel):
    degree: str
    institution: str
    start_date: str
    end_date: str
    gpa: str
    description: str

class Skills(BaseModel):
    technical: List[str]
    soft: List[str]
    languages: List[str]

class Additional(BaseModel):
    certifications: str  # HTML formatted
    projects: str        # HTML formatted

class ResumeData(BaseModel):
    personal_info: PersonalInfo
    experience: List[Experience]
    education: List[Education]
    skills: Skills
    additional: Additional
    is_complete: bool
```

## RISEN Framework Implementation

### Role
- Expert resume parser with specialized expertise in comprehensive resume analysis

### Instruction
- Structured step-by-step process to extract ALL resume information

### Step
1. **Personal Information Extraction**
   - Extract contact details, title, summary
   - Generate first-person professional summary if missing
   - Deduce professional title based on experience and skills

2. **Work Experience Extraction**
   - Identify all experience entries
   - Extract complete job descriptions with HTML formatting
   - Preserve all achievements and technical details
   - Use consistent date formatting (YYYY-MM)

3. **Education Extraction**
   - Extract all education entries
   - Include degrees, institutions, dates, GPA
   - Handle ongoing education with "Present" end date

4. **Skills Categorization**
   - Technical skills: programming languages, tools, technologies
   - Soft skills: communication, leadership, problem-solving
   - Languages: spoken languages with proficiency levels

5. **Additional Information**
   - Certifications: HTML formatted list
   - Projects: HTML formatted list
   - Look for projects in various sections and formats

6. **Completeness Validation**
   - Verify critical information extraction
   - Set is_complete flag appropriately

### Endgoal
- Complete, structured resume data with consistent formatting
- All sections properly extracted and formatted
- HTML formatting for rich content (descriptions, certifications, projects)

### Narrowing
- Focus only on resume information extraction
- Prevent scope creep and ensure consistency
- Maintain data integrity and accuracy

## Usage in the Project

### 1. Resume Upload and Parsing

```python
# In resume_builder/views.py
from ai_service.structured_resume import format_resume_single_call

def upload_resume(request):
    # Extract text from uploaded file (PDF, DOC, DOCX)
    resume_text = extract_text_from_file(resume_file)
    
    # Parse using AI service
    parsed_data = format_resume_single_call(resume_text)
    
    # Create Resume object
    resume = Resume.objects.create(
        user=request.user,
        personal_info=parsed_data.personal_info.model_dump(),
        experience=[exp.model_dump() for exp in parsed_data.experience],
        education=[edu.model_dump() for edu in parsed_data.education],
        skills=parsed_data.skills.model_dump(),
        additional=parsed_data.additional.model_dump(),
        is_optimized=False
    )
```

### 2. Professional Summary Generation

```python
# In resume_builder/views.py
from ai_service.open_ai import generate_professional_summary

def generate_ai_summary(request):
    resume_data = {
        'personal_info': resume.personal_info,
        'experience': resume.experience,
        'education': resume.education,
        'skills': resume.skills,
        'additional': resume.additional
    }
    
    ai_result = generate_professional_summary(resume_data)
    return JsonResponse({'success': True, 'summary': ai_result['summary']})
```

### 3. Dashboard Optimization Workflow

The dashboard uses the AI service for comprehensive resume optimization and cover letter generation:

#### **Step 1: User Input**
- User uploads resume or selects existing resume
- User provides job description, company name, and job title
- Dashboard validates input and prepares for AI processing

#### **Step 2: Resume Optimization**
```python
# Generate optimized resume with ATS scoring
optimized_result = generate_optimized_resume(
    resume_text=resume_data['original_content'],
    job_description=job_description
)

# Results include:
# - optimized_content: Enhanced resume text
# - keyword_matches: List of matched keywords
# - improvement_suggestions: AI recommendations
# - ats_score: Compatibility score (0-100)
```

#### **Step 3: Cover Letter Generation**
```python
# Generate personalized cover letter
cover_letter_result = generate_cover_letter(
    resume_data=resume_data,
    job_description=job_description,
    company_name=company_name,
    job_title=job_title
)

# Results include:
# - cover_letter: Personalized cover letter text
# - confidence_score: AI confidence in the generated content
```

#### **Step 4: Results Storage and Display**
- Store optimized resume with ATS score
- Store generated cover letter
- Display results in dashboard with:
  - ATS compatibility score
  - Keyword matches found
  - Improvement suggestions
  - Optimized resume preview
  - Cover letter preview

### 4. Error Handling

```python
# Network error handling
try:
    parsed_data = format_resume_single_call(resume_text)
except TimeoutError:
    error_dialog = get_network_timeout_dialog()
    return JsonResponse({'success': False, 'error': error_dialog}, status=504)
except ConnectionError:
    error_dialog = get_network_connection_dialog()
    return JsonResponse({'success': False, 'error': error_dialog}, status=503)
except Exception as e:
    error_dialog = get_network_generic_dialog()
    return JsonResponse({'success': False, 'error': error_dialog}, status=500)
```

### 5. Cover Letter Generation

```python
# In ai_service/open_ai.py
def generate_cover_letter(resume_data, job_description, company_name, job_title):
    """
    Generate a personalized cover letter based on resume and job requirements
    """
    system_msg = (
        "You are an expert cover letter writer. Create a compelling, personalized cover letter "
        "that matches the candidate's experience with the job requirements."
    )
    
    user_msg = f"""
    Resume Data: {resume_data}
    Job Description: {job_description}
    Company: {company_name}
    Position: {job_title}
    
    Generate a professional cover letter that:
    1. Addresses the specific job requirements
    2. Highlights relevant experience from the resume
    3. Shows enthusiasm for the company and position
    4. Uses first-person perspective
    5. Is 3-4 paragraphs long
    """
    
    # AI call implementation...
```

### 6. Resume Optimization with ATS Scoring

```python
# In ai_service/open_ai.py
def generate_optimized_resume(resume_text, job_description):
    """
    Optimize resume for ATS systems and calculate compatibility score
    """
    system_msg = (
        "You are an expert resume optimizer specializing in ATS (Applicant Tracking System) optimization. "
        "Analyze the resume against the job description and provide improvements."
    )
    
    user_msg = f"""
    Original Resume: {resume_text}
    Job Description: {job_description}
    
    Please:
    1. Identify relevant keywords from the job description
    2. Suggest improvements to match the resume with job requirements
    3. Calculate an ATS compatibility score (0-100)
    4. Provide an optimized version of the resume
    5. List specific keyword matches found
    """
    
    # AI call implementation...
```

## Configuration

### Environment Variables

```bash
# Required
OPENAI_API_KEY=your_openai_api_key_here

# Optional
OPENAI_MODEL=gpt-4o-2024-08-06  # Default model
OPENAI_TIMEOUT=30               # Request timeout in seconds
```

### Model Settings

- **Model**: `gpt-4o-2024-08-06` (latest GPT-4 model)
- **Temperature**: 0.0 for parsing, 0.3-0.7 for content generation
- **Response Format**: Structured JSON using Pydantic models
- **Max Tokens**: Handled automatically by OpenAI

## Error Handling

### Network Errors
- **Timeout**: 504 Gateway Timeout
- **Connection**: 503 Service Unavailable
- **Generic**: 500 Internal Server Error

### Validation Errors
- **Invalid File Format**: 400 Bad Request
- **Empty Content**: 400 Bad Request
- **Parsing Failure**: 500 Internal Server Error

### User-Friendly Error Messages
- Network timeout dialogs
- Connection error dialogs
- Generic error dialogs
- Specific validation messages

## Performance Considerations

### Optimization Strategies
1. **Single Call vs Dual Call**: Use `format_resume_single_call()` for better performance
2. **Caching**: Consider caching parsed results for repeated uploads
3. **Async Processing**: For large files, consider background processing
4. **Rate Limiting**: Implement rate limiting for API calls

### Monitoring
- Log parsing success/failure rates
- Monitor API response times
- Track error patterns
- Monitor token usage

## Testing

### Test Functions

```python
# Test basic parsing
test_format_resume()

# Test single call performance
test_single_call_performance()

# Test RISEN framework consistency
test_rise_framework_consistency()

# Compare parsing methods
compare_parsing_methods()
```

### Test Cases
- Standard professional resumes
- Complex resumes with multiple formats
- Minimal resume formats
- Edge cases and error conditions

## Integration Points

### Frontend Integration
- Resume upload form (`resume_builder/optimize_resume_form.html`)
- Progress indicators during parsing
- Error message display
- Success redirects

### Dashboard Integration
- **Resume Optimization**: AI-powered resume optimization against job descriptions
- **Cover Letter Generation**: Personalized cover letters based on resume and job requirements
- **ATS Scoring**: Compatibility scoring for Applicant Tracking Systems
- **Keyword Matching**: Identify relevant keywords from job descriptions
- **Improvement Suggestions**: AI-generated recommendations for resume enhancement
- **Real-time Processing**: Dashboard shows optimization progress and results

### Database Integration
- Resume model storage
- User association
- Template selection
- Draft vs. ready status
- Optimized resume storage with ATS scores
- Cover letter storage and management

### Template Rendering
- HTML formatting preservation
- Dynamic content rendering
- Template switching
- Export functionality

## Security Considerations

### API Key Management
- Store API keys in environment variables
- Never commit keys to version control
- Use secure key rotation practices

### Input Validation
- Validate file types and sizes
- Sanitize user input
- Prevent injection attacks

### Rate Limiting
- Implement per-user rate limits
- Monitor API usage
- Prevent abuse

## Future Enhancements

### Planned Features
1. **Multi-language Support**: Parse resumes in different languages
2. **ATS Optimization**: AI-powered resume optimization for ATS systems
3. **Cover Letter Generation**: Generate matching cover letters
4. **Interview Preparation**: Generate interview questions and answers
5. **Skills Gap Analysis**: Identify missing skills for job requirements

### Technical Improvements
1. **Batch Processing**: Handle multiple resumes simultaneously
2. **Advanced Caching**: Redis-based caching for better performance
3. **Webhook Integration**: Real-time parsing status updates
4. **Analytics Dashboard**: Detailed parsing analytics and insights

## Troubleshooting

### Common Issues

1. **Empty Projects Section**
   - Check if resume has a "Projects" section
   - Look for alternative section names
   - Verify projects are mentioned in other sections

2. **Missing Languages**
   - Ensure languages are mentioned in the resume
   - Check for language proficiency indicators
   - Verify skills section includes languages

3. **Inconsistent Formatting**
   - Verify temperature is set to 0.0
   - Check RISEN framework implementation
   - Ensure proper HTML formatting instructions

4. **API Errors**
   - Verify OpenAI API key is valid
   - Check network connectivity
   - Monitor API rate limits

### Debug Steps
1. Enable detailed logging
2. Test with sample resume data
3. Verify model responses
4. Check error handling paths
5. Validate data structure consistency

## Contributing

### Development Guidelines
1. Follow RISEN framework for new parsing features
2. Maintain consistent error handling
3. Add comprehensive tests for new functionality
4. Update documentation for API changes
5. Use type hints and Pydantic models

### Code Quality
- Use consistent formatting (Black)
- Follow PEP 8 guidelines
- Add docstrings for all functions
- Include type hints
- Write unit tests

---

For more information, see the main project documentation or contact the development team. 