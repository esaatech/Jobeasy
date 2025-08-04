from openai import OpenAI, OpenAIError
from datetime import datetime
from dotenv import load_dotenv
import os
import json

load_dotenv()
# Initialize the client
client = OpenAI()  # Make sure OPENAI_API_KEY is set in your environment
def optimize_resume_for_job(job_description: str, resume_text: str):
    """
    Given a job description and pre-formatted resume text, call ChatGPT to:
    1. Rewrite / optimise the resume text to match the posting.
    2. Return a JSON payload with the fields you need to re-populate the
       structured columns of your Resume model.
    """
    system_msg = (
        "You are an elite ATS-optimization assistant. "
        "Your job is to transform a candidate's resume so it matches a "
        "specific job description. You MUST respond with **valid JSON only**, "
        "no markdown, using the exact schema shown:\n\n"
        "{\n"
        '  "optimized_content": str,\n'
        '  "personal_info": { "full_name": "...", "email": "...", "phone": "...", "location": "...", "linkedin": "..." },\n'
        '  "experience": [ { "title": "...", "company": "...", "duration": "...", "description": "...", "achievements": ["..."] } ],\n'
        '  "education": [ { "degree": "...", "institution": "...", "year": "...", "gpa": "..." } ],\n'
        '  "skills": { "Category 1": ["Skill A", "Skill B"] },\n'
        '  "additional": { "Key": "Value" },\n'
        '  "keyword_matches": [ "Keyword1", "Keyword2" ],\n'
        '  "improvement_suggestions": [ "Suggestion 1" ],\n'
        '  "ats_score": 85\n'
        "}"
    )

    user_msg = f"""
    ### JOB DESCRIPTION ###
    {job_description}

    ### CURRENT RESUME ###
    {resume_text}

    ### TASK ###
    1. Rewrite the resume so it clearly reflects the most relevant skills,
       achievements and keywords from the job posting.
    2. Populate *all* fields in the JSON schema.
       - Do not invent experience; only re-phrase or re-order what you see.
       - The `optimized_content` should be a full, ATS-friendly, plain-text resume.
    """

    try:
        chat_resp = client.chat.completions.create(
            model="gpt-4o",
            temperature=0.3,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg}
            ],
            response_format={"type": "json_object"}
        )

        raw_json = chat_resp.choices[0].message.content.strip()
        data = json.loads(raw_json)
        return {"success": True, "data": data}

    except (OpenAIError, json.JSONDecodeError) as err:
        return {"success": False, "error": str(err)}


EXPECTED_KEYS = {
    "optimized_summary",
    "relevant_experience",
    "reordered_skills",
    "reordered_projects",
    "keyword_matches",
    "improvement_suggestions",
    "ats_score",
}

def optimize_my_resume_for_job(job_description: str, resume_data: dict):
    """
    Optimise a structured resume dict for a given job posting.
    Input (resume_data):
        professional_summary : str
        experience           : list[dict]
        technical_skills     : list[str]
        soft_skills          : list[str]
        languages            : list[str]
        projects             : list[dict]
    Output:
        {
          "optimized_summary": str,
          "relevant_experience": [ {...} ],
          "reordered_technical_skills": [...],
          "reordered_soft_skills": [...],
          "reordered_languages": [...],
          "reordered_projects": [ {...} ],
          "keyword_matches": [ ... ],
          "improvement_suggestions": [ ... ],
          "ats_score": int
        }
    """
    system_msg = (
        "You are an elite resume-optimization assistant. "
        "Return ONLY valid JSON (no markdown) with exactly these keys and nothing else:\n\n"
        "{\n"
        '  "optimized_summary": str,\n'
        '  "relevant_experience": [ { "title": "...", "company": "...", '
        '"duration": "...", "description": "...", "achievements": ["..."] } ],\n'
        '  "reordered_technical_skills": ["Skill1", "Skill2"],\n'
        '  "reordered_soft_skills": ["Skill3", "Skill4"],\n'
        '  "reordered_languages": ["English", "Spanish"],\n'
        '  "reordered_projects": [ { "name": "...", "description": "...", "impact": "..." } ],\n'
        '  "keyword_matches": [ "Keyword1", "Keyword2" ],\n'
        '  "improvement_suggestions": [ "Suggestion 1", "Suggestion 2" ],\n'
        '  "ats_score": 0\n'
        "}"
    )
    user_msg = f"""
### JOB DESCRIPTION ###
{job_description}

### STRUCTURED RESUME INPUT ###
Professional Summary: {resume_data.get('professional_summary', '')}

Experience: {json.dumps(resume_data.get('experience', []), indent=2)}

Technical Skills: {json.dumps(resume_data.get('technical_skills', []), indent=2)}

Soft Skills: {json.dumps(resume_data.get('soft_skills', []), indent=2)}

Languages: {json.dumps(resume_data.get('languages', []), indent=2)}

Projects: {json.dumps(resume_data.get('projects', []), indent=2)}

### TASK ###
• Rewrite the professional summary → optimized_summary
• Select and return ONLY experience entries relevant to the job → relevant_experience
• Reorder technical skills so the most relevant are first → reordered_technical_skills
• Reorder soft skills so the most relevant are first → reordered_soft_skills
• Reorder languages so the most relevant are first → reordered_languages
• Reorder / filter projects so the most relevant are first → reordered_projects
• List the job-matching keywords you used → keyword_matches
• Provide constructive improvement suggestions → improvement_suggestions
• Estimate an ATS match score (0–100) → ats_score
• Do NOT add education, personal info, or any other fields.
• Respond with JSON ONLY, using exactly the keys shown above.
"""
    try:
        chat_resp = client.chat.completions.create(
            model="gpt-4o",
            temperature=0.3,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg}
            ],
            response_format={"type": "json_object"}
        )
        data = json.loads(chat_resp.choices[0].message.content.strip())
        # Filter to only expected keys and return directly
        expected_keys = [
            "optimized_summary", "relevant_experience",
            "reordered_technical_skills", "reordered_soft_skills", "reordered_languages",
            "reordered_projects", "keyword_matches", "improvement_suggestions", "ats_score"
        ]
        return {k: v for k, v in data.items() if k in expected_keys}
    except (OpenAIError, json.JSONDecodeError) as err:
        raise Exception(f"Resume optimization failed: {str(err)}")

def test_optimize_my_resume_for_job():
    # Sample job description
    job_description = """
    Shelter Cook – Part-Time
    We need a reliable cook to plan and prepare daily meals for 60–80 individuals at our community shelter.
    Must be able to work independently, manage food donations, and follow safety protocols.
    Experience with large-batch cooking, sanitation, and meal planning is required.
    """

    # Sample structured resume input
    resume_data = {
        "professional_summary": (
            "Hardworking and detail-oriented cook with experience in fast-paced kitchens. Skilled at preparing "
            "meals efficiently and keeping workspaces clean and organized. Committed to food safety and "
            "high-quality service."
        ),
        "experience": [
            {
                "title": "Line Cook",
                "company": "Sunset Grill",
                "duration": "2021 – Present",
                "description": "Prepared meals in a busy restaurant setting and ensured compliance with health codes.",
                "achievements": [
                    "Reduced food waste by 15% through better portion control",
                    "Trained 3 new kitchen assistants"
                ]
            },
            {
                "title": "Kitchen Assistant",
                "company": "Downtown Shelter",
                "duration": "2019 – 2021",
                "description": "Helped prepare meals for up to 80 people and managed food donations.",
                "achievements": [
                    "Assisted in planning weekly menus using limited supplies",
                    "Maintained perfect inspection scores from public health visits"
                ]
            }
        ],
        "technical_skills": ["Batch cooking", "Knife skills", "Inventory rotation"],
        "soft_skills": ["Teamwork", "Time management", "Attention to detail"],
        "languages": ["English", "Spanish"],
        "projects": []
    }

    try:
        result = optimize_my_resume_for_job(job_description, resume_data)
        print("\n✅ Optimized Resume Output:")
        print(json.dumps(result, indent=2))
        
        # Quick validation
        expected_keys = {"optimized_summary", "relevant_experience", "reordered_technical_skills", 
                        "reordered_soft_skills", "reordered_languages", "reordered_projects", "keyword_matches", "improvement_suggestions", "ats_score"}
        actual_keys = set(result.keys())
        
        if expected_keys == actual_keys:
            print("\n✅ All expected keys present!")
        else:
            print(f"\n⚠️ Key mismatch. Expected: {expected_keys}, Got: {actual_keys}")
            
    except Exception as e:
        print(f"\n❌ Optimization failed: {str(e)}")

# Don't forget to import json at the top if not already imported



def test_cover_letter():
    job_details = {
        "position": "Senior Software Engineer",
        "company": "Tech Corp",
        "description": "Looking for experienced developer...",
        "department": "Engineering"
    }

    candidate_details = {
        "name": "Jane Smith",
        "current_role": "Software Engineer",
        "experience": "5 years",
        "skills": "Python, JavaScript, AWS",
        "achievements": "Led team of 5, increased efficiency by 40%"
    }     

    #cover_letter = generate_cover_letter_from_fields(job_details, candidate_details)       
    #print(cover_letter)

    
    # Example usage with raw text
    job_posting = """
    Senior Software Engineer - AI/ML Team
    
    We're looking for a Senior Software Engineer to join our AI/ML team. The ideal candidate will have strong Python experience and a background in machine learning deployments. You'll be responsible for building and maintaining our ML infrastructure and working closely with data scientists.

    Requirements:
    - 5+ years of software development experience
    - Strong Python programming skills
    - Experience with ML frameworks (TensorFlow, PyTorch)
    - Knowledge of cloud platforms (AWS preferred)
    - Experience with containerization and orchestration
    
    About us:
    Tech Corp is a leading AI company focused on building ethical AI solutions. We value innovation, collaboration, and continuous learning.
    """

    resume = """
    JANE SMITH
    Software Engineer
    email@example.com | (555) 123-4567

    EXPERIENCE
    Senior Developer, AI Solutions Inc.
    2020-Present
    - Led team of 5 developers in building ML pipeline
    - Reduced model deployment time by 40%
    - Implemented automated testing for ML models

    Software Engineer, Tech Startup
    2018-2020
    - Developed Python microservices
    - Worked with AWS and Docker

    SKILLS
    Python, TensorFlow, PyTorch, AWS, Docker, Kubernetes
    """

    # The original generate_cover_letter_from_raw_text function is removed,
    # so this test will now fail.
    # result = generate_cover_letter_from_raw_text(job_posting, resume, "Jane Smith")
    
    # if result['success']:
    #     print("COVER LETTER:")
    #     print("-" * 50)
    #     print(result['cover_letter'])
    # else:
    #     print("Error:", result['error'])

def parse_resume_from_text(resume_text: str):
    """
    Parse raw resume text and extract structured data for creating a Resume object.
    Input: Raw resume text from uploaded file
    Output: Structured resume data that can be used to create a Resume model instance
    """
    system_msg = (
        "You are an expert resume parser. Extract structured information from raw resume text. "
        "Return ONLY valid JSON (no markdown) with exactly these keys and nothing else:\n\n"
        "{\n"
        '  "personal_info": { "full_name": "...", "email": "...", "phone": "...", "location": "...", "linkedin": "...", "summary": "..." },\n'
        '  "experience": [ { "title": "...", "company": "...", "start_date": "YYYY-MM", "end_date": "YYYY-MM or Present", "description": "...", "achievements": ["..."] } ],\n'
        '  "education": [ { "degree": "...", "institution": "...", "start_date": "YYYY-MM", "end_date": "YYYY-MM or Present", "gpa": "...", "description": "..." } ],\n'
        '  "skills": { "technical": ["Skill1", "Skill2"], "soft": ["Skill3", "Skill4"], "languages": ["English", "Spanish"] },\n'
        '  "additional": { "certifications": "...", "projects": "..." },\n'
        '  "is_complete": true\n'
        "}"
        ")\n\n"
        "If the resume does not contain a professional summary, generate a concise and relevant professional summary for the candidate based on their experience, education, and skills."
    )
    
    user_msg = f"""
### RAW RESUME TEXT ###
{resume_text}

### TASK ###
Extract and structure the resume information into the JSON format above:

• personal_info: Extract name, email, phone, location, LinkedIn, and professional summary
• experience: List all work experience with title, company, start_date (YYYY-MM), end_date (YYYY-MM or Present), description, and achievements
• education: List all education with degree, institution, start_date (YYYY-MM), end_date (YYYY-MM or Present), GPA if available, and description if available
• skills: Categorize skills into technical, soft skills, and languages
• additional: Extract certifications, projects, or other relevant information
• is_complete: Set to true if you can extract most fields, false if data is incomplete

Guidelines:
- For each experience and education entry, always extract start_date and end_date if available. Use the format YYYY-MM (e.g., 2022-03). If only a year is present, use YYYY-01. If the entry is current, set end_date to "Present". If a date is not found, use an empty string.
- Only extract information that is clearly present in the text
- Do not invent or assume information
- If a field is not found, use empty string or empty array as appropriate
- For skills, categorize them appropriately (technical vs soft skills)
- Set is_complete to false if you cannot extract at least name, some experience, and some skills

Respond with JSON ONLY, using exactly the keys shown above.
"""
    
    try:
        chat_resp = client.chat.completions.create(
            model="gpt-4o",
            temperature=0.1,  # Lower temperature for more consistent parsing
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg}
            ],
            response_format={"type": "json_object"}
        )
        
        data = json.loads(chat_resp.choices[0].message.content.strip())
        
        # Validate and clean the data
        expected_keys = ["personal_info", "experience", "education", "skills", "additional", "is_complete"]
        cleaned_data = {k: v for k, v in data.items() if k in expected_keys}
        
        # Ensure all required nested structures exist
        if "personal_info" not in cleaned_data:
            cleaned_data["personal_info"] = {}
        if "experience" not in cleaned_data:
            cleaned_data["experience"] = []
        else:
            # Ensure each experience entry has start_date and end_date
            for exp in cleaned_data["experience"]:
                exp.setdefault("start_date", "")
                exp.setdefault("end_date", "")
        if "education" not in cleaned_data:
            cleaned_data["education"] = []
        if "skills" not in cleaned_data:
            cleaned_data["skills"] = {"technical": [], "soft": [], "languages": []}
        if "additional" not in cleaned_data:
            cleaned_data["additional"] = {}
        if "is_complete" not in cleaned_data:
            cleaned_data["is_complete"] = False
            
        return cleaned_data
        
    except (OpenAIError, json.JSONDecodeError) as err:
        raise Exception(f"Resume parsing failed: {str(err)}")

def test_parse_resume_from_text():
    """Test function for parse_resume_from_text"""
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
        result = parse_resume_from_text(sample_resume_text)
        print("\n✅ Resume Parsing Output:")
        print(json.dumps(result, indent=2))
        
        # Quick validation
        expected_keys = {"personal_info", "experience", "education", "skills", "additional", "is_complete"}
        actual_keys = set(result.keys())
        
        if expected_keys == actual_keys:
            print("\n✅ All expected keys present!")
        else:
            print(f"\n⚠️ Key mismatch. Expected: {expected_keys}, Got: {actual_keys}")
            
        # Check if data was extracted properly
        personal_info = result.get('personal_info', {})
        experience = result.get('experience', [])
        skills = result.get('skills', {})
        
        print(f"\n📊 Extraction Summary:")
        print(f"- Name extracted: {bool(personal_info.get('full_name'))}")
        print(f"- Experience entries: {len(experience)}")
        print(f"- Technical skills: {len(skills.get('technical', []))}")
        print(f"- Is complete: {result.get('is_complete')}")
            
    except Exception as e:
        print(f"\n❌ Parsing failed: {str(e)}")

def generate_professional_summary(resume_data: dict):
    """
    Generate a professional summary for a resume using all relevant information.
    Input: resume_data (dict) with keys: personal_info, experience, education, skills, additional
    Output: { 'success': True, 'summary': str } or { 'success': False, 'error': str }
    """
    system_msg = (
        "You are an expert resume writer. Given a candidate's full resume data, "
        "write a concise, compelling professional summary (3-5 sentences) that highlights their most relevant "
        "skills, experience, and strengths. The summary should be suitable for the top of a modern resume, "
        "written in a professional, first-person implied style (do NOT use the candidate's name, and do NOT use 'he', 'she', or 'they'). "
        "Do NOT include any personal pronouns or refer to the candidate by name. "
        "Focus on value, impact, and expertise. Respond with JSON: { 'summary': ... } only."
    )
    user_msg = f"""
### RESUME DATA ###
Personal Info: {json.dumps(resume_data.get('personal_info', {}), indent=2)}
Experience: {json.dumps(resume_data.get('experience', []), indent=2)}
Education: {json.dumps(resume_data.get('education', []), indent=2)}
Skills: {json.dumps(resume_data.get('skills', {}), indent=2)}
Additional: {json.dumps(resume_data.get('additional', {}), indent=2)}
### TASK ###
Write a professional summary for this candidate. Respond with JSON: {{ 'summary': ... }} only.
"""
    try:
        chat_resp = client.chat.completions.create(
            model="gpt-4o",
            temperature=0.3,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_msg}
            ],
            response_format={"type": "json_object"}
        )
        data = json.loads(chat_resp.choices[0].message.content.strip())
        return {"success": True, "summary": data.get("summary", "")}
    except (OpenAIError, json.JSONDecodeError) as err:
        return {"success": False, "error": str(err)}

if __name__ == "__main__":
    # Example usage:
    test_optimize_my_resume_for_job()
    print("\n" + "="*50)
    test_parse_resume_from_text()


