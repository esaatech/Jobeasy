from .open_ai import client

def generate_cover_letter_from_raw_text(job_posting, resume_text, applicant_name=None, include_email_subject=False):
    """
    Generate a cover letter from raw job posting and resume text.
    For use with uploaded CV and/or unstructured job posting.
    
    Args:
        job_posting (str): The job posting/description text
        resume_text (str): The resume content text
        applicant_name (str, optional): The applicant's name. If not provided, AI will extract from resume
        include_email_subject (bool): Whether to also generate an email subject line
    
    Returns:
        dict: Contains success status, cover letter content, title, and optionally email subject
    """
    # If no applicant name provided, instruct AI to extract it from resume
    name_instruction = ""
    if not applicant_name or applicant_name.strip() == "":
        name_instruction = """
        IMPORTANT: No applicant name was provided. You must extract the applicant's full name from the resume text.
        Look for the name at the top of the resume, typically in the first few lines.
        Common patterns: "JOHN DOE", "John Doe", "J. Doe", etc.
        Use the most professional/complete version of the name you find.
        """
        applicant_name = "[EXTRACT_NAME_FROM_RESUME]"
    
    # Determine the system prompt based on whether email subject is requested
    if include_email_subject:
        system_prompt = """You are a professional cover letter writer who creates compelling, tailored cover letters and email subjects. 
        Generate the cover letter content AND a professional email subject line.
        
        Your response should be structured as follows:
        TITLE: [A professional title for the cover letter, 3-6 words, include company name like "Full Stack Developer Application at Company Name"]
        EMAIL_SUBJECT: [A compelling email subject line, 5-10 words]
        COVER_LETTER: [The full cover letter content]
        
        Do not include any additional formatting, headers, extra text, or appendices beyond these three sections."""
    else:
        system_prompt = """You are a professional cover letter writer who creates compelling, tailored cover letters. 
        Generate the cover letter content AND a professional title.
        
        Your response should be structured as follows:
        TITLE: [A professional title for the cover letter, 3-6 words, include company name like "Full Stack Developer Application at Company Name"]
        COVER_LETTER: [The full cover letter content]
        
        Do not include any additional formatting, headers, extra text, or appendices beyond these two sections."""
    
    try:
        cover_letter = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"""
                Create a professional cover letter based on the following resume and job posting:

                RESUME:
                {resume_text}

                JOB POSTING:
                {job_posting}

                {name_instruction}

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
                
                {f'The email subject should be compelling, professional, and specific to the role. Avoid generic subjects like "Job Application" or "Resume Submission". Use formats like "Application for [Position] at [Company]" or "[Position] - Application for [Company]" or "Applying for [Position] Role at [Company]". Make it clear this is a job application.' if include_email_subject else ''}
                """}
            ],
            temperature=0.7
        )

        # Clean and parse the response
        response_content = cover_letter.choices[0].message.content.strip()
        
        # Parse the structured response
        result = parse_ai_response(response_content, include_email_subject)
        
        # Clean the cover letter content
        if result.get('cover_letter'):
            result['cover_letter'] = clean_cover_letter_content(result['cover_letter'], applicant_name)
        
        return {
            'success': True,
            **result
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def parse_ai_response(response_content, include_email_subject):
    """
    Parse the AI response to extract title, email subject (if requested), and cover letter content.
    
    Args:
        response_content (str): The raw AI response
        include_email_subject (bool): Whether email subject was requested
    
    Returns:
        dict: Parsed content with title, email_subject (if applicable), and cover_letter
    """
    result = {}
    
    # Remove any markdown formatting
    if response_content.startswith('```'):
        response_content = response_content.split('```', 2)[1] if '```' in response_content else response_content
    
    lines = response_content.split('\n')
    current_section = None
    section_content = []
    
    for line in lines:
        line = line.strip()
        
        # Skip empty lines and markdown formatting
        if not line or line.startswith('#') or line.startswith('**') or line.startswith('*'):
            continue
        
        # Check for section headers
        if line.upper().startswith('TITLE:'):
            if current_section and section_content:
                result[current_section] = '\n'.join(section_content).strip()
            current_section = 'title'
            section_content = []
            # Extract title content (remove "TITLE:" prefix)
            title_content = line[6:].strip()
            if title_content:
                section_content.append(title_content)
            continue
            
        elif line.upper().startswith('EMAIL_SUBJECT:'):
            if current_section and section_content:
                result[current_section] = '\n'.join(section_content).strip()
            current_section = 'email_subject'
            section_content = []
            # Extract email subject content (remove "EMAIL_SUBJECT:" prefix)
            subject_content = line[14:].strip()
            if subject_content:
                section_content.append(subject_content)
            continue
            
        elif line.upper().startswith('COVER_LETTER:'):
            if current_section and section_content:
                result[current_section] = '\n'.join(section_content).strip()
            current_section = 'cover_letter'
            section_content = []
            # Extract cover letter content (remove "COVER_LETTER:" prefix)
            letter_content = line[13:].strip()
            if letter_content:
                section_content.append(letter_content)
            continue
        
        # Add content to current section
        if current_section:
            section_content.append(line)
    
    # Add the last section
    if current_section and section_content:
        result[current_section] = '\n'.join(section_content).strip()
    
    # If no structured response was found, treat the entire content as cover letter
    if not result:
        result['cover_letter'] = response_content
        result['title'] = 'Cover Letter'
        if include_email_subject:
            result['email_subject'] = 'Job Application'
    
    return result

def clean_cover_letter_content(cover_letter_content, applicant_name):
    """
    Clean the cover letter content to ensure proper formatting.
    
    Args:
        cover_letter_content (str): The raw cover letter content
        applicant_name (str): The applicant's name
    
    Returns:
        str: Cleaned cover letter content
    """
    if not cover_letter_content:
        return ""
    
    # Remove any structured sections that might be added at the end
    lines = cover_letter_content.split('\n')
    cleaned_lines = []
    found_closing = False
    signature_added = False
    
    for i, line in enumerate(lines):
        line = line.strip()
        
        # Skip markdown headers and formatting
        if line.startswith('#') or line.startswith('**') or line.startswith('*'):
            continue
            
        # Stop processing if we find structured content sections
        if any(section in line.lower() for section in ['experience:', 'skills:', 'education:', 'background:', 'qualifications:', 'summary:']):
            break
            
        # If we've found the closing, include it and look for the signature
        if 'sincerely,' in line.lower():
            found_closing = True
            cleaned_lines.append(line)
            continue
            
        # If we found closing and this is the signature line, include it
        if found_closing and line and not line.startswith('experience:') and not line.startswith('skills:'):
            cleaned_lines.append(line)
            signature_added = True
            break
            
        # Include normal content lines
        if line:
            cleaned_lines.append(line)
    
    # If we didn't find a proper signature, add it
    if found_closing and not signature_added:
        cleaned_lines.append(applicant_name)
    
    # Join the lines back together
    return '\n'.join(cleaned_lines) 