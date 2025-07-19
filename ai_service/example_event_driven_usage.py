"""
Example: Event-Driven Backend-to-Frontend Communication

This example demonstrates how the AI assistant can trigger frontend actions
directly from function handlers using Django Channels WebSocket events.

The flow works like this:
1. User sends message to AI: "Switch to modern template"
2. AI calls switch_template function
3. Function handler emits event via EventEmitter
4. WebSocket consumer receives event and sends to frontend
5. Frontend JavaScript handles event and updates UI
"""

import json
from typing import Dict, Any

# Example 1: User asks to switch template
def example_switch_template():
    """
    Example: User says "Switch to modern template"
    """
    print("=" * 60)
    print("EXAMPLE 1: Template Switching via AI")
    print("=" * 60)
    
    # User message
    user_message = "Switch to modern template"
    print(f"👤 User: {user_message}")
    
    # AI processes and calls function
    function_call = {
        "name": "switch_template",
        "arguments": json.dumps({
            "user_id": "123",
            "resume_id": "456",
            "template_id": "modern"
        })
    }
    print(f"🤖 AI Function Call: {function_call}")
    
    # Function handler executes
    result = {
        "success": True,
        "message": "Template switched to modern successfully",
        "data": {
            "resume_id": "456",
            "template_id": "modern",
            "user_id": "123"
        }
    }
    print(f"🔧 Function Result: {result}")
    
    # EventEmitter sends event to frontend
    event_data = {
        "event_type": "template_changed",
        "data": {
            "resume_id": "456",
            "template_id": "modern",
            "action": "switch_template",
            "timestamp": "2024-01-15T10:30:00Z"
        }
    }
    print(f"🎯 Event Emitted: {event_data}")
    
    # Frontend receives event and updates UI
    frontend_actions = [
        "1. WebSocket receives 'template_changed' event",
        "2. ChatUI.handleTemplateChanged() called",
        "3. TemplatePreview.switchTemplate('modern') called",
        "4. Template button 'modern' becomes active",
        "5. Resume preview updates with modern template",
        "6. Success message added to chat"
    ]
    
    print("\n📱 Frontend Actions:")
    for action in frontend_actions:
        print(f"   {action}")
    
    print("\n✅ Result: Template switched without user clicking!")

# Example 2: User creates resume
def example_create_resume():
    """
    Example: User says "Create a new resume called My Professional Resume"
    """
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Resume Creation via AI")
    print("=" * 60)
    
    # User message
    user_message = "Create a new resume called My Professional Resume"
    print(f"👤 User: {user_message}")
    
    # AI processes and calls function
    function_call = {
        "name": "create_resume",
        "arguments": json.dumps({
            "user_id": "123",
            "resume_name": "My Professional Resume",
            "template_id": "professional"
        })
    }
    print(f"🤖 AI Function Call: {function_call}")
    
    # Function handler executes
    result = {
        "success": True,
        "message": "Resume 'My Professional Resume' created successfully",
        "data": {
            "resume_id": "789",
            "resume_name": "My Professional Resume",
            "template_id": "professional",
            "user_id": "123"
        }
    }
    print(f"🔧 Function Result: {result}")
    
    # EventEmitter sends event to frontend
    event_data = {
        "event_type": "resume_created",
        "data": {
            "resume_id": "789",
            "resume_name": "My Professional Resume",
            "template_id": "professional",
            "status": "draft"
        }
    }
    print(f"🎯 Event Emitted: {event_data}")
    
    # Frontend receives event and updates UI
    frontend_actions = [
        "1. WebSocket receives 'resume_created' event",
        "2. ChatUI.handleResumeCreated() called",
        "3. currentResumeId set to '789'",
        "4. Success message added to chat",
        "5. TemplatePreview.updateResumePreview('789') called",
        "6. TemplatePreview.switchTemplate('professional') called",
        "7. Resume preview shows new resume with professional template"
    ]
    
    print("\n📱 Frontend Actions:")
    for action in frontend_actions:
        print(f"   {action}")
    
    print("\n✅ Result: Resume created and preview updated automatically!")

# Example 3: User adds personal info
def example_add_personal_info():
    """
    Example: User provides personal information
    """
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Adding Personal Information via AI")
    print("=" * 60)
    
    # User message
    user_message = "My name is John Doe, I'm a Software Engineer, my email is john@example.com"
    print(f"👤 User: {user_message}")
    
    # AI processes and calls function
    function_call = {
        "name": "save_personal_info",
        "arguments": json.dumps({
            "user_id": "123",
            "resume_id": "789",
            "full_name": "John Doe",
            "title": "Software Engineer",
            "email": "john@example.com"
        })
    }
    print(f"🤖 AI Function Call: {function_call}")
    
    # Function handler executes
    result = {
        "success": True,
        "message": "Personal information saved successfully",
        "data": {
            "resume_id": "789",
            "user_id": "123"
        }
    }
    print(f"🔧 Function Result: {result}")
    
    # EventEmitter sends event to frontend
    event_data = {
        "event_type": "resume_updated",
        "data": {
            "resume_id": "789",
            "personal_info": {
                "full_name": "John Doe",
                "title": "Software Engineer",
                "email": "john@example.com"
            },
            "timestamp": "2024-01-15T10:31:00Z"
        }
    }
    print(f"🎯 Event Emitted: {event_data}")
    
    # Frontend receives event and updates UI
    frontend_actions = [
        "1. WebSocket receives 'resume_updated' event",
        "2. ChatUI.handleResumeUpdated() called",
        "3. TemplatePreview.updateResumePreview('789') called",
        "4. Resume preview updates with new personal info",
        "5. Success message added to chat",
        "6. User sees updated resume in real-time"
    ]
    
    print("\n📱 Frontend Actions:")
    for action in frontend_actions:
        print(f"   {action}")
    
    print("\n✅ Result: Personal info added and resume updated in real-time!")

# Example 4: Complex workflow
def example_complex_workflow():
    """
    Example: Complete resume creation workflow
    """
    print("\n" + "=" * 60)
    print("EXAMPLE 4: Complete Resume Creation Workflow")
    print("=" * 60)
    
    workflow_steps = [
        {
            "user_message": "I want to create a modern resume",
            "ai_action": "create_resume with modern template",
            "frontend_result": "Resume created, modern template loaded"
        },
        {
            "user_message": "My name is Sarah Johnson, I'm a Data Scientist",
            "ai_action": "save_personal_info",
            "frontend_result": "Personal info saved, resume preview updated"
        },
        {
            "user_message": "Switch to professional template",
            "ai_action": "switch_template to professional",
            "frontend_result": "Template switched, preview updated"
        },
        {
            "user_message": "Add my experience at TechCorp as Senior Data Scientist",
            "ai_action": "save_experience",
            "frontend_result": "Experience added, resume preview updated"
        },
        {
            "user_message": "Switch back to modern template",
            "ai_action": "switch_template to modern",
            "frontend_result": "Template switched, all data preserved"
        }
    ]
    
    print("🔄 Complete Workflow:")
    for i, step in enumerate(workflow_steps, 1):
        print(f"\n{i}. User: {step['user_message']}")
        print(f"   AI: {step['ai_action']}")
        print(f"   Result: {step['frontend_result']}")
    
    print("\n🎯 Key Benefits:")
    benefits = [
        "✅ No manual clicking required",
        "✅ Real-time UI updates",
        "✅ Seamless user experience",
        "✅ AI controls the interface",
        "✅ Consistent state management",
        "✅ Automatic error handling"
    ]
    
    for benefit in benefits:
        print(f"   {benefit}")

# Example 5: Error handling
def example_error_handling():
    """
    Example: How errors are handled in the event-driven system
    """
    print("\n" + "=" * 60)
    print("EXAMPLE 5: Error Handling in Event-Driven System")
    print("=" * 60)
    
    # Scenario: User tries to switch template but resume doesn't exist
    user_message = "Switch to creative template"
    print(f"👤 User: {user_message}")
    
    # AI calls function but gets error
    function_call = {
        "name": "switch_template",
        "arguments": json.dumps({
            "user_id": "123",
            "resume_id": "nonexistent",
            "template_id": "creative"
        })
    }
    print(f"🤖 AI Function Call: {function_call}")
    
    # Function handler returns error
    error_result = {
        "success": False,
        "error": "Resume with ID nonexistent not found for user 123"
    }
    print(f"❌ Function Error: {error_result}")
    
    # No event is emitted (EventEmitter handles errors gracefully)
    print("🎯 No event emitted due to error")
    
    # AI responds with error message
    ai_response = "I'm sorry, I couldn't find that resume. Let me help you create a new one first."
    print(f"🤖 AI Response: {ai_response}")
    
    # Frontend shows error in chat
    print("📱 Frontend: Error message displayed in chat")
    
    print("\n✅ Result: Error handled gracefully without breaking the UI")

if __name__ == "__main__":
    # Run all examples
    example_switch_template()
    example_create_resume()
    example_add_personal_info()
    example_complex_workflow()
    example_error_handling()
    
    print("\n" + "=" * 60)
    print("🎉 EVENT-DRIVEN APPROACH SUMMARY")
    print("=" * 60)
    
    summary = """
    The event-driven approach enables:
    
    1. 🎯 DIRECT BACKEND CONTROL: AI function handlers can trigger any frontend action
    2. 🔄 REAL-TIME UPDATES: UI updates instantly when data changes
    3. 🚀 SEAMLESS UX: No manual clicking required for template switching
    4. 📱 RESPONSIVE INTERFACE: Frontend reacts to backend events automatically
    5. 🛡️ ERROR HANDLING: Graceful error handling with user feedback
    6. 🔧 FLEXIBLE ARCHITECTURE: Easy to add new events and handlers
    
    This creates a truly conversational AI experience where the AI can
    control the interface naturally, just like a human assistant would!
    """
    
    print(summary) 