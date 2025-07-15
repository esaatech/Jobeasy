from openai import OpenAI, OpenAIError
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import json

# Initialize the client
client = OpenAI()

# Pydantic models for structured resume parsing
class PersonalInfo(BaseModel):
    full_name: str = Field(description="Full name of the candidate")
    email: str = Field(description="Email address")
    phone: str = Field(description="Phone number")
    location: str = Field(description="City, State/Country")
    linkedin: str = Field(description="LinkedIn profile URL")
    summary: str = Field(description="Professional summary or objective")
    title: str = Field(description="Professional title/position (e.g., 'Senior Software Engineer', 'Marketing Manager')")

class Experience(BaseModel):
    title: str = Field(description="Job title")
    company: str = Field(description="Company name")
    start_date: str = Field(description="Start date in YYYY-MM format")
    end_date: str = Field(description="End date in YYYY-MM format or 'Present'")
    description: str = Field(description="Complete job description including all responsibilities and achievements")
    achievements: List[str] = Field(description="List of key achievements and accomplishments")

class Education(BaseModel):
    degree: str = Field(description="Degree or qualification")
    institution: str = Field(description="Institution name")
    start_date: str = Field(description="Start date in YYYY-MM format")
    end_date: str = Field(description="End date in YYYY-MM format or 'Present'")
    gpa: str = Field(description="GPA if available")
    description: str = Field(description="Additional description if available")

class Skills(BaseModel):
    technical: List[str] = Field(description="Technical skills")
    soft: List[str] = Field(description="Soft skills")
    languages: List[str] = Field(description="Languages spoken")

class Additional(BaseModel):
    certifications: str = Field(description="Certifications and licenses")
    projects: str = Field(description="Notable projects")

class ResumeDataBasic(BaseModel):
    personal_info: PersonalInfo = Field(description="Personal information")
    education: List[Education] = Field(description="Education history")
    skills: Skills = Field(description="Skills categorized by type")
    additional: Additional = Field(description="Additional information")
    is_complete: bool = Field(description="Whether the resume data is complete")

class ResumeData(BaseModel):
    personal_info: PersonalInfo = Field(description="Personal information")
    experience: List[Experience] = Field(description="Work experience")
    education: List[Education] = Field(description="Education history")
    skills: Skills = Field(description="Skills categorized by type")
    additional: Additional = Field(description="Additional information")
    is_complete: bool = Field(description="Whether the resume data is complete")

class ExperienceList(BaseModel):
    experiences: List[Experience] = Field(description="List of work experience entries")

def format_resume_basic(resume_text: str) -> ResumeDataBasic:
    """
    Parse basic resume information (personal info, education, skills, additional) using OpenAI's structured response format.
    
    Args:
        resume_text (str): Raw resume text from uploaded file
        
    Returns:
        ResumeDataBasic: Structured basic resume data using Pydantic models
        
    Raises:
        Exception: If parsing fails
    """
    system_msg = (
        "You are an expert resume parser specializing in extracting basic resume information. "
        "Extract structured information from raw resume text with the following guidelines:\n\n"
        
        "PERSONAL INFORMATION:\n"
        "- Extract full name, email, phone, location, LinkedIn URL\n"
        "- For professional title: If explicitly provided, use it. If not provided, deduce the most appropriate title "
        "based on the candidate's most recent or most prominent job experience, skills, and overall career level\n"
        "- The title should be specific and professional (e.g., 'Senior Software Engineer', 'Marketing Manager', 'Project Coordinator')\n"
        "- If the resume shows multiple roles, choose the most recent or highest-level position\n"
        "- For professional summary: If the resume contains a professional summary/objective, extract it. "
        "If not present, generate a compelling 3-4 sentence professional summary based on the candidate's experience, "
        "skills, and career achievements. The summary should highlight key strengths, experience level, and career focus.\n\n"
        
        "EDUCATION:\n"
        "- Extract all education entries with degree, institution, dates, GPA, and descriptions\n"
        "- Use YYYY-MM format for dates. If only year is available, use YYYY-01\n"
        "- If current, set end_date to 'Present'\n\n"
        
        "SKILLS:\n"
        "- Categorize skills into technical, soft skills, and languages\n"
        "- Technical skills: programming languages, tools, technologies, software\n"
        "- Soft skills: communication, leadership, problem-solving, teamwork, etc.\n"
        "- Languages: spoken languages with proficiency levels if mentioned\n\n"
        
        "ADDITIONAL:\n"
        "- Extract certifications, licenses, and notable projects\n"
        "- Include any other relevant information that doesn't fit other categories\n\n"
        
        "GENERAL GUIDELINES:\n"
        "- Only extract information that is clearly present in the text\n"
        "- Do not invent or assume information\n"
        "- If a field is not found, use empty string or empty array as appropriate\n"
        "- Set is_complete to false if you cannot extract at least name, some education, and some skills"
    )
    
    user_msg = f"""
### RAW RESUME TEXT ###
{resume_text}

### TASK ###
Extract and structure the basic resume information (personal info, education, skills, additional) into the specified format.
Focus on accuracy and completeness. For the professional title, make sure to deduce an appropriate title if not explicitly provided.
For the professional summary, extract if present or generate a compelling one based on the candidate's background.
"""
    
    try:
        completion = client.chat.completions.parse(
            model="gpt-4o-2024-08-06",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg}
            ],
            response_format=ResumeDataBasic,
        )
        
        return completion.choices[0].message.parsed
        
    except (OpenAIError, Exception) as err:
        raise Exception(f"Basic resume parsing failed: {str(err)}")

def parse_experience_section(resume_text: str) -> List[Experience]:
    """
    Parse work experience section with detailed focus on complex formatting and complete descriptions.
    
    Args:
        resume_text (str): Raw resume text from uploaded file
        
    Returns:
        List[Experience]: List of structured work experience entries
        
    Raises:
        Exception: If parsing fails
    """
    system_msg = (
        "You are an expert resume parser specializing in work experience extraction. "
        "Your task is to extract ALL work experience entries with complete accuracy and detail.\n\n"
        
        "EXPERIENCE EXTRACTION GUIDELINES:\n"
        "1. **COMPLETE DESCRIPTIONS**: Extract the FULL job description, including all responsibilities, "
        "achievements, and details. Do not truncate or summarize unless the original text is extremely long.\n\n"
        
        "2. **ALL EXPERIENCE ENTRIES**: Ensure you capture EVERY work experience entry mentioned in the resume. "
        "Do not skip any jobs, even if they seem brief or less prominent.\n\n"
        
        "3. **DESCRIPTION FORMATTING**:\n"
        "   - Return descriptions as clean text with HTML formatting\n"
        "   - If there are multiple bullet points or achievements, format them as HTML lists\n"
        "   - Use <ul><li> for bullet points and <ol><li> for numbered lists\n"
        "   - Preserve all technical details, metrics, and specific accomplishments\n"
        "   - Include all responsibilities, technologies used, and quantifiable results\n"
        "   - Wrap paragraphs in <p> tags for proper formatting\n\n"
        
        "4. **ACHIEVEMENTS EXTRACTION**:\n"
        "   - Extract specific achievements, metrics, and quantifiable results as separate items\n"
        "   - Include all bullet points and accomplishment statements\n"
        "   - Preserve the original wording and detail level\n"
        "   - Each achievement should be a complete, standalone statement\n\n"
        
        "5. **DATE HANDLING**:\n"
        "   - Use YYYY-MM format for dates\n"
        "   - If only year is available, use YYYY-01\n"
        "   - For current positions, set end_date to 'Present'\n"
        "   - Handle various date formats (e.g., '2020-2023', 'Jan 2020 - Dec 2023', '2020-Present')\n\n"
        
        "6. **COMPANY AND TITLE EXTRACTION**:\n"
        "   - Extract complete company names including legal entities (Inc., LLC, etc.)\n"
        "   - Capture full job titles including seniority levels\n"
        "   - Handle multiple titles at the same company if mentioned\n\n"
        
        "7. **QUALITY STANDARDS**:\n"
        "   - Preserve all technical details, technologies used, and specific accomplishments\n"
        "   - Maintain the professional tone and detail level of the original\n"
        "   - Do not add, remove, or modify information - extract exactly what's present\n"
        "   - Ensure descriptions are comprehensive and include all relevant details\n\n"
        
        "8. **ERROR PREVENTION**:\n"
        "   - If you're unsure about any detail, include it rather than exclude it\n"
        "   - For long descriptions, prioritize completeness over brevity\n"
        "   - Ensure no experience entries are missed or partially captured\n"
        "   - Always return properly formatted HTML text for descriptions"
    )
    
    user_msg = f"""
### RAW RESUME TEXT ###
{resume_text}

### TASK ###
Extract ALL work experience entries from this resume with complete accuracy and detail.
Focus on capturing every job, complete descriptions, and all achievements.
Format descriptions as clean text with proper HTML formatting (use <ul><li> for bullets, <ol><li> for numbered lists).
Ensure no experience entries are missed or partially captured.
Return properly formatted HTML text for descriptions.
"""
    
    try:
        completion = client.chat.completions.parse(
            model="gpt-4o-2024-08-06",
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg}
            ],
            response_format=ExperienceList,
        )
        
        return completion.choices[0].message.parsed.experiences
        
    except (OpenAIError, Exception) as err:
        raise Exception(f"Experience parsing failed: {str(err)}")

def format_resume(resume_text: str) -> ResumeData:
    """
    Parse raw resume text and extract structured data using separate AI calls for basic info and experience.
    
    Args:
        resume_text (str): Raw resume text from uploaded file
        
    Returns:
        ResumeData: Complete structured resume data using Pydantic models
        
    Raises:
        Exception: If parsing fails
    """
    try:
        # Parse basic resume information
        basic_data = format_resume_basic(resume_text)
        
        # Parse work experience separately
        experience_data = parse_experience_section(resume_text)
        
        # Combine the data
        return ResumeData(
            personal_info=basic_data.personal_info,
            experience=experience_data,
            education=basic_data.education,
            skills=basic_data.skills,
            additional=basic_data.additional,
            is_complete=basic_data.is_complete and len(experience_data) > 0
        )
        
    except Exception as err:
        raise Exception(f"Complete resume parsing failed: {str(err)}")

def test_format_resume():
    """Test function for format_resume"""
    sample_resume_text = """
    JOHN DOE
    Software Engineer
    john.doe@email.com | (555) 123-4567 | New York, NY
    linkedin.com/in/johndoe

    PROFESSIONAL SUMMARY
    Experienced software engineer with 5+ years developing web applications using Python, JavaScript, and React. Passionate about creating scalable solutions and leading development teams.

    EXPERIENCE
    Senior Software Engineer
    Tech Corp | 2021 - Present
    - Led development of microservices architecture serving 1M+ users
    - Managed team of 5 developers and improved deployment efficiency by 40%
    - Implemented CI/CD pipelines reducing deployment time by 60%

    Software Engineer
    Startup Inc | 2019 - 2021
    - Developed REST APIs using Python Flask and Django
    - Built responsive frontend using React and TypeScript
    - Collaborated with cross-functional teams in agile environment

    EDUCATION
    Bachelor of Science in Computer Science
    University of Technology | 2019 | GPA: 3.8

    SKILLS
    Technical: Python, JavaScript, React, Node.js, AWS, Docker, Kubernetes
    Soft Skills: Leadership, Communication, Problem Solving, Team Collaboration
    Languages: English (Native), Spanish (Conversational)

    CERTIFICATIONS
    AWS Certified Developer Associate
    Google Cloud Professional Developer

    PROJECTS
    E-commerce Platform: Built full-stack application using React and Django
    """

    try:
        result = format_resume(sample_resume_text)
        print("\n✅ Structured Resume Parsing Output:")
        print(result.model_dump_json(indent=2))
        
        # Quick validation
        print(f"\n📊 Extraction Summary:")
        print(f"- Name extracted: {bool(result.personal_info.full_name)}")
        print(f"- Professional title: {result.personal_info.title}")
        print(f"- Experience entries: {len(result.experience)}")
        print(f"- Technical skills: {len(result.skills.technical)}")
        print(f"- Is complete: {result.is_complete}")
        
        # Print some details
        if result.experience:
            print(f"\n📋 First Experience Entry:")
            exp = result.experience[0]
            print(f"  Title: {exp.title}")
            print(f"  Company: {exp.company}")
            print(f"  Duration: {exp.start_date} to {exp.end_date}")
            print(f"  Description length: {len(exp.description)} characters")
            print(f"  Achievements count: {len(exp.achievements)}")
            
    except Exception as e:
        print(f"\n❌ Structured parsing failed: {str(e)}")

if __name__ == "__main__":
    test_format_resume() 