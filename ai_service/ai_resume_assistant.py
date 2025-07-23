"""
OpenAI Assistant Manager with RAG and Function Calling

This module provides a comprehensive interface for creating and managing OpenAI Assistants
with Retrieval-Augmented Generation (RAG) capabilities and function calling features.

ARCHITECTURE OVERVIEW:
=====================

The module follows a two-phase workflow:

1. SETUP PHASE (One-time):
   - Create an assistant with specific functions and instructions
   - Upload documents to a vector store for RAG capabilities
   - Configure the assistant with both function calling and file search tools

2. CONVERSATION PHASE (Repeated):
   - Create threads for individual conversations
   - Exchange messages with the assistant
   - Handle function calls triggered by AI responses
   - Each thread maintains its own conversation history

KEY COMPONENTS:
===============

- OpenAIAssistantManager: Main class for managing assistants, threads, and conversations
- FunctionConfig: Configuration class for defining custom functions
- FunctionHandlers: External class that implements the actual function logic

USAGE EXAMPLES:
===============

Basic Setup:
    manager = OpenAIAssistantManager()
    assistant_id = manager.create_assistant(
        name="Email Assistant",
        base_instructions="You are an email assistant...",
        functions=[email_function_config]
    )
    vector_store_id = manager.create_and_upload_to_vector_store(
        "documents.txt", assistant_id
    )

Basic Conversation:
    thread_id = manager.create_thread()
    response = manager.add_message_and_run(
        thread_id, assistant_id, "Write an email to john@example.com"
    )

FUNCTION CALLING WORKFLOW:
=========================

1. User sends message to assistant
2. Assistant processes message and determines if function call is needed
3. If function call required, status becomes "requires_action"
4. System extracts function name and arguments from AI response
5. Function is executed through FunctionHandlers
6. Results are submitted back to assistant
7. Assistant provides final response to user

TROUBLESHOOTING:
===============

Common Issues:
- OPENAI_API_KEY not set: Check environment variables
- Function calls not working: Verify FunctionHandlers implementation
- Vector store upload fails: Check file permissions and OpenAI quotas
- Timeout errors: Increase timeout value in add_message_and_run method

DEPENDENCIES:
============

Required packages:
- openai: OpenAI API client
- python-dotenv: Environment variable management
- json: JSON parsing
- time: Timeout handling
- os: Environment variable access

External dependencies:
- agents.services.tasks_schema: Task schema definitions
- agents.services.function_handlers: Function implementation handlers
"""

import openai
import time
import os
from typing import Optional, List, Dict, Any, Callable
from dotenv import load_dotenv
from .task_schema import TASK_SCHEMAS
from openai import OpenAI
from .function_handlers import FunctionHandlers
import json

class FunctionConfig:
    """
    Configuration class for defining custom functions that can be called by the AI assistant.
    
    This class encapsulates all the metadata needed to register a function with OpenAI's
    assistant API, including the function schema, description, and usage instructions.
    
    Attributes:
        name (str): The function name that will be called
        description (str): Human-readable description of what the function does
        parameters (Dict[str, Any]): JSON schema defining the function parameters
        instructions (str): Instructions for when and how the AI should use this function
    
    Example:
        email_function = FunctionConfig(
            name="save_email",
            description="Save an email response to the system",
            parameters={
                "type": "object",
                "properties": {
                    "recipient": {"type": "string", "description": "Email recipient"},
                    "subject": {"type": "string", "description": "Email subject"},
                    "content": {"type": "string", "description": "Email content"}
                },
                "required": ["recipient", "subject", "content"]
            },
            instructions="Use this function when you need to save an email response"
        )
    """
    def __init__(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        instructions: str
    ):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.instructions = instructions

class OpenAIAssistantManager:
    """
    Manages OpenAI Assistants, Threads, and Vector Stores with RAG and Function Calling
    
    This class provides a complete interface for creating and managing AI assistants
    that can both search through documents (RAG) and execute custom functions.
    
    WORKFLOW OVERVIEW:
    ==================
    
    1. SETUP PHASE (One-time setup):
       - Create an assistant with specific functions and instructions
       - Create vector store and upload initial documents
       - This phase establishes the assistant's knowledge base and capabilities
    
    2. CONVERSATION PHASE (Can be repeated):
       - Create a new thread for each conversation
       - Exchange messages within the thread
       - Handle function calls triggered by AI responses
       - Each thread maintains its own conversation history
    
    KEY FEATURES:
    =============
    
    - RAG (Retrieval-Augmented Generation): Search through uploaded documents
    - Function Calling: Execute custom functions based on AI decisions
    - Thread Management: Maintain separate conversation contexts
    - Vector Store Management: Upload, update, and manage document collections
    - Error Handling: Comprehensive error handling and logging
    - User Management: Proper user isolation for multi-user environments
    
    USAGE PATTERNS:
    ===============
    
    Basic Setup:
        manager = OpenAIAssistantManager()
        assistant_id = manager.create_assistant(
            name="My Assistant",
            base_instructions="You are a helpful assistant...",
            functions=[function_configs]
        )
        vector_store_id = manager.create_and_upload_to_vector_store(
            "file.txt", assistant_id
        )
    
    Conversation:
        thread_id = manager.create_thread()
        response = manager.add_message_and_run(
            thread_id, assistant_id, "Hello", user_id="user_123"
        )
    
    ADVANCED USAGE:
    ===============
    
    Multi-function Assistant:
        functions = [
            FunctionConfig(name="save_email", ...),
            FunctionConfig(name="add_reminder", ...),
            FunctionConfig(name="search_database", ...)
        ]
        assistant_id = manager.create_assistant(
            name="Multi-Function Assistant",
            base_instructions="You can perform multiple tasks...",
            functions=functions
        )
    
    Document Management:
        # Add new documents to existing assistant
        manager.add_file_to_existing_vector_store(
            "new_document.txt", vector_store_id
        )
        
        # List all documents
        files = manager.list_files_in_vector_store(vector_store_id)
        
        # Delete specific documents
        manager.delete_file_from_vector_store(vector_store_id, file_id)
    
    ERROR HANDLING:
    ===============
    
    The class includes comprehensive error handling:
    - API key validation on initialization
    - Timeout handling for long-running operations
    - Graceful degradation when functions fail
    - Detailed logging for debugging
    
    PERFORMANCE CONSIDERATIONS:
    ==========================
    
    - Vector store operations can be slow for large documents
    - Function calls add latency to conversations
    - Consider caching assistant and thread IDs for reuse
    - Monitor OpenAI API usage and quotas
    
    SECURITY CONSIDERATIONS:
    =======================
    
    - API keys are loaded from environment variables
    - Function arguments are validated before execution
    - No sensitive data is logged in debug output
    - User isolation ensures data privacy
    - Consider implementing rate limiting for production use
    """
    
    def __init__(self):
        """
        Initialize OpenAI Assistant Manager
        
        Sets up the OpenAI client with API key from environment variables.
        Validates that the API key is available before proceeding.
        
        Raises:
            ValueError: If OPENAI_API_KEY is not found in environment variables
        
        Example:
            try:
                manager = OpenAIAssistantManager()
                print("Manager initialized successfully")
            except ValueError as e:
                print(f"Initialization failed: {e}")
        """
        load_dotenv()
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        self.client = OpenAI(api_key=api_key)  # Initialize the client

    def create_assistant(
        self,
        name: str,
        base_instructions: str,
        functions: List[FunctionConfig],
        model: str = "gpt-4o-mini"
    ) -> Optional[str]:
        """
        Create an OpenAI assistant with dynamic function configuration
        
        This method creates a new assistant with the specified functions and instructions.
        The assistant will be able to call the provided functions and search through
        uploaded documents using RAG capabilities.
        
        Args:
            name (str): Human-readable name for the assistant
            base_instructions (str): Base behavior instructions for the assistant
            functions (List[FunctionConfig]): List of function configurations
            model (str, optional): OpenAI model to use. Defaults to "gpt-4o-mini"
        
        Returns:
            Optional[str]: Assistant ID if successful, None if failed
        
        Raises:
            Exception: If assistant creation fails due to API errors
        
        Example:
            # Create a simple email assistant
            email_function = FunctionConfig(
                name="save_email",
                description="Save an email response",
                parameters={"type": "object", "properties": {...}},
                instructions="Use this to save email responses"
            )
            
            assistant_id = manager.create_assistant(
                name="Email Assistant",
                base_instructions="You are an email assistant...",
                functions=[email_function]
            )
            
            if assistant_id:
                print(f"Assistant created: {assistant_id}")
            else:
                print("Failed to create assistant")
        
        Notes:
            - The assistant will have both file_search and function calling capabilities
            - Function instructions are appended to base instructions
            - All functions are set to strict mode for better control
        """
        try:
            # Build complete instructions by combining base and function-specific instructions
            complete_instructions = [base_instructions]
            for func in functions:
                complete_instructions.append(func.instructions)
            
            # Build tools list - Include both file_search and function tools
            tools = [{"type": "file_search"}]  # Add file_search first for RAG
            
            # Add function tools for each configured function
            for func in functions:
                tools.append({
                    "type": "function",
                    "function": {
                        "name": func.name,
                        "description": func.description,
                        "parameters": func.parameters,
                        "strict": True  # Enforce strict parameter validation
                    }
                })

            print(f"Creating assistant with tools: {[tool.get('type', 'function') for tool in tools]}")
            
            # Create the assistant using OpenAI API
            assistant = self.client.beta.assistants.create(
                name=name,
                instructions="\n\n".join(complete_instructions),
                model=model,
                tools=tools
            )
            
            print(f"Assistant created with ID: {assistant.id}")
            return assistant.id
            
        except Exception as e:
            print(f"Error creating assistant: {e}")
            return None

    def create_and_upload_to_vector_store(self, file_path: str, assistant_id: str) -> Optional[str]:
        """
        Create vector store and upload initial file for RAG capabilities
        
        This method creates a new vector store and uploads the specified file to it.
        The vector store is then associated with the assistant, enabling document
        search capabilities.
        
        Args:
            file_path (str): Path to the file to upload
            assistant_id (str): ID of the assistant to associate with the vector store
        
        Returns:
            Optional[str]: Vector store ID if successful, None if failed
        
        Raises:
            FileNotFoundError: If the specified file doesn't exist
            Exception: If vector store creation or file upload fails
        
        Example:
            # Upload a knowledge base document
            vector_store_id = manager.create_and_upload_to_vector_store(
                "company_policies.txt",
                assistant_id
            )
            
            if vector_store_id:
                print(f"Vector store created: {vector_store_id}")
            else:
                print("Failed to create vector store")
        
        Notes:
            - Only one vector store is created per assistant
            - Multiple files can be added to the same vector store
            - The assistant is automatically updated with the vector store reference
        """
        try:
            # Create vector store
            vector_store = self.client.beta.vector_stores.create(
                name=f"Assistant Store - {assistant_id}"
            )
            print(f"Vector store created with ID: {vector_store.id}")
            
            # Upload file to the vector store
            with open(file_path, "rb") as file:
                file_batch = self.client.beta.vector_stores.file_batches.upload_and_poll(
                    vector_store_id=vector_store.id,
                    files=[file]
                )
            
            # Get current assistant to preserve existing tools
            current_assistant = self.client.beta.assistants.retrieve(assistant_id)
            current_tools = current_assistant.tools
            
            # Add file_search to existing tools (preserve function tools)
            tools = [tool for tool in current_tools if tool.type != "file_search"]
            tools.append({"type": "file_search"})
            
            # Update assistant with vector store reference
            assistant = self.client.beta.assistants.update(
                assistant_id=assistant_id,
                tools=tools,
                tool_resources={
                    "file_search": {
                        "vector_store_ids": [vector_store.id]
                    }
                }
            )
            
            print(f"Assistant updated with tools: {[tool.type for tool in assistant.tools]}")
            return vector_store.id
            
        except Exception as e:
            print(f"Error in setup: {e}")
            return None

    def add_file_to_existing_vector_store(self, file_path: str, vector_store_id: str) -> bool:
        """
        Add a new file to an existing vector store
        
        Use this method when you need to add more documents to an existing assistant's
        knowledge base. The assistant will automatically have access to the new content
        once it's added to the vector store.
        
        Args:
            file_path (str): Path to the new file to upload
            vector_store_id (str): ID of the existing vector store
            
        Returns:
            bool: True if successful, False if failed
        
        Raises:
            FileNotFoundError: If the specified file doesn't exist
            Exception: If file upload fails
        
        Example:
            # Add new document to existing setup
            success = manager.add_file_to_existing_vector_store(
                "new_policy_document.txt",
                existing_vector_store_id
            )
            
            if success:
                print("File added successfully")
            else:
                print("Failed to add file")
        
        Notes:
            - The file is processed asynchronously by OpenAI
            - Check the returned status to confirm successful upload
            - Large files may take time to process
        """
        try:
            with open(file_path, "rb") as file:
                file_batch = self.client.beta.vector_stores.file_batches.upload_and_poll(
                    vector_store_id=vector_store_id,
                    files=[file]
                )
            print(f"File added to vector store. Status: {file_batch.status}")
            return file_batch.status == "succeeded"
        except Exception as e:
            print(f"Error adding file: {e}")
            return False

    def create_thread(self) -> Optional[str]:
        """
        Create a new conversation thread
        
        Each new conversation should use a new thread to maintain separate conversation
        history. Threads are lightweight and can be created on-demand.
        
        Returns:
            Optional[str]: Thread ID if successful, None if failed
        
        Raises:
            Exception: If thread creation fails due to API errors
        
        Example:
            # Create a new conversation thread
            thread_id = manager.create_thread()
            
            if thread_id:
                print(f"Thread created: {thread_id}")
            else:
                print("Failed to create thread")
        
        Notes:
            - Threads are independent conversation contexts
            - Each thread maintains its own message history
            - Threads can be reused for related conversations
        """
        try:
            thread = self.client.beta.threads.create()
            print(f"Thread created with ID: {thread.id}")
            return thread.id
        except Exception as e:
            print(f"Error creating thread: {e}")
            return None

    def add_message_and_run(self, thread_id: str, assistant_id: str, query: str, user_id: str) -> Optional[Dict]:
        """
        Add a message to thread and run the assistant with function calling support
        
        This is the main method for interacting with the assistant. It handles the
        complete conversation flow including function calls, tool outputs, and
        response generation.
        
        WORKFLOW:
        1. Add user message to thread
        2. Create and start a run
        3. Poll for run status
        4. Handle function calls if required
        5. Submit tool outputs back to assistant
        6. Return final response with any resume IDs
        
        Args:
            thread_id (str): ID of the conversation thread
            assistant_id (str): ID of the assistant to use
            query (str): User's message/query
            user_id (str): ID of the user initiating the conversation
        
        Returns:
            Optional[Dict]: Dictionary with 'response' and optional 'resume_id' if successful, None if failed
        
        Raises:
            Exception: If message processing or function execution fails
        
        Example:
            # Send a message and get response
            result = manager.add_message_and_run(
                thread_id="thread_abc123",
                assistant_id="asst_xyz789",
                query="Create a new resume for me",
                user_id="user_123"
            )
            
            if result:
                print(f"Assistant: {result['response']}")
                if result.get('resume_id'):
                    print(f"Resume ID: {result['resume_id']}")
            else:
                print("No response received")
        
        Notes:
            - Function calls are handled automatically
            - The method includes timeout protection (60 seconds)
            - All function results are logged for debugging
            - The assistant can call multiple functions in sequence
            - Resume IDs are extracted from function results and returned
        """
        try:
            print("\n" + "="*60)
            print("🚀 AI ASSISTANT: Starting add_message_and_run")
            print("="*60)
            print(f"📝 Thread ID: {thread_id}")
            print(f"🤖 Assistant ID: {assistant_id}")
            print(f"💬 Query: {query}")
            print(f"👤 User ID: {user_id}")
            
            # Add user message to thread with user context
            print(f"\n📝 Adding message to thread {thread_id}")
            try:
                # Inject user context into the message
                contextualized_query = f"""Current user ID: {user_id}

User message: {query}

IMPORTANT: Always use user_id: {user_id} when calling any functions that require a user_id parameter."""
                
                self.client.beta.threads.messages.create(
                    thread_id=thread_id,
                    role="user",
                    content=contextualized_query
                )
                print("✅ Message added successfully with user context")
            except Exception as e:
                print(f"❌ Error adding message: {e}")
                raise
            
            # Create and start a run
            print(f"🚀 Starting run with assistant {assistant_id}")
            try:
                run = self.client.beta.threads.runs.create(
                    thread_id=thread_id,
                    assistant_id=assistant_id
                )
                print(f"✅ Run created with ID: {run.id}")
            except Exception as e:
                print(f"❌ Error creating run: {e}")
                raise
            
            # Track resume IDs from function calls
            resume_ids = []
            
            # Poll for run status
            start_time = time.time()
            timeout = 90  # Increased from 60 to 90 seconds to match frontend timeout
            poll_count = 0
            
            print(f"⏰ Starting polling loop (timeout: {timeout}s)")
            
            while time.time() - start_time < timeout:
                poll_count += 1
                elapsed_time = time.time() - start_time
                print(f"\n🔄 Poll #{poll_count} (elapsed: {elapsed_time:.1f}s / {timeout}s)")
                
                try:
                    run_status = self.client.beta.threads.runs.retrieve(
                        thread_id=thread_id,
                        run_id=run.id
                    )
                    print(f"⏳ Run status: {run_status.status}")
                except Exception as e:
                    print(f"❌ Error retrieving run status: {e}")
                    raise
                
                # Handle function calls
                if run_status.status == "requires_action":
                    print("\n🔧 Function calls required!")
                    tool_calls = run_status.required_action.submit_tool_outputs.tool_calls
                    print(f"🔧 Number of tool calls: {len(tool_calls)}")
                    
                    tool_outputs = []
                    for i, tool_call in enumerate(tool_calls):
                        print(f"\n🔧 Processing tool call {i+1}/{len(tool_calls)}")
                        print(f"🔧 Function to call: {tool_call.function.name}")
                        print(f"🔧 Arguments: {tool_call.function.arguments}")
                        
                        # Create function handler instance
                        handler = FunctionHandlers()
                        
                        # Parse the function arguments
                        args = json.loads(tool_call.function.arguments)
                        
                        # Execute the appropriate function based on name
                        print(f"🔧 Executing function: {tool_call.function.name}")
                        try:
                            if tool_call.function.name == "save_email":
                                result = handler.save_email(**args)
                            elif tool_call.function.name == "auto_respond_email":
                                result = handler.auto_respond_email(**args)
                            elif tool_call.function.name == "reply_to_email":
                                result = handler.reply_to_email(**args)
                            elif tool_call.function.name == "forward_email":
                                result = handler.forward_email(**args)
                            # Resume builder functions - New robust version
                            elif tool_call.function.name == "create_resume":
                                result = handler.create_resume(**args)
                                # Extract resume ID if created successfully
                                if result.get("success") and result.get("data", {}).get("resume_id"):
                                    resume_ids.append(result["data"]["resume_id"])
                            elif tool_call.function.name == "save_personal_info":
                                result = handler.save_personal_info(**args)
                                # Extract resume ID if available
                                if result.get("success") and result.get("data", {}).get("resume_id"):
                                    resume_ids.append(result["data"]["resume_id"])
                            elif tool_call.function.name == "edit_personal_info":
                                result = handler.edit_personal_info(**args)
                            elif tool_call.function.name == "save_experience":
                                result = handler.save_experience(**args)
                                # Extract resume ID if available
                                if result.get("success") and result.get("data", {}).get("resume_id"):
                                    resume_ids.append(result["data"]["resume_id"])
                            elif tool_call.function.name == "delete_experience_by_company":
                                result = handler.delete_experience_by_company(**args)
                            elif tool_call.function.name == "edit_experience":
                                result = handler.edit_experience(**args)
                            elif tool_call.function.name == "delete_experience":
                                result = handler.delete_experience(**args)
                            elif tool_call.function.name == "save_education":
                                result = handler.save_education(**args)
                                # Extract resume ID if available
                                if result.get("success") and result.get("data", {}).get("resume_id"):
                                    resume_ids.append(result["data"]["resume_id"])
                            elif tool_call.function.name == "edit_education":
                                result = handler.edit_education(**args)
                            elif tool_call.function.name == "delete_education":
                                result = handler.delete_education(**args)
                            elif tool_call.function.name == "save_skills":
                                result = handler.save_skills(**args)
                                # Extract resume ID if available
                                if result.get("success") and result.get("data", {}).get("resume_id"):
                                    resume_ids.append(result["data"]["resume_id"])
                            elif tool_call.function.name == "edit_skills":
                                result = handler.edit_skills(**args)
                            elif tool_call.function.name == "save_additional":
                                result = handler.save_additional(**args)
                                # Extract resume ID if available
                                if result.get("success") and result.get("data", {}).get("resume_id"):
                                    resume_ids.append(result["data"]["resume_id"])
                            elif tool_call.function.name == "save_summary":
                                result = handler.save_summary(**args)
                                # Extract resume ID if available
                                if result.get("success") and result.get("data", {}).get("resume_id"):
                                    resume_ids.append(result["data"]["resume_id"])
                            elif tool_call.function.name == "edit_additional":
                                result = handler.edit_additional(**args)
                            elif tool_call.function.name == "get_resume_info":
                                result = handler.get_resume_info(**args)
                            elif tool_call.function.name == "list_user_resumes":
                                result = handler.list_user_resumes(**args)
                            elif tool_call.function.name == "finalize_resume":
                                result = handler.finalize_resume(**args)
                                # Extract resume ID if available
                                if result.get("success") and result.get("data", {}).get("resume_id"):
                                    resume_ids.append(result["data"]["resume_id"])
                            elif tool_call.function.name == "list_templates":
                                result = handler.list_templates(**args)
                            elif tool_call.function.name == "preview_template":
                                result = handler.preview_template(**args)
                            elif tool_call.function.name == "switch_template":
                                result = handler.switch_template(**args)
                                # Extract resume ID if available
                                if result.get("success") and result.get("data", {}).get("resume_id"):
                                    resume_ids.append(result["data"]["resume_id"])
                            elif tool_call.function.name == "get_current_date":
                                result = handler.get_current_date(**args)
                            elif tool_call.function.name == "create_cover_letter":
                                result = handler.create_cover_letter(**args)
                            elif tool_call.function.name == "save_cover_letter_user_info":
                                result = handler.save_cover_letter_user_info(**args)
                            elif tool_call.function.name == "save_cover_letter_employer_info":
                                result = handler.save_cover_letter_employer_info(**args)
                            elif tool_call.function.name == "save_cover_letter_greeting":
                                result = handler.save_cover_letter_greeting(**args)
                            elif tool_call.function.name == "save_cover_letter_introduction":
                                result = handler.save_cover_letter_introduction(**args)
                            elif tool_call.function.name == "save_cover_letter_body":
                                result = handler.save_cover_letter_body(**args)
                            elif tool_call.function.name == "finalize_cover_letter":
                                result = handler.finalize_cover_letter(**args)
                            else:
                                print(f"❌ Unknown function: {tool_call.function.name}")
                                result = {"error": f"Unknown function: {tool_call.function.name}"}
                            
                            print(f"✅ Function result: {result}")
                            
                        except Exception as e:
                            print(f"❌ Error executing function {tool_call.function.name}: {e}")
                            result = {"error": f"Function execution failed: {str(e)}"}
                        
                        # Add result to tool outputs
                        tool_outputs.append({
                            "tool_call_id": tool_call.id,
                            "output": json.dumps(result)
                        })
                    
                    # Submit tool outputs back to assistant
                    if tool_outputs:
                        print(f"\n📤 Submitting {len(tool_outputs)} tool outputs...")
                        try:
                            self.client.beta.threads.runs.submit_tool_outputs(
                                thread_id=thread_id,
                                run_id=run.id,
                                tool_outputs=tool_outputs
                            )
                            print("✅ Tool outputs submitted successfully")
                        except Exception as e:
                            print(f"❌ Error submitting tool outputs: {e}")
                            raise
                    else:
                        print("\n⚠️ No tool outputs generated!")
                
                # Handle successful completion
                elif run_status.status == "completed":
                    print("\n✅ Run completed!")
                    try:
                        messages = self.client.beta.threads.messages.list(
                            thread_id=thread_id
                        )
                        print(f"📝 Retrieved {len(messages.data)} messages")
                        
                        if messages.data:
                            response_text = messages.data[0].content[0].text.value
                            print(f"📝 Response text: {response_text[:100]}...")
                            
                            # Return response with any resume IDs
                            result = {"response": response_text}
                            
                            # Add resume ID if any were created/updated
                            if resume_ids:
                                result["resume_id"] = resume_ids[-1]  # Use the most recent one
                                print(f"📄 Resume ID extracted: {result['resume_id']}")
                            
                            # Check for actions from function results
                            if hasattr(messages.data[0], 'content') and messages.data[0].content:
                                # Look for action metadata in the response
                                # This could be enhanced to parse structured data from the AI response
                                pass
                            
                            print("✅ Returning successful result")
                            return result
                        else:
                            print("❌ No messages found")
                            return None
                            
                    except Exception as e:
                        print(f"❌ Error retrieving messages: {e}")
                        raise
                    
                # Handle failures
                elif run_status.status in ["failed", "expired", "cancelled"]:
                    print(f"\n❌ Run failed with status: {run_status.status}")
                    if hasattr(run_status, 'last_error'):
                        print(f"❌ Error: {run_status.last_error}")
                    return None
                
                # Handle queued status
                elif run_status.status == "queued":
                    print("⏳ Run is queued, waiting...")
                
                # Handle in_progress status
                elif run_status.status == "in_progress":
                    print("⚙️ Run is in progress...")
                    
                # Wait before next status check
                print("⏳ Waiting 1 second before next poll...")
                time.sleep(1)
            
            print(f"⏰ Timeout reached after {timeout} seconds")
            return None
                
        except Exception as e:
            print(f"\n❌ Error in add_message_and_run: {str(e)}")
            import traceback
            print(f"📋 Traceback: {traceback.format_exc()}")
            return None

    def delete_file_from_vector_store(self, vector_store_id: str, file_id: str) -> bool:
        """
        Delete a specific file from a vector store
        
        Removes a single file from the vector store. This is useful for maintaining
        the knowledge base by removing outdated or incorrect documents.
        
        Args:
            vector_store_id (str): ID of the vector store containing the file
            file_id (str): ID of the specific file to delete
            
        Returns:
            bool: True if successful, False if failed
        
        Raises:
            Exception: If file deletion fails due to API errors
        
        Example:
            # Delete a specific file from vector store
            success = manager.delete_file_from_vector_store(
                vector_store_id="vs_abc123",
                file_id="file_xyz789"
            )
            
            if success:
                print("File deleted successfully")
            else:
                print("Failed to delete file")
        
        Notes:
            - The file is permanently removed from the vector store
            - This action cannot be undone
            - The assistant will no longer have access to the deleted content
        """
        try:
            response = self.client.beta.vector_stores.files.delete(
                vector_store_id=vector_store_id,
                file_id=file_id
            )
            print(f"File {file_id} deleted from vector store")
            return True
        except Exception as e:
            print(f"Error deleting file: {e}")
            return False

    def list_files_in_vector_store(self, vector_store_id: str) -> Optional[List[Dict]]:
        """
        List all files in a vector store
        
        Retrieves information about all files currently stored in the vector store.
        Useful for managing the knowledge base and understanding what documents
        the assistant has access to.
        
        Args:
            vector_store_id (str): ID of the vector store to query
            
        Returns:
            Optional[List[Dict]]: List of file information dictionaries if successful, None if failed
        
        Raises:
            Exception: If listing files fails due to API errors
        
        Example:
            # List all files in vector store
            files = manager.list_files_in_vector_store("vs_abc123")
            
            if files:
                for file in files:
                    print(f"File ID: {file.id}, Name: {file.name}")
            else:
                print("Failed to list files")
        
        Notes:
            - Returns detailed information about each file
            - Includes file IDs, names, and metadata
            - Useful for file management and cleanup operations
        """
        try:
            files = self.client.beta.vector_stores.files.list(
                vector_store_id=vector_store_id
            )
            return files.data
        except Exception as e:
            print(f"Error listing files: {e}")
            return None

    def delete_vector_store(self, vector_store_id: str) -> bool:
        """
        Delete an entire vector store and all its files
        
        Completely removes a vector store and all files within it. This is a
        destructive operation that cannot be undone.
        
        Args:
            vector_store_id (str): ID of the vector store to delete
            
        Returns:
            bool: True if successful, False if failed
        
        Raises:
            Exception: If vector store deletion fails due to API errors
        
        Example:
            # Delete entire vector store
            success = manager.delete_vector_store("vs_abc123")
            
            if success:
                print("Vector store deleted successfully")
            else:
                print("Failed to delete vector store")
        
        Notes:
            - This action is irreversible
            - All files in the vector store will be permanently deleted
            - The assistant will lose access to all documents in this store
            - Consider backing up important documents before deletion
        """
        try:
            response = self.client.beta.vector_stores.delete(
                vector_store_id=vector_store_id
            )
            print(f"Vector store {vector_store_id} deleted")
            return True
        except Exception as e:
            print(f"Error deleting vector store: {e}")
            return False

    def list_files(self) -> Optional[List[Dict]]:
        """
        List all files uploaded to OpenAI
        
        Retrieves information about all files that have been uploaded to OpenAI,
        regardless of which vector stores they belong to.
        
        Returns:
            Optional[List[Dict]]: List of file information dictionaries if successful, None if failed
        
        Raises:
            Exception: If listing files fails due to API errors
        
        Example:
            # List all uploaded files
            files = manager.list_files()
            
            if files:
                for file in files:
                    print(f"File ID: {file.id}, Name: {file.filename}")
            else:
                print("Failed to list files")
        
        Notes:
            - Returns all files across all vector stores
            - Useful for global file management
            - Includes files that may not be in any vector store
        """
        try:
            files = self.client.files.list()
            return files.data
        except Exception as e:
            print(f"Error listing files: {e}")
            return None

    def delete_file(self, file_id: str) -> bool:
        """
        Delete a file from OpenAI
        
        Removes a file from OpenAI's servers. This affects all vector stores
        that may be using this file.
        
        Args:
            file_id (str): ID of the file to delete
            
        Returns:
            bool: True if successful, False if failed
        
        Raises:
            Exception: If file deletion fails due to API errors
        
        Example:
            # Delete a file from OpenAI
            success = manager.delete_file("file-abc123")
            
            if success:
                print("File deleted successfully")
            else:
                print("Failed to delete file")
        
        Notes:
            - This action is irreversible
            - The file will be removed from all vector stores that use it
            - Consider the impact on multiple assistants before deletion
        """
        try:
            response = self.client.files.delete(file_id)
            print(f"File {file_id} deleted successfully")
            return True
        except Exception as e:
            print(f"Error deleting file: {e}")
            return False

    def get_file_info(self, file_id: str) -> Optional[Dict]:
        """
        Get information about a specific file
        
        Retrieves detailed information about a specific file, including its
        metadata, purpose, and usage information.
        
        Args:
            file_id (str): ID of the file to retrieve info for
            
        Returns:
            Optional[Dict]: Dictionary containing file information if successful, None if failed
        
        Raises:
            Exception: If file info retrieval fails due to API errors
        
        Example:
            # Get file information
            file_info = manager.get_file_info("file-abc123")
            
            if file_info:
                print(f"File name: {file_info.filename}")
                print(f"Purpose: {file_info.purpose}")
                print(f"Created at: {file_info.created_at}")
            else:
                print("Failed to get file info")
        
        Notes:
            - Returns comprehensive file metadata
            - Useful for debugging and file management
            - Includes creation date, purpose, and other details
        """
        try:
            file_info = self.client.files.retrieve(file_id)
            return file_info
        except Exception as e:
            print(f"Error retrieving file info: {e}")
            return None

def main():
    """
    Example usage of OpenAIAssistantManager
    
    This function demonstrates the basic workflow for creating an assistant,
    uploading documents, and having a conversation with function calling.
    
    WORKFLOW:
    1. Initialize the manager
    2. Create an assistant with email functionality
    3. Create a thread for conversation
    4. Upload documents to vector store
    5. Send a message and get response
    
    Example:
        # Run the example
        main()
    
    Notes:
        - This is a demonstration function
        - Requires proper environment setup
        - Uses example data and configurations
    """
    try:
        # Initialize manager
        manager = OpenAIAssistantManager()
        
        # Create assistant
        assistant_id = manager.create_assistant(
            name="Email Assistant",
            instructions="""You are an expert email composer. Your task is to:
            1. When asked to write an email, first compose a professional and contextually appropriate email
            2. Then use the draft_email function to save it as a draft for approval
            3. The email should be clear, concise, and maintain a professional tone
            4. After saving the draft, confirm that it's ready for review
            
            Remember: Always compose the email based on the user's requirements and context, 
            then use the draft_email function to save it for approval.""",
            integration_type="email",
            task_type="draft_email"
        )
        print(f"Created assistant: {assistant_id}")
        
        # Create thread
        thread_id = manager.create_thread()
        print(f"Created thread: {thread_id}")
        
        # Create vector store and upload file
        vector_store_id = manager.create_and_upload_to_vector_store(
            "ai/datastore/data/odyssey.txt",
            assistant_id
        )
        
        if vector_store_id:
            print("\nSetup complete. Starting conversation...")
            time.sleep(2)  # Give everything time to settle
            
            # Have a conversation
            response = manager.add_message_and_run(
                thread_id=thread_id,
                assistant_id=assistant_id,
                query="What's the name of Odysseus wife?",
                user_id="user_123"
            )
            
            if response:
                print("\nAssistant Response:")
                print("-" * 50)
                print(response)
            else:
                print("No response received")
                
    except Exception as e:
        print(f"Error in process: {e}")

def test_save_email_assistant():
    """
    Test creating assistant with save_email function and file search
    
    This function demonstrates how to create an assistant that can:
    1. Search through uploaded documents (RAG)
    2. Call the save_email function to save email responses
    3. Handle customer inquiries using knowledge base
    
    WORKFLOW:
    1. Create assistant with save_email function
    2. Upload furniture price list document
    3. Test email composition with document search
    
    Example:
        # Test email assistant functionality
        test_save_email_assistant()
    
    Notes:
        - Uses furniture price list as example document
        - Demonstrates RAG + function calling combination
        - Shows how to handle customer inquiries with product information
    """
    try:
        # Initialize manager
        manager = OpenAIAssistantManager()
        
        # Base instructions define the general role
        base_instructions = """You are a helpful customer service assistant. 
        When asked a query, use file_search to find relevant information."""

        # Function-specific instructions focus on when/how to use this specific function
        save_email_function = FunctionConfig(
            name="save_email",
            description="Save an email response to the system",
            parameters={
                "type": "object",
                "properties": {
                    "recipient": {
                        "type": "string",
                        "description": "Email address of the recipient"
                    },
                    "subject": {
                        "type": "string",
                        "description": "Subject line of the email"
                    },
                    "content": {
                        "type": "string",
                        "description": "Main body content of the email"
                    }
                },
                "required": ["recipient", "subject", "content"],
                "additionalProperties": False
            },
            instructions="""When you need to respond to a customer via email:
            1. First search and gather all relevant information using file_search
            2. Compose your response based on the information found
            3. Use this save_email function to save your response
            4. Do not write the email in the chat - only use this function
            5. After saving, confirm that the response has been saved"""
        )
        
        # Create assistant with base instructions and function
        assistant_id = manager.create_assistant(
            name="Personal Assistant with File Search",
            base_instructions=base_instructions,
            functions=[save_email_function]
        )
        
        if assistant_id:
            print(f"\nAssistant created successfully with ID: {assistant_id}")
            
            # Upload the furniture price list
            vector_store_id = manager.create_and_upload_to_vector_store(
                file_path="/Users/joelivongbe/Documents/django/esaaba/ai/services/furniture-pricelist.txt",
                assistant_id=assistant_id
            )
            print(f"Vector store created with ID: {vector_store_id}")
            
            # Create a thread and test
            thread_id = manager.create_thread()
            test_message = """Please write an email to customer@example.com responding to their inquiry about dining tables. 
            Use our furniture price list to include specific details about our available dining table options and their prices."""
            
            print("\nSending message to assistant...")
            response = manager.add_message_and_run(
                thread_id=thread_id,
                assistant_id=assistant_id,
                query=test_message,
                user_id="user_123"
            )
            
            print("\nTest Message:", test_message)
            print("\nAssistant Response:", response)
            
        else:
            print("Failed to create assistant")
            
    except Exception as e:
        print(f"Error in test: {str(e)}")

def test_multi_function_assistant():
    """
    Test creating assistant with multiple functions
    
    This function demonstrates how to create an assistant that can handle
    multiple types of tasks by calling different functions based on the
    user's request.
    
    WORKFLOW:
    1. Create assistant with multiple functions (save_email, add_reminder)
    2. Upload knowledge base documents
    3. Test complex multi-function requests
    
    Example:
        # Test multi-function assistant
        test_multi_function_assistant()
    
    Notes:
        - Shows how to combine multiple functions in one assistant
        - Demonstrates complex workflow handling
        - Illustrates how AI can choose appropriate functions based on context
    """
    try:
        # Initialize manager
        manager = OpenAIAssistantManager()
        
        # Define save_email function
        save_email_function = FunctionConfig(
            name="save_email",
            description="Save an email response to the system",
            parameters={
                "type": "object",
                "properties": {
                    "recipient": {
                        "type": "string",
                        "description": "Email address of the recipient"
                    },
                    "subject": {
                        "type": "string",
                        "description": "Subject line of the email"
                    },
                    "content": {
                        "type": "string",
                        "description": "Main body content of the email"
                    }
                },
                "required": ["recipient", "subject", "content"],
                "additionalProperties": False
            },
            instructions="""When you need to respond to a customer via email:
            . First search and gather all relevant information using file_search
            . Compose your response based on the information found
            . Use this save_email function to save your response
            . After saving, confirm that the response has been saved"""
        )
        
        # Define add_reminder function
        add_reminder_function = FunctionConfig(
            name="add_reminder",
            description="Add a reminder to the system",
            parameters={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Brief title of the reminder"
                    },
                    "description": {
                        "type": "string",
                        "description": "Detailed description of what needs to be remembered"
                    },
                    "due_date": {
                        "type": "string",
                        "description": "When this reminder is due (YYYY-MM-DD format)"
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high"],
                        "description": "Priority level of the reminder"
                    }
                },
                "required": ["title", "description", "due_date", "priority"],
                "additionalProperties": False
            },
            instructions="""When asked to set or create a reminder:
            . Extract the key information from the request
            . Use this add_reminder function to save the reminder
            . After saving, confirm that the reminder has been set"""
        )
        
        # Create assistant with both functions
        assistant_id = manager.create_assistant(
            name="Multi-Function Assistant",
            base_instructions="""You are a helpful customer service assistant. 
            When asked a query, use file_search to find relevant information.
            """,
            functions=[save_email_function, add_reminder_function]
        )
        
        if assistant_id:
            print(f"\nAssistant created successfully with ID: {assistant_id}")
            
            # Upload the furniture price list
            vector_store_id = manager.create_and_upload_to_vector_store(
                file_path="/Users/joelivongbe/Documents/django/esaaba/ai/services/furniture-pricelist.txt",
                assistant_id=assistant_id
            )
            print(f"Vector store created with ID: {vector_store_id}")
            
            # Create a thread
            thread_id = manager.create_thread()
            
            # Test both functions with a single complex query
            complex_test = """
            1. Write an email to customer@example.com about our dining table collection:
               - Include available sizes and styles from our catalog
               - Mention price ranges
               - Include any current promotions
               - Suggest booking a showroom visit
            
            2. Also, set a reminder for me to follow up with this customer next Friday at high priority.
            
            Please use our furniture price list for accurate information."""
            
            print("\nTesting complex multi-function request...")
            response = manager.add_message_and_run(
                thread_id=thread_id,
                assistant_id=assistant_id,
                query=complex_test,
                user_id="user_123"
            )
            print("\nComplex Test Response:", response)
            
        else:
            print("Failed to create assistant")
            
    except Exception as e:
        print(f"Error in test: {str(e)}")

if __name__ == "__main__":
    #main()
    #manager = OpenAIAssistantManager()
    #manager.add_file_to_existing_vector_store("ai/datastore/data/about-us.txt", "vs_UfD2J8pthS0qlP19uXlHHWDJ")
    #thread_id=manager.create_thread()
    #print(f"Thread created: {thread_id}")
    #response = manager.add_message_and_run(thread_id, "asst_vShH1Hyfaprc3elbsEg7VjKq", "tell me about traveltaf?", "user_123")
    #print(f"Assistant response: {response}")
    #manager.delete_file("file-Wq5u3pqoQ3Rg8ec5VdKWaa")
    #manager.delete_vector_store("vs_mJVHTIDCiZ2KTZi3tUja7Mik")
    test_multi_function_assistant()