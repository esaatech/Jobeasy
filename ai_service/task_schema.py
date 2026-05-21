from resume_builder.template_registry import TEMPLATE_ID_ENUM

TASK_SCHEMAS = {
    'resume': {
        'create_resume': {
            'name': 'create_resume',
            'description': 'Create a new resume for the user',
            'parameters': {
                'type': 'object',
                'properties': {
                    'user_id': {'type': 'string', 'description': 'ID of the user creating the resume'},
                    'resume_name': {'type': 'string', 'description': 'Name for the resume'},
                    'template_id': {'type': 'string', 'enum': TEMPLATE_ID_ENUM, 'description': 'Default template to use'}
                },
                'required': ['user_id', 'resume_name', 'template_id'],
                'additionalProperties': False
            }
        },
        'save_personal_info': {
            'name': 'save_personal_info',
            'description': 'Save personal information for resume with comprehensive validation (summary will be generated later)',
            'parameters': {
                'type': 'object',
                'properties': {
                    'user_id': {'type': 'string', 'description': 'ID of the user'},
                    'resume_id': {'type': 'string', 'description': 'ID of the resume to update'},
                    'full_name': {'type': 'string', 'description': 'Full name of the person'},
                    'email': {'type': 'string', 'description': 'Email address'},
                    'phone': {'type': 'string', 'description': 'Phone number'},
                    'location': {'type': 'string', 'description': 'City, State/Country'},
                    'linkedin': {'type': 'string', 'description': 'LinkedIn profile URL (optional)'},
                    'github': {'type': 'string', 'description': 'GitHub profile URL (optional)'},
                    'portfolio': {'type': 'string', 'description': 'Portfolio or personal website URL (optional)'},
                    'title': {'type': 'string', 'description': 'Professional title/position'}
                },
                'required': ['user_id', 'resume_id', 'full_name', 'email', 'phone', 'location', 'title'],
                'additionalProperties': False
            }
        },
        'save_experience': {
            'name': 'save_experience',
            'description': 'Add new work experience entries to existing ones (preserves existing experience)',
            'parameters': {
                'type': 'object',
                'properties': {
                    'user_id': {'type': 'string', 'description': 'ID of the user'},
                    'resume_id': {'type': 'string', 'description': 'ID of the resume to update'},
                    'experience_entries': {
                        'type': 'array',
                        'description': 'Array of work experience entries to add (will be appended to existing experience)',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'title': {'type': 'string', 'description': 'Job title'},
                                'company': {'type': 'string', 'description': 'Company name'},
                                'start_date': {'type': 'string', 'description': 'Start date in YYYY-MM format'},
                                'end_date': {'type': 'string', 'description': 'End date in YYYY-MM format (use "Present" for current positions)'},
                                'description': {'type': 'string', 'description': 'Job description and achievements formatted as HTML list (e.g., "<ul><li>Achievement 1</li><li>Achievement 2</li></ul>")'}
                            },
                            'required': ['title', 'company', 'start_date', 'end_date', 'description'],
                            'additionalProperties': False
                        }
                    }
                },
                'required': ['user_id', 'resume_id', 'experience_entries'],
                'additionalProperties': False
            }
        },
        'save_education': {
            'name': 'save_education',
            'description': 'Add new education entries to existing ones (preserves existing education)',
            'parameters': {
                'type': 'object',
                'properties': {
                    'user_id': {'type': 'string', 'description': 'ID of the user'},
                    'resume_id': {'type': 'string', 'description': 'ID of the resume to update'},
                    'education_entries': {
                        'type': 'array',
                        'description': 'Array of education entries to add (will be appended to existing education)',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'degree': {'type': 'string', 'description': 'Degree or qualification'},
                                'institution': {'type': 'string', 'description': 'Institution name'},
                                'start_date': {'type': 'string', 'description': 'Start date in YYYY-MM format'},
                                'end_date': {'type': 'string', 'description': 'End date in YYYY-MM format (use "Present" for current education)'},
                                'description': {'type': 'string', 'description': 'Additional details about the education formatted as HTML list (e.g., "<ul><li>Detail 1</li><li>Detail 2</li></ul>")'}
                            },
                            'required': ['degree', 'institution', 'start_date', 'end_date', 'description'],
                            'additionalProperties': False
                        }
                    }
                },
                'required': ['user_id', 'resume_id', 'education_entries'],
                'additionalProperties': False
            }
        },
        'save_skills': {
            'name': 'save_skills',
            'description': 'Save skills information with validation',
            'parameters': {
                'type': 'object',
                'properties': {
                    'user_id': {'type': 'string', 'description': 'ID of the user'},
                    'resume_id': {'type': 'string', 'description': 'ID of the resume to update'},
                    'technical_skills': {
                        'type': 'array',
                        'description': 'Array of technical skills (e.g., programming languages, tools, technologies)',
                        'items': {'type': 'string'}
                    },
                    'soft_skills': {
                        'type': 'array',
                        'description': 'Array of soft skills (e.g., communication, teamwork, leadership)',
                        'items': {'type': 'string'}
                    },
                    'languages': {
                        'type': 'array',
                        'description': 'Array of languages the person speaks',
                        'items': {'type': 'string'}
                    }
                },
                'required': ['user_id', 'resume_id', 'technical_skills', 'soft_skills', 'languages'],
                'additionalProperties': False
            }
        },
        'save_additional': {
            'name': 'save_additional',
            'description': 'Save additional information like certifications and projects',
            'parameters': {
                'type': 'object',
                'properties': {
                    'user_id': {'type': 'string', 'description': 'ID of the user'},
                    'resume_id': {'type': 'string', 'description': 'ID of the resume to update'},
                    'certifications': {
                        'type': 'string',
                        'description': 'Certifications, licenses, or professional qualifications formatted as HTML list (e.g., "<ul><li>Certification Name (Date)</li></ul>")'
                    },
                    'projects': {
                        'type': 'string',
                        'description': 'Projects, achievements, or additional work formatted as HTML list (e.g., "<ul><li>Project Name - Description</li></ul>")'
                    }
                },
                'required': ['user_id', 'resume_id', 'certifications', 'projects'],
                'additionalProperties': False
            }
        },
        'save_summary': {
            'name': 'save_summary',
            'description': 'Generate and save a professional summary based on the complete resume content',
            'parameters': {
                'type': 'object',
                'properties': {
                    'user_id': {'type': 'string', 'description': 'ID of the user'},
                    'resume_id': {'type': 'string', 'description': 'ID of the resume to update'},
                    'summary': {
                        'type': 'string',
                        'description': 'Professional summary formatted as HTML paragraph (e.g., "<p>Professional summary text...</p>")'
                    }
                },
                'required': ['user_id', 'resume_id', 'summary'],
                'additionalProperties': False
            }
        },
        'edit_personal_info': {
            'name': 'edit_personal_info',
            'description': 'Edit specific personal information fields',
            'parameters': {
                'type': 'object',
                'properties': {
                    'user_id': {'type': 'string', 'description': 'ID of the user'},
                    'resume_id': {'type': 'string', 'description': 'ID of the resume to update'},
                    'field': {'type': 'string', 'enum': ['full_name', 'email', 'phone', 'location', 'title'], 'description': 'Field to edit'},
                    'value': {'type': 'string', 'description': 'New value for the field'}
                },
                'required': ['user_id', 'resume_id', 'field', 'value'],
                'additionalProperties': False
            }
        },
        'edit_education': {
            'name': 'edit_education',
            'description': 'Edit a specific education entry by index',
            'parameters': {
                'type': 'object',
                'properties': {
                    'user_id': {'type': 'string', 'description': 'ID of the user'},
                    'resume_id': {'type': 'string', 'description': 'ID of the resume to update'},
                    'education_index': {'type': 'integer', 'description': 'Index of education entry to edit (0, 1, 2, etc.)'},
                    'field': {'type': 'string', 'enum': ['degree', 'institution', 'start_date', 'end_date', 'description'], 'description': 'Field to edit'},
                    'value': {'type': 'string', 'description': 'New value for the field'}
                },
                'required': ['user_id', 'resume_id', 'education_index', 'field', 'value'],
                'additionalProperties': False
            }
        },
        'delete_education': {
            'name': 'delete_education',
            'description': 'Delete a specific education entry by index',
            'parameters': {
                'type': 'object',
                'properties': {
                    'user_id': {'type': 'string', 'description': 'ID of the user'},
                    'resume_id': {'type': 'string', 'description': 'ID of the resume to update'},
                    'education_index': {'type': 'integer', 'description': 'Index of education entry to delete (0, 1, 2, etc.)'}
                },
                'required': ['user_id', 'resume_id', 'education_index'],
                'additionalProperties': False
            }
        },
        'edit_experience': {
            'name': 'edit_experience',
            'description': 'Edit a specific experience entry by index',
            'parameters': {
                'type': 'object',
                'properties': {
                    'user_id': {'type': 'string', 'description': 'ID of the user'},
                    'resume_id': {'type': 'string', 'description': 'ID of the resume to update'},
                    'experience_index': {'type': 'integer', 'description': 'Index of experience entry to edit (0, 1, 2, etc.)'},
                    'field': {'type': 'string', 'enum': ['title', 'company', 'start_date', 'end_date', 'description'], 'description': 'Field to edit'},
                    'value': {'type': 'string', 'description': 'New value for the field'}
                },
                'required': ['user_id', 'resume_id', 'experience_index', 'field', 'value'],
                'additionalProperties': False
            }
        },
        'delete_experience': {
            'name': 'delete_experience',
            'description': 'Delete a specific experience entry by index',
            'parameters': {
                'type': 'object',
                'properties': {
                    'user_id': {'type': 'string', 'description': 'ID of the user'},
                    'resume_id': {'type': 'string', 'description': 'ID of the resume to update'},
                    'experience_index': {'type': 'integer', 'description': 'Index of experience entry to delete (0, 1, 2, etc.)'}
                },
                'required': ['user_id', 'resume_id', 'experience_index'],
                'additionalProperties': False
            }
        },
        'list_templates': {
            'name': 'list_templates',
            'description': 'List available resume templates',
            'parameters': {
                'type': 'object',
                'properties': {
                    'user_id': {'type': 'string', 'description': 'ID of the user'}
                },
                'required': ['user_id'],
                'additionalProperties': False
            }
        },
        'preview_template': {
            'name': 'preview_template',
            'description': 'Preview a specific template without requiring a resume',
            'parameters': {
                'type': 'object',
                'properties': {
                    'user_id': {'type': 'string', 'description': 'ID of the user'},
                    'template_id': {'type': 'string', 'enum': TEMPLATE_ID_ENUM, 'description': 'Template to preview'}
                },
                'required': ['user_id', 'template_id'],
                'additionalProperties': False
            }
        },
        'switch_template': {
            'name': 'switch_template',
            'description': 'Switch template for an existing resume',
            'parameters': {
                'type': 'object',
                'properties': {
                    'user_id': {'type': 'string', 'description': 'ID of the user'},
                    'resume_id': {'type': 'string', 'description': 'ID of the resume to update'},
                    'template_id': {'type': 'string', 'enum': TEMPLATE_ID_ENUM, 'description': 'New template to use'}
                },
                'required': ['user_id', 'resume_id', 'template_id'],
                'additionalProperties': False
            }
        },
        'list_user_resumes': {
            'name': 'list_user_resumes',
            'description': 'Show user resumes in the utility tab - use this whenever the user asks about their resumes, wants to see them, or needs to work with them',
            'parameters': {
                'type': 'object',
                'properties': {
                    'user_id': {'type': 'string', 'description': 'ID of the user'}
                },
                'required': ['user_id'],
                'additionalProperties': False
            }
        },
        'get_resume_info': {
            'name': 'get_resume_info',
            'description': 'Get detailed information about a specific resume',
            'parameters': {
                'type': 'object',
                'properties': {
                    'user_id': {'type': 'string', 'description': 'ID of the user'},
                    'resume_id': {'type': 'string', 'description': 'ID of the resume to get info for'}
                },
                'required': ['user_id', 'resume_id'],
                'additionalProperties': False
            }
        },
        'finalize_resume': {
            'name': 'finalize_resume',
            'description': 'Mark a resume as complete and ready for use',
            'parameters': {
                'type': 'object',
                'properties': {
                    'user_id': {'type': 'string', 'description': 'ID of the user'},
                    'resume_id': {'type': 'string', 'description': 'ID of the resume to finalize'}
                },
                'required': ['user_id', 'resume_id'],
                'additionalProperties': False
            }
        },
        'get_current_date': {
            'name': 'get_current_date',
            'description': 'Get the current date in a format suitable for cover letters and formal documents.',
            'parameters': {
                'type': 'object',
                'properties': {
                    'user_id': {'type': 'string', 'description': 'ID of the user requesting the date'},
                    'format': {'type': 'string', 'description': 'Date format preference: "formal" (e.g., "January 15, 2024"), "short" (e.g., "Jan 15, 2024"), or "numeric" (e.g., "01/15/2024"). Default is "formal".'}
                },
                'required': ['user_id', 'format'],
                'additionalProperties': False
            }
        },
        'create_cover_letter': {
            'name': 'create_cover_letter',
            'description': 'Create a new cover letter for the user',
            'parameters': {
                'type': 'object',
                'properties': {
                    'user_id': {'type': 'string', 'description': 'ID of the user creating the cover letter'},
                    'cover_letter_name': {'type': 'string', 'description': 'Name for the cover letter'}
                },
                'required': ['user_id', 'cover_letter_name'],
                'additionalProperties': False
            }
        },
        'save_cover_letter_user_info': {
            'name': 'save_cover_letter_user_info',
            'description': 'Save user information for cover letter (name, address, email, phone)',
            'parameters': {
                'type': 'object',
                'properties': {
                    'user_id': {'type': 'string', 'description': 'ID of the user'},
                    'cover_letter_id': {'type': 'string', 'description': 'ID of the cover letter to update'},
                    'full_name': {'type': 'string', 'description': 'Full name of the person'},
                    'address': {'type': 'string', 'description': 'Address (City, State/Country)'},
                    'email': {'type': 'string', 'description': 'Email address'},
                    'phone': {'type': 'string', 'description': 'Phone number'}
                },
                'required': ['user_id', 'cover_letter_id', 'full_name', 'address', 'email', 'phone'],
                'additionalProperties': False
            }
        },
        'save_cover_letter_employer_info': {
            'name': 'save_cover_letter_employer_info',
            'description': 'Save employer information for cover letter (company, position, hiring manager)',
            'parameters': {
                'type': 'object',
                'properties': {
                    'user_id': {'type': 'string', 'description': 'ID of the user'},
                    'cover_letter_id': {'type': 'string', 'description': 'ID of the cover letter to update'},
                    'company_name': {'type': 'string', 'description': 'Name of the company'},
                    'position_title': {'type': 'string', 'description': 'Title of the position being applied for'}
                },
                'required': ['user_id', 'cover_letter_id', 'company_name', 'position_title'],
                'additionalProperties': False
            }
        },
        'save_cover_letter_greeting': {
            'name': 'save_cover_letter_greeting',
            'description': 'Save the greeting/salutation for the cover letter',
            'parameters': {
                'type': 'object',
                'properties': {
                    'user_id': {'type': 'string', 'description': 'ID of the user'},
                    'cover_letter_id': {'type': 'string', 'description': 'ID of the cover letter to update'},
                    'greeting': {'type': 'string', 'description': 'The greeting text (e.g., "Dear Hiring Manager," or "Dear Mr. Smith,")'}
                },
                'required': ['user_id', 'cover_letter_id', 'greeting'],
                'additionalProperties': False
            }
        },
        'save_cover_letter_introduction': {
            'name': 'save_cover_letter_introduction',
            'description': 'Save the introduction paragraph for the cover letter',
            'parameters': {
                'type': 'object',
                'properties': {
                    'user_id': {'type': 'string', 'description': 'ID of the user'},
                    'cover_letter_id': {'type': 'string', 'description': 'ID of the cover letter to update'},
                    'introduction': {'type': 'string', 'description': 'The introduction paragraph text'}
                },
                'required': ['user_id', 'cover_letter_id', 'introduction'],
                'additionalProperties': False
            }
        },
        'save_cover_letter_body': {
            'name': 'save_cover_letter_body',
            'description': 'Save the main body content for the cover letter',
            'parameters': {
                'type': 'object',
                'properties': {
                    'user_id': {'type': 'string', 'description': 'ID of the user'},
                    'cover_letter_id': {'type': 'string', 'description': 'ID of the cover letter to update'},
                    'body': {'type': 'string', 'description': 'The main body content of the cover letter'}
                },
                'required': ['user_id', 'cover_letter_id', 'body'],
                'additionalProperties': False
            }
        },
        'finalize_cover_letter': {
            'name': 'finalize_cover_letter',
            'description': 'Mark a cover letter as complete and ready for use',
            'parameters': {
                'type': 'object',
                'properties': {
                    'user_id': {'type': 'string', 'description': 'ID of the user'},
                    'cover_letter_id': {'type': 'string', 'description': 'ID of the cover letter to finalize'}
                },
                'required': ['user_id', 'cover_letter_id'],
                'additionalProperties': False
            }
        }
    }
}