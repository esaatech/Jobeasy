# 🔄 Complete AI Resume Assistant Flow

## 📊 **Complete Flow: User Input → Template Switching**

### **1. 🚀 User Interaction (Frontend)**
```
User types: "Can I view the modern template?"
↓
ChatUI.sendMessage() called
↓
ChatUI.sendWebSocketMessage() sends via WebSocket
```

### **2. 🌐 WebSocket Connection**
```
Frontend WebSocket → Django Channels → ResumeBuilderConsumer
↓
WebSocket URL: ws://localhost:8000/ws/resume-builder/
↓
Consumer receives message in ResumeBuilderConsumer.receive()
```

### **3. 🎯 Django View Processing**
```
ResumeBuilderConsumer.receive()
↓
Calls ResumeBuilderConsumer.process_with_real_ai()
↓
Imports and calls resume_builder.views.get_or_create_assistant()
↓
Gets or creates OpenAI Assistant with all functions
↓
Calls manager.add_message_and_run() with user context
```

### **4. 🤖 AI Assistant Processing**
```
OpenAIAssistantManager.add_message_and_run()
↓
Injects user context: "Current user ID: {user_id}"
↓
Sends contextualized message to OpenAI Assistant
↓
OpenAI Assistant analyzes message and decides to call function
↓
Calls preview_template function with user_id and template_id
```

### **5. 🔧 Function Handler Execution**
```
AI calls: preview_template(user_id="1", template_id="modern")
↓
FunctionHandlers.preview_template() executed
↓
Validates template_id ("modern" is valid)
↓
Calls EventEmitter.emit_event() with 'template_preview_changed'
↓
Event data: { template_id: "modern", action: "preview_template" }
```

### **6. 📡 Event Emission (Django Channels)**
```
EventEmitter.emit_event()
↓
Uses Django Channels to send to WebSocket group
↓
Group name: f'resume_builder_{user_id}'
↓
Sends event to ResumeBuilderConsumer.send_event()
```

### **7. 🔄 WebSocket Response**
```
ResumeBuilderConsumer.send_event()
↓
Sends 'backend_event' message to frontend
↓
Message: { type: 'backend_event', event_type: 'template_preview_changed', data: {...} }
```

### **8. 🎨 Frontend Template Update**
```
Frontend receives WebSocket message
↓
ChatUI.handleWebSocketMessage() processes message
↓
Calls ChatUI.handleBackendEvent('template_preview_changed', data)
↓
Calls ChatUI.handleTemplatePreviewChanged(data)
↓
Calls window.templatePreview.switchTemplate('modern')
```

### **9. 🎯 Template Preview Component**
```
TemplatePreview.switchTemplate('modern')
↓
Updates currentTemplate = 'modern'
↓
Calls TemplatePreview.updateTemplateButtons('modern')
↓
Calls TemplatePreview.loadTemplatePreview('modern')
↓
Makes HTTP request to: /resume/preview_template/modern/?locale=en-US
```

### **10. 🌐 Django Template View**
```
HTTP Request → resume_builder.views.preview_template()
↓
Gets localized sample data for 'modern' template
↓
Renders template: resume_templates/modern.html
↓
Returns HTML content to frontend
```

### **11. ✅ Frontend Update Complete**
```
TemplatePreview receives HTML response
↓
Updates resumePreview.innerHTML with new template
↓
Shows success message in chat: "🎨 Template preview switched to modern!"
↓
Template preview now shows Modern template with sample data
```

---

## 🔧 **Key Components in the Flow**

### **Django Views (resume_builder/views.py)**
- `ai_resume_assistant()` - Renders the main interface
- `chat_with_ai()` - HTTP API endpoint (not used in WebSocket flow)
- `preview_template()` - Returns template HTML
- `get_or_create_assistant()` - Manages AI assistant creation

### **WebSocket Consumer (resume_builder/consumers.py)**
- `ResumeBuilderConsumer.receive()` - Handles incoming messages
- `ResumeBuilderConsumer.process_with_real_ai()` - Integrates with AI assistant
- `ResumeBuilderConsumer.send_event()` - Sends events to frontend

### **AI Assistant (ai_service/ai_resume_assistant.py)**
- `OpenAIAssistantManager.add_message_and_run()` - Main AI processing
- Function calling logic - Executes preview_template function
- User context injection - Ensures real user ID is used

### **Function Handlers (ai_service/function_handlers.py)**
- `FunctionHandlers.preview_template()` - Handles template preview
- `EventEmitter.emit_event()` - Sends events via Django Channels

### **Frontend Components**
- `ChatUI` - Manages chat interface and WebSocket communication
- `TemplatePreview` - Manages template switching and preview
- WebSocket connection - Real-time communication with backend

---

## 🎯 **Template Switching Flow Summary**

```
User Input → WebSocket → Django Consumer → AI Assistant → Function Call → Event Emission → WebSocket → Frontend → Template Update → HTTP Request → Django View → HTML Response → Frontend Update
```

**Total Steps:** 11 major steps
**Technologies Used:** Django, Django Channels, WebSockets, OpenAI Assistant API, JavaScript, HTML/CSS
**Real-time Updates:** Yes, via WebSocket events
**Template Loading:** HTTP requests to Django views for template HTML 