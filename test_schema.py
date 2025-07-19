#!/usr/bin/env python3
"""
Test script to verify the schema is valid and assistant can be created
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jobeas.settings')
django.setup()

from ai_service.ai_resume_assistant import OpenAIAssistantManager, FunctionConfig
from ai_service.task_schema import TASK_SCHEMAS

def test_schema():
    """Test that the schema is valid"""
    print("🔍 Testing schema validity...")
    
    try:
        # Test save_experience schema
        experience_schema = TASK_SCHEMAS['resume']['save_experience']
        print(f"✅ save_experience schema loaded successfully")
        
        # Check required fields
        required_fields = experience_schema['parameters']['properties']['experience_entries']['items']['required']
        print(f"📋 Required fields: {required_fields}")
        
        # Check all properties are in required
        properties = list(experience_schema['parameters']['properties']['experience_entries']['items']['properties'].keys())
        print(f"📋 All properties: {properties}")
        
        missing_required = [prop for prop in properties if prop not in required_fields]
        if missing_required:
            print(f"❌ Missing from required: {missing_required}")
            return False
        else:
            print(f"✅ All properties are in required array")
        
        # Test save_education schema
        education_schema = TASK_SCHEMAS['resume']['save_education']
        print(f"✅ save_education schema loaded successfully")
        
        # Check required fields
        required_fields = education_schema['parameters']['properties']['education_entries']['items']['required']
        print(f"📋 Required fields: {required_fields}")
        
        # Check all properties are in required
        properties = list(education_schema['parameters']['properties']['education_entries']['items']['properties'].keys())
        print(f"📋 All properties: {properties}")
        
        missing_required = [prop for prop in properties if prop not in required_fields]
        if missing_required:
            print(f"❌ Missing from required: {missing_required}")
            return False
        else:
            print(f"✅ All properties are in required array")
        
        return True
        
    except Exception as e:
        print(f"❌ Schema test failed: {str(e)}")
        return False

def test_assistant_creation():
    """Test that the assistant can be created"""
    print("\n🤖 Testing assistant creation...")
    
    try:
        # Initialize the manager
        manager = OpenAIAssistantManager()
        print("✅ Manager initialized")
        
        # Create assistant with resume building functions
        resume_functions = []
        for func_name, func_config in TASK_SCHEMAS['resume'].items():
            print(f"📋 Adding function: {func_name}")
            resume_functions.append(FunctionConfig(
                name=func_config['name'],
                description=func_config['description'],
                parameters=func_config['parameters'],
                instructions=f"Use this function when you need to {func_config['description'].lower()}"
            ))
        
        print(f"📋 Total functions: {len(resume_functions)}")
        
        assistant_id = manager.create_assistant(
            name="Test Resume Builder Assistant",
            base_instructions="You are a test assistant for resume building.",
            functions=resume_functions
        )
        
        if assistant_id:
            print(f"✅ Assistant created successfully with ID: {assistant_id}")
            return True
        else:
            print("❌ Assistant creation failed")
            return False
            
    except Exception as e:
        print(f"❌ Assistant creation test failed: {str(e)}")
        import traceback
        print(f"📋 Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    print("🧪 Starting schema and assistant tests...")
    
    # Test schema validity
    schema_valid = test_schema()
    
    if schema_valid:
        # Test assistant creation
        assistant_created = test_assistant_creation()
        
        if assistant_created:
            print("\n🎉 All tests passed! Schema is valid and assistant can be created.")
        else:
            print("\n❌ Assistant creation failed.")
            sys.exit(1)
    else:
        print("\n❌ Schema validation failed.")
        sys.exit(1) 