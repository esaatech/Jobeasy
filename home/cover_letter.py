from openai import OpenAI
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()
# Initialize the client
client = OpenAI()  # Make sure OPENAI_API_KEY is set in your environment



def generate_cover_letter_from_raw_text(job_posting, resume_text):
    """
    Generate a cover letter from raw job posting and resume text.
    For use with uploaded CV and/or unstructured job posting.
    """
    # Extract name from resume_text (first line typically)
    applicant_name = resume_text.strip().split('\n')[0]
    
    try:
        cover_letter = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a professional cover letter writer who creates compelling, tailored cover letters."},
                {"role": "user", "content": f"""
                Create a professional cover letter based on the following resume and job posting:

                RESUME:
                {resume_text}

                JOB POSTING:
                {job_posting}

                The cover letter should:
                1. Start with "Dear Hiring Manager,"
                2. Focus on the most relevant experiences from the resume
                3. Demonstrate clear understanding of the company's needs
                4. Show enthusiasm for the role and company
                5. Include specific examples and achievements
                6. Maintain a professional yet engaging tone
                7. End with "Sincerely," followed by "{applicant_name}" on a new line
                8. Do not include any dates or addresses

                Keep the length to one page maximum.
                """}
            ],
            temperature=0.7
        )

        return {
            'success': True,
            'cover_letter': cover_letter.choices[0].message.content
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

















def generate_cover_letter_from_fields(job_details, candidate_details):
    """
    Generate a cover letter from structured input fields.
    For use with manually entered experience and job details.
    """
    try:
        cover_letter = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a professional cover letter writer who creates compelling, tailored cover letters."},
                {"role": "user", "content": f"""
                Generate a professional cover letter with the following details:

                JOB DETAILS:
                Position: {job_details.get('position')}
                Company: {job_details.get('company')}
                Department: {job_details.get('department')}
                Description: {job_details.get('description')}

                CANDIDATE DETAILS:
                Name: {candidate_details.get('full_name')}
                Current Role: {candidate_details.get('current_role')}
                Experience: {candidate_details.get('experience')}
                Key Skills: {candidate_details.get('key_skills')}
                Achievements: {candidate_details.get('achievements')}

                The cover letter should:
                1. Start with "Dear Hiring Manager,"
                2. Focus on relevant experiences
                3. Demonstrate clear understanding of the company's needs
                4. Show enthusiasm for the role and company
                5. Include specific examples and achievements
                6. Maintain a professional yet engaging tone
                7. End with "Sincerely," followed by "{candidate_details.get('full_name')}" on a new line
                8. Do not include any dates or addresses

                Keep the length to one page maximum.
                """}
            ],
            temperature=0.7
        )

        return {
            'success': True,
            'cover_letter': cover_letter.choices[0].message.content
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


if __name__ == "__main__":
    # Example usage:
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

    result = generate_cover_letter_from_raw_text(job_posting, resume)
    
    if result['success']:
        print("COVER LETTER:")
        print("-" * 50)
        print(result['cover_letter'])
    else:
        print("Error:", result['error'])
