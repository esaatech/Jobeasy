# AI Service Module

## Documentation map

| Document | Contents |
|----------|----------|
| **[`docs/AI_PLATFORM.md`](docs/AI_PLATFORM.md)** | **Primary reference:** configurable prompts (`AIService` / `AIPromptConfiguration`), model catalog (`AIModel`), multi-provider roadmap, resume–job evaluation structured output, dashboard product ideas, admin playground, setup commands |
| This README | Legacy detail: OpenAI resume parsing (RISEN), cover letter/optimization, AI assistant task schema |

For new work on prompts, Gemini evaluation, or model configuration, start with **`docs/AI_PLATFORM.md`**.

---

## Overview

The `ai_service` module provides AI-powered functionality for the Jobeas resume builder platform. It handles resume parsing, content generation, and optimization using OpenAI's GPT models with structured output formatting. **Resume–job fit evaluation** uses Google Gemini with database-driven prompts and a structured JSON schema (see platform doc above).

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




### How the AI Assistant Works (Simple Explanation)

Think of the AI assistant like a smart personal secretary who can help you with specific tasks. Here's how it works in everyday terms:

#### The Conversation Flow

**Example: You want to create a resume**

1. **You start a conversation**: "Hi, I need help creating a resume"
2. **The AI understands your request**: It recognizes you want to build a resume
3. **The AI asks for information**: "Great! Let's start with your personal information. What's your full name?"
4. **You provide details**: "My name is John Smith"
5. **The AI saves the information**: It uses a special "save function" to store your name
6. **The AI continues guiding you**: "Perfect! Now what's your email address?"

#### What Happens Behind the Scenes

**The Task Schema** (like a recipe book):
- Think of the task schema as a cookbook that tells the AI what "recipes" (functions) it can use
- Each recipe has a name, description, and list of ingredients (parameters) needed
- For example: "save_personal_info" recipe needs: full name, email, phone, etc.

**The Function Handlers** (like kitchen tools):
- These are the actual tools that do the work
- When the AI decides to save your name, it uses the "save_personal_info" tool
- This tool takes your information and stores it properly in the system

#### A Real Example Walkthrough

**User**: "I want to create a resume"

**AI**: "Great! I can help you create a professional resume. Let's start with your personal information. What's your full name?"

**User**: "John Smith"

**AI**: "Perfect! What's your email address?"

**User**: "john.smith@email.com"

**AI**: "Excellent! Now what's your phone number?"

**User**: "555-123-4567"

**AI**: "Great! What's your professional title?"

**User**: "Software Engineer"

**AI**: "Perfect! Now let me save all this information for you."

*[Behind the scenes, the AI uses the save_personal_info function with all the details]*

**AI**: "Your personal information has been saved! Now let's move on to your work experience. What was your most recent job title?"

#### How the System Knows What to Do

**The Magic of Function Calling**:
- The AI doesn't just chat - it can actually DO things
- When you provide information, the AI recognizes it needs to save it
- It looks at its "recipe book" (task schema) and finds the right "recipe" (function)
- It uses the "kitchen tool" (function handler) to actually save your data
- Then it continues the conversation naturally

**Why This is Powerful**:
- You don't need to fill out forms or click buttons
- You just have a natural conversation
- The AI handles all the technical stuff behind the scenes
- Your information gets saved automatically as you provide it
- The AI guides you through the entire process step by step

#### The Resume Building Process

**Step 1 - Personal Info**: AI asks for your name, email, phone, title
**Step 2 - Experience**: AI asks about your work history, job titles, companies
**Step 3 - Education**: AI asks about your degrees, schools, graduation dates
**Step 4 - Skills**: AI asks about your technical skills, soft skills, languages
**Step 5 - Additional**: AI asks about certifications, projects, awards
**Step 6 - Finalize**: AI helps you choose a template and completes your resume

At each step, the AI uses different "tools" (functions) to save your information properly, just like a skilled assistant who knows exactly how to organize and store everything you tell them.



## AI Assistant Module Requirements

### Overview
The AI Assistant module consists of three main components that work together:
1. **Task Schema** - Defines what functions the AI can call
2. **Function Handlers** - Implements the actual functionality
3. **Assistant Manager** - Orchestrates the conversation and function calling

### 1. Task Schema Requirements (`task_schema.py`)

The task schema defines the "recipes" that tell the AI what functions it can use and what parameters they need.

#### Structure:
```python
TASK_SCHEMAS = {
    'your_domain': {  # e.g., 'resume', 'email', 'calendar'
        'function_name': {
            'name': 'function_name',
            'description': 'What this function does',
            'parameters': {
                'type': 'object',
                'properties': {
                    'param1': {'type': 'string', 'description': 'What this parameter is'},
                    'param2': {'type': 'array', 'items': {'type': 'string'}, 'description': 'List of items'},
                    'param3': {'type': 'string', 'enum': ['option1', 'option2'], 'description': 'Choose from options'}
                },
                'required': ['param1', 'param2', 'param3'],  # ALL properties must be listed here
                'additionalProperties': False
            }
        }
    }
}
```

#### Example: Adding a New Task
```python
# Add this to TASK_SCHEMAS in task_schema.py
'calendar': {
    'create_event': {
        'name': 'create_event',
        'description': 'Create a new calendar event',
        'parameters': {
            'type': 'object',
            'properties': {
                'title': {'type': 'string', 'description': 'Event title'},
                'date': {'type': 'string', 'description': 'Event date in YYYY-MM-DD format'},
                'time': {'type': 'string', 'description': 'Event time in HH:MM format'},
                'duration': {'type': 'integer', 'description': 'Duration in minutes'},
                'description': {'type': 'string', 'description': 'Event description'}
            },
            'required': ['title', 'date', 'time', 'duration', 'description'],
            'additionalProperties': False
        }
    }
}
```

### 2. Function Handler Requirements (`function_handlers.py`)

Function handlers contain the actual code that gets executed when the AI calls a function.

#### Structure:
```python
@staticmethod
def your_function_name(
    param1: str,
    param2: list = None,
    param3: str = None
) -> Dict[str, Any]:
    """Description of what this function does"""
    try:
        print(f"\n========== YOUR FUNCTION NAME ==========")
        print(f"Param1: {param1}")
        print(f"Param2: {param2}")
        print(f"Param3: {param3}")
        
        # TODO: Integrate with Django models
        # from your_app.models import YourModel
        # your_model = YourModel.objects.get(id=model_id)
        # your_model.field = param1
        # your_model.save()
        
        result = {
            "success": True,
            "message": "Operation completed successfully",
            "data": {
                "param1": param1,
                "param2": param2,
                "param3": param3,
                "timestamp": datetime.now().isoformat()
            }
        }
        return result
        
    except Exception as e:
        logger.error(f"Error in your_function_name: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }
```

#### Example: Adding a New Function Handler
```python
@staticmethod
def create_event(
    title: str,
    date: str,
    time: str,
    duration: int,
    description: str = None
) -> Dict[str, Any]:
    """Create a new calendar event"""
    try:
        print(f"\n========== CREATE EVENT ==========")
        print(f"Title: {title}")
        print(f"Date: {date}")
        print(f"Time: {time}")
        print(f"Duration: {duration} minutes")
        print(f"Description: {description}")
        
        # TODO: Integrate with Django models
        # from calendar_app.models import Event
        # event = Event.objects.create(
        #     title=title,
        #     date=date,
        #     time=time,
        #     duration=duration,
        #     description=description
        # )
        
        result = {
            "success": True,
            "message": f"Event '{title}' created successfully",
            "data": {
                "title": title,
                "date": date,
                "time": time,
                "duration": duration,
                "description": description,
                "timestamp": datetime.now().isoformat()
            }
        }
        return result
        
    except Exception as e:
        logger.error(f"Error in create_event: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }
```

### 3. Assistant Manager Integration

The Assistant Manager needs to know about your new function to call it.

#### Add to Function Mapping:
In `open_ai_assistant_with_rag_and_function_call.py`, add your function to the mapping:

```python
# In the add_message_and_run method, add this case:
elif tool_call.function.name == "create_event":
    result = handler.create_event(**args)
```

### 4. Complete Example: Adding a Calendar Event System

#### Step 1: Add to Task Schema
```python
# In task_schema.py, add to TASK_SCHEMAS
'calendar': {
    'create_event': {
        'name': 'create_event',
        'description': 'Create a new calendar event',
        'parameters': {
            'type': 'object',
            'properties': {
                'title': {'type': 'string', 'description': 'Event title'},
                'date': {'type': 'string', 'description': 'Event date in YYYY-MM-DD format'},
                'time': {'type': 'string', 'description': 'Event time in HH:MM format'},
                'duration': {'type': 'integer', 'description': 'Duration in minutes'},
                'description': {'type': 'string', 'description': 'Event description'}
            },
            'required': ['title', 'date', 'time', 'duration', 'description'],
            'additionalProperties': False
        }
    }
}
```

#### Step 2: Add Function Handler
```python
# In function_handlers.py, add to FunctionHandlers class
@staticmethod
def create_event(
    title: str,
    date: str,
    time: str,
    duration: int,
    description: str = None
) -> Dict[str, Any]:
    """Create a new calendar event"""
    try:
        print(f"\n========== CREATE EVENT ==========")
        print(f"Title: {title}")
        print(f"Date: {date}")
        print(f"Time: {time}")
        print(f"Duration: {duration} minutes")
        print(f"Description: {description}")
        
        # TODO: Integrate with Django models
        # from calendar_app.models import Event
        # event = Event.objects.create(
        #     title=title,
        #     date=date,
        #     time=time,
        #     duration=duration,
        #     description=description
        # )
        
        result = {
            "success": True,
            "message": f"Event '{title}' created successfully",
            "data": {
                "title": title,
                "date": date,
                "time": time,
                "duration": duration,
                "description": description,
                "timestamp": datetime.now().isoformat()
            }
        }
        return result
        
    except Exception as e:
        logger.error(f"Error in create_event: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }
```

#### Step 3: Create Assistant with New Function
```python
# In your test or setup script
from ai_service.open_ai_assistant_with_rag_and_function_call import OpenAIAssistantManager, FunctionConfig
from ai_service.task_schema import TASK_SCHEMAS

# Get the schema for your function
calendar_schema = TASK_SCHEMAS['calendar']['create_event']

# Create function configuration
calendar_function = FunctionConfig(
    name=calendar_schema['name'],
    description=calendar_schema['description'],
    parameters=calendar_schema['parameters'],
    instructions="""When a user wants to create a calendar event:
    1. Extract the event title, date, time, duration, and description
    2. Use this function to create the event
    3. Confirm the event was created successfully
    4. Be helpful and ask for any missing information"""
)

# Create assistant with calendar function
manager = OpenAIAssistantManager()
assistant_id = manager.create_assistant(
    name="Calendar Assistant",
    base_instructions="You are a helpful calendar assistant.",
    functions=[calendar_function]
)
```

#### Step 4: Add to Function Mapping
```python
# In open_ai_assistant_with_rag_and_function_call.py, add:
elif tool_call.function.name == "create_event":
    result = handler.create_event(**args)
```

### 5. Testing Your New Function

```python
# Test the new function
thread_id = manager.create_thread()
response = manager.add_message_and_run(
    thread_id=thread_id,
    assistant_id=assistant_id,
    query="Create a meeting tomorrow at 2 PM for 1 hour about project planning"
)
print(response)
```

### Key Requirements Summary:

1. **Task Schema**: Define function name, description, parameters, and requirements
2. **Function Handler**: Implement the actual function with proper error handling
3. **Assistant Manager**: Add function to the mapping in the message processing
4. **Function Config**: Create configuration object for the assistant
5. **Testing**: Test the complete flow from user input to function execution

### Common Patterns:

- **Save Operations**: Use `save_*` naming convention
- **Create Operations**: Use `create_*` naming convention
- **Update Operations**: Use `update_*` naming convention
- **Delete Operations**: Use `delete_*` naming convention

### Error Handling:
- Always wrap function logic in try-catch blocks
- Return consistent result format with success/error indicators
- Log errors for debugging
- Provide helpful error messages

### How the AI Assistant Works (Simple Explanation)
