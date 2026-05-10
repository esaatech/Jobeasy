import logging

from .open_ai import client
from .prompt_formatting import coerce_skill_list, format_items_for_prompt

logger = logging.getLogger(__name__)


def normalize_optimization_result(data: dict) -> dict:
    """
    Map common AI / JSON key aliases onto fields _optimize_resume_for_job_application expects.
    Models often return Title Case keys (e.g. 'Professional Summary', 'Skills').
    """
    if not data:
        return data
    d = dict(data)

    opt = d.get("optimized_summary")
    has_summary = isinstance(opt, str) and bool(opt.strip())
    if not has_summary:
        for k in (
            "Professional Summary",
            "professional_summary",
            "Summary",
            "summary",
        ):
            v = d.get(k)
            if isinstance(v, str) and v.strip():
                d["optimized_summary"] = v.strip()
                break
            if v is not None and not isinstance(v, (dict, list, str)):
                d["optimized_summary"] = str(v).strip()
                break

    if d.get("reordered_technical_skills") is None:
        skills = d.get("Skills") or d.get("skills") or d.get("technical_skills")
        if isinstance(skills, list) and skills:
            d["reordered_technical_skills"] = coerce_skill_list(skills)

    if d.get("reordered_soft_skills") is None:
        ss = d.get("Soft Skills") or d.get("soft_skills")
        if isinstance(ss, list) and ss:
            d["reordered_soft_skills"] = coerce_skill_list(ss)

    if d.get("reordered_languages") is None:
        lang = d.get("Languages") or d.get("languages")
        if isinstance(lang, list) and lang:
            d["reordered_languages"] = coerce_skill_list(lang)

    if not d.get("relevant_experience"):
        ex = d.get("Experience") or d.get("experience")
        if isinstance(ex, list):
            d["relevant_experience"] = ex

    if d.get("ats_score") is None:
        ats = d.get("ATS Score") or d.get("ATS")
        if ats is not None:
            try:
                d["ats_score"] = int(str(ats).strip().rstrip("%"))
            except (ValueError, TypeError):
                d["ats_score"] = 0

    if not d.get("keyword_matches"):
        km = d.get("Keyword Matches") or d.get("keyword_matches")
        if isinstance(km, list):
            d["keyword_matches"] = [str(x) for x in km]

    if not d.get("improvement_suggestions"):
        imp = d.get("Improvement Suggestions") or d.get("improvement_suggestions")
        if isinstance(imp, list):
            d["improvement_suggestions"] = imp

    if d.get("reordered_projects") is None:
        pr = d.get("Projects") or d.get("projects")
        if isinstance(pr, list):
            d["reordered_projects"] = pr

    return d


def optimize_resume_for_job(job_description, resume_data, include_email_subject=False):
    """
    Optimize a resume for a specific job using AI.
    
    Args:
        job_description (str): The job posting/description text
        resume_data (dict): Structured resume data containing skills, experience, etc.
        include_email_subject (bool): Whether to also generate an email subject line
    
    Returns:
        dict: Contains success status, optimization results, title, and optionally email subject
    """
    # Determine the system prompt based on whether email subject is requested
    if include_email_subject:
        system_prompt = """You are a professional resume optimization expert who creates compelling, tailored resumes and email subjects. 
        Generate resume optimization AND a professional email subject line.
        
        Your response should be structured as follows:
        TITLE: [A professional title for the optimized resume, 3-6 words, include company name like "Senior Developer Resume for Google"]
        EMAIL_SUBJECT: [A compelling email subject line, 5-10 words]
        OPTIMIZATION: [All optimization data in JSON format]
        
        Do not include any additional formatting, headers, extra text, or appendices beyond these three sections."""
    else:
        system_prompt = """You are a professional resume optimization expert who creates compelling, tailored resumes. 
        Generate resume optimization AND a professional title.
        
        Your response should be structured as follows:
        TITLE: [A professional title for the optimized resume, 3-6 words, include company name like "Senior Developer Resume for Google"]
        OPTIMIZATION: [All optimization data in JSON format]
        
        Do not include any additional formatting, headers, extra text, or appendices beyond these two sections."""
    
    try:
        # Prepare the user prompt with resume data
        user_prompt = f"""
        Please optimize this resume for the following job description:

        JOB DESCRIPTION:
        {job_description}

        RESUME DATA:
        Professional Summary: {resume_data.get('professional_summary', 'N/A')}
        
        Technical Skills: {format_items_for_prompt(resume_data.get('technical_skills') or [])}
        Soft Skills: {format_items_for_prompt(resume_data.get('soft_skills') or [])}
        Languages: {format_items_for_prompt(resume_data.get('languages') or [])}
        
        Experience: {resume_data.get('experience', [])}
        Projects: {resume_data.get('projects', [])}

        Please provide:
        1. An optimized professional summary that highlights relevant experience
        2. Reordered skills (most relevant first)
        3. Relevant experience sections
        4. ATS score (0-100)
        5. Keyword matches
        6. Improvement suggestions
        7. Reordered projects (if applicable)
        
        {f'The email subject should be compelling, professional, and specific to the role. Use formats like "Application for [Position] at [Company]" or "[Position] - Application for [Company]".' if include_email_subject else ''}
        """

        logger.info(
            "resume_optimization: calling OpenAI (include_email_subject=%s)",
            include_email_subject,
        )
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7
        )

        # Clean and parse the response
        response_content = response.choices[0].message.content.strip()
        logger.debug("resume_optimization: raw response length=%s", len(response_content))

        # Parse the structured response
        result = parse_ai_response(response_content, include_email_subject)
        os = result.get("optimized_summary")
        has_summary = isinstance(os, str) and bool(os.strip())
        logger.info(
            "resume_optimization: parsed ok title=%r has_optimized_summary=%s",
            result.get("title"),
            has_summary,
        )

        return {
            'success': True,
            **result
        }

    except Exception as e:
        logger.exception("resume_optimization: failed")
        return {
            'success': False,
            'error': str(e)
        }

def parse_ai_response(response_content, include_email_subject):
    """
    Parse the AI response to extract title, email subject (if requested), and optimization data.
    
    Args:
        response_content (str): The raw AI response
        include_email_subject (bool): Whether email subject was requested
    
    Returns:
        dict: Parsed content with title, email_subject (if applicable), and optimization data
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
            
        elif line.upper().startswith('OPTIMIZATION:'):
            if current_section and section_content:
                result[current_section] = '\n'.join(section_content).strip()
            current_section = 'optimization'
            section_content = []
            # Extract optimization content (remove "OPTIMIZATION:" prefix)
            optimization_content = line[13:].strip()
            if optimization_content:
                section_content.append(optimization_content)
            continue
        
        # Add content to current section
        if current_section:
            section_content.append(line)
    
    # Add the last section
    if current_section and section_content:
        result[current_section] = '\n'.join(section_content).strip()
    
    # Parse optimization data if present
    if result.get('optimization'):
        optimization_data = parse_optimization_data(result['optimization'])
        result.update(optimization_data)
    
    # If no structured response was found, treat the entire content as optimization
    if not result:
        result['title'] = 'Optimized Resume'
        if include_email_subject:
            result['email_subject'] = 'Job Application'
        # Try to parse the content as optimization data
        optimization_data = parse_optimization_data(response_content)
        result.update(optimization_data)

    return normalize_optimization_result(result)

def parse_optimization_data(optimization_content):
    """
    Parse the optimization content to extract structured data.
    
    Args:
        optimization_content (str): The optimization section content
    
    Returns:
        dict: Parsed optimization data
    """
    try:
        # Try to parse as JSON first
        import json
        return json.loads(optimization_content)
    except json.JSONDecodeError:
        # If not valid JSON, try to extract key-value pairs
        result = {}
        lines = optimization_content.split('\n')
        
        for line in lines:
            line = line.strip()
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().lower().replace(' ', '_')
                value = value.strip()
                
                # Try to parse lists
                if value.startswith('[') and value.endswith(']'):
                    try:
                        value = json.loads(value)
                    except:
                        pass
                
                result[key] = value
        
        return result 