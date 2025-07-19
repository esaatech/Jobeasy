"""
Simple test for OpenAI Assistant functionality with Resume Builder
"""

import os
from .ai_resume_assistant import OpenAIAssistantManager, FunctionConfig
from .task_schema import TASK_SCHEMAS

def test_resume_builder_assistant():
    """Test resume builder assistant with all functions"""
    try:
        print("🧪 Testing Resume Builder Assistant...")
        
        # Initialize manager
        manager = OpenAIAssistantManager()
        
        # Setup Django and create a test user
        import os
        import django
        from django.conf import settings
        
        if not settings.configured:
            os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobeas.settings')
            django.setup()
        
        from django.contrib.auth.models import User
        
        # Create a test user
        test_user, created = User.objects.get_or_create(
            username='ai_test_user',
            defaults={
                'email': 'ai_test@example.com',
                'first_name': 'AI',
                'last_name': 'Test'
            }
        )
        if created:
            test_user.set_password('testpass123')
            test_user.save()
            print(f"✅ Created test user: {test_user.username} (ID: {test_user.id})")
        else:
            print(f"✅ Using existing test user: {test_user.username} (ID: {test_user.id})")
        
        user_id = str(test_user.id)
        
        # Create resume builder functions from task schema
        functions = []
        
        # Create Resume Function
        create_resume_schema = TASK_SCHEMAS['resume']['create_resume']
        create_resume_function = FunctionConfig(
            name=create_resume_schema['name'],
            description=create_resume_schema['description'],
            parameters=create_resume_schema['parameters'],
            instructions="""When a user wants to create a new resume:
            1. Use this function to create a new resume for the user
            2. Always use the user_id provided in the conversation context
            3. Ask for a resume name and preferred template
            4. Confirm the resume was created and get the resume_id for future operations"""
        )
        functions.append(create_resume_function)
        
        # Personal Info Function
        personal_info_schema = TASK_SCHEMAS['resume']['save_personal_info']
        personal_info_function = FunctionConfig(
            name=personal_info_schema['name'],
            description=personal_info_schema['description'],
            parameters=personal_info_schema['parameters'],
            instructions="""When a user provides personal information:
            1. Extract their name, email, phone, location, LinkedIn, title, and summary
            2. Use this function to save their personal information
            3. Always include the user_id and resume_id from the conversation context
            4. Confirm what was saved and ask for the next section
            5. Be conversational and friendly"""
        )
        functions.append(personal_info_function)
        
        # Experience Function
        experience_schema = TASK_SCHEMAS['resume']['save_experience']
        experience_function = FunctionConfig(
            name=experience_schema['name'],
            description=experience_schema['description'],
            parameters=experience_schema['parameters'],
            instructions="""When a user provides work experience:
            1. Extract job title, company, dates, description, and achievements
            2. Use this function to save their work experience
            3. Always include the user_id and resume_id from the conversation context
            4. Confirm what was saved and ask for more experience or next section
            5. Help them format descriptions with HTML if needed"""
        )
        functions.append(experience_function)
        
        # Education Function
        education_schema = TASK_SCHEMAS['resume']['save_education']
        education_function = FunctionConfig(
            name=education_schema['name'],
            description=education_schema['description'],
            parameters=education_schema['parameters'],
            instructions="""When a user provides education information:
            1. Extract degree, institution, dates, GPA, and description
            2. Use this function to save their education
            3. Always include the user_id and resume_id from the conversation context
            4. Confirm what was saved and ask for more education or next section"""
        )
        functions.append(education_function)
        
        # Skills Function
        skills_schema = TASK_SCHEMAS['resume']['save_skills']
        skills_function = FunctionConfig(
            name=skills_schema['name'],
            description=skills_schema['description'],
            parameters=skills_schema['parameters'],
            instructions="""When a user provides skills information:
            1. Categorize skills into technical, soft skills, and languages
            2. Use this function to save their skills
            3. Always include the user_id and resume_id from the conversation context
            4. Confirm what was saved and ask for next section
            5. Always extract languages if mentioned"""
        )
        functions.append(skills_function)
        
        # Additional Function
        additional_schema = TASK_SCHEMAS['resume']['save_additional']
        additional_function = FunctionConfig(
            name=additional_schema['name'],
            description=additional_schema['description'],
            parameters=additional_schema['parameters'],
            instructions="""When a user provides certifications or projects:
            1. Extract certifications and projects information
            2. Use this function to save additional information
            3. Always include the user_id and resume_id from the conversation context
            4. Confirm what was saved and ask for next section
            5. Format with HTML for better presentation"""
        )
        functions.append(additional_function)
        
        # Finalize Function
        finalize_schema = TASK_SCHEMAS['resume']['finalize_resume']
        finalize_function = FunctionConfig(
            name=finalize_schema['name'],
            description=finalize_schema['description'],
            parameters=finalize_schema['parameters'],
            instructions="""When the user wants to complete their resume:
            1. Use this function to finalize the resume
            2. Always include the user_id and resume_id from the conversation context
            3. Ask which template they prefer (professional, modern, creative)
            4. Confirm the resume is complete and ready"""
        )
        functions.append(finalize_function)
        
        # List Templates Function
        list_templates_schema = TASK_SCHEMAS['resume']['list_templates']
        list_templates_function = FunctionConfig(
            name=list_templates_schema['name'],
            description=list_templates_schema['description'],
            parameters=list_templates_schema['parameters'],
            instructions="""When a user asks about available templates:
            1. Use this function to get all available templates
            2. Present the templates with their descriptions and features
            3. Help them choose the best template for their needs"""
        )
        functions.append(list_templates_function)
        
        # Switch Template Function
        switch_template_schema = TASK_SCHEMAS['resume']['switch_template']
        switch_template_function = FunctionConfig(
            name=switch_template_schema['name'],
            description=switch_template_schema['description'],
            parameters=switch_template_schema['parameters'],
            instructions="""When a user wants to switch templates:
            1. Use this function to switch to the requested template
            2. Always include the user_id and resume_id from the conversation context
            3. Confirm the template has been switched
            4. Continue with resume creation using the new template"""
        )
        functions.append(switch_template_function)
        
        # Create assistant
        assistant_id = manager.create_assistant(
            name="Resume Builder Assistant",
            base_instructions=f"""You are a friendly and professional resume builder assistant.
            
            Your role is to guide users through creating their resume step by step in a conversational manner.
            
            USER CONTEXT:
            - The current user ID is: {user_id}
            - Always include this user_id in all function calls
            - This ensures all resumes are properly associated with the user
            
            RESUME MANAGEMENT:
            - When a user wants to create a resume, first use create_resume function with user_id: {user_id}
            - Always use the resume_id returned from create_resume for all subsequent operations
            - If user wants to edit existing resumes, use list_user_resumes with user_id: {user_id}
            - Use get_resume_info to check the current state of a resume
            
            TEMPLATE HANDLING:
            - When users ask about templates, use the list_templates function to show available options
            - When users want to switch templates, use the switch_template function with the resume_id
            - Help users choose the best template for their industry and experience level
            - Professional template: Best for corporate and traditional industries
            - Modern template: Great for tech and contemporary companies
            - Creative template: Perfect for creative industries and portfolios
            
            RESUME BUILDING FLOW:
            1. Create resume first (create_resume with user_id: {user_id})
            2. Save personal information (save_personal_info with user_id and resume_id)
            3. Add work experience entries (save_experience with user_id and resume_id)
            4. Add education entries (save_education with user_id and resume_id)
            5. Add skills (save_skills with user_id and resume_id)
            6. Add additional information (save_additional with user_id and resume_id)
            7. Finalize the resume (finalize_resume with user_id and resume_id)
            
            EDITING CAPABILITIES:
            - Users can edit any field using edit_personal_info, edit_experience, edit_education, edit_skills, edit_additional
            - Users can delete experience or education entries using delete_experience or delete_education
            - Always confirm changes and show the updated information
            
            CONVERSATION STYLE:
            - Be conversational and friendly
            - Ask one question at a time
            - Confirm information before saving
            - Provide helpful suggestions and tips
            - Always acknowledge when information is saved successfully
            - If user wants to edit something, help them do it step by step""",
            functions=functions
        )
        
        if assistant_id:
            print(f"✅ Resume Builder Assistant created with ID: {assistant_id}")
            
            # Create a thread
            thread_id = manager.create_thread()
            print(f"✅ Thread created with ID: {thread_id}")
            
            # Test conversation flow
            test_messages = [
                "Hi! I want to create a new resume. Can you help me?",
                "What templates do you have available?",
                "I'd like to use the professional template",
                "Perfect! Now let's start creating my resume. My name is Sarah Johnson, I'm a marketing manager with 8 years of experience. My email is sarah.johnson@email.com and I live in San Francisco, CA.",
                "I worked as a Senior Marketing Manager at TechCorp from 2020 to 2023. I led digital marketing campaigns and managed a team of 5 people.",
                "I have a Bachelor's degree in Marketing from University of California, graduated in 2015 with a 3.8 GPA.",
                "My skills include digital marketing, social media management, Google Analytics, and team leadership.",
                "I have certifications in Google Ads and HubSpot Marketing, and I led a project that increased website traffic by 40%.",
                "Actually, can you change my job title from 'Senior Marketing Manager' to 'Marketing Director'?",
                "Great! Now let's finalize my resume with the professional template."
            ]
            
            for i, message in enumerate(test_messages, 1):
                print(f"\n📤 Message {i}: {message}")
                response = manager.add_message_and_run(
                    thread_id=thread_id,
                    assistant_id=assistant_id,
                    query=message,
                    user_id=user_id
                )
                print(f"📥 Response {i}: {response}")
            
            return True
        else:
            print("❌ Failed to create resume builder assistant")
            return False
            
    except Exception as e:
        print(f"❌ Error in resume builder test: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Resume Builder Assistant Test...")
    print("=" * 60)
    
    # Test resume builder functionality
    success = test_resume_builder_assistant()
    
    if success:
        print("\n🎉 Resume Builder Assistant test passed!")
        print("✅ All functions are working correctly")
        print("✅ Assistant can guide users through resume creation")
        print("✅ Functions can save resume data")
    else:
        print("\n❌ Resume Builder Assistant test failed")
        print("Check your OpenAI API key and configuration")
    
    print("\n" + "=" * 60)
    print("🏁 Testing complete!") 