from django.core.management.base import BaseCommand
from email_utility.models import EmailFunctionSchema, AgentEmailConfiguration

class Command(BaseCommand):
    help = 'Initialize default function schemas for email tasks'

    def handle(self, *args, **kwargs):
        default_schemas = {
            AgentEmailConfiguration.TaskTypes.AUTO_RESPOND: {
                'name': 'auto_respond_email',
                'description': 'Automatically respond to an incoming email',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'recipient': {
                            'type': 'string',
                            'description': 'Email address of the recipient'
                        },
                        'subject': {
                            'type': 'string',
                            'description': 'Subject line of the email'
                        },
                        'content': {
                            'type': 'string',
                            'description': 'Main body content of the email'
                        },
                        'original_email': {
                            'type': 'string',
                            'description': 'Content of the original email being responded to'
                        }
                    },
                    'required': ['recipient', 'subject', 'content', 'original_email']
                },
                'instructions': """When auto-responding to an email:
                1. Analyze the original email content
                2. Generate an appropriate response
                3. Use this function to send the auto-response
                4. Keep the tone professional and contextually appropriate""",
                'handler_path': 'email_utility.function_routers.EmailFunctionRouter.auto_respond_email'
            },
            
            AgentEmailConfiguration.TaskTypes.REPLY_EMAIL: {
                'name': 'reply_to_email',
                'description': 'Reply to an existing email thread',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'recipient': {
                            'type': 'string',
                            'description': 'Email address of the recipient'
                        },
                        'subject': {
                            'type': 'string',
                            'description': 'Subject line (should maintain thread)'
                        },
                        'content': {
                            'type': 'string',
                            'description': 'Reply content'
                        },
                        'thread_id': {
                            'type': 'string',
                            'description': 'ID of the email thread being replied to'
                        },
                        'quoted_text': {
                            'type': 'string',
                            'description': 'Text being replied to'
                        }
                    },
                    'required': ['recipient', 'subject', 'content', 'thread_id']
                },
                'instructions': """When replying to an email:
                1. Reference the original message
                2. Address all points in the original email
                3. Maintain the email thread
                4. Use this function to send the reply""",
                'handler_path': 'email_utility.function_routers.EmailFunctionRouter.reply_to_email'
            },
            
            AgentEmailConfiguration.TaskTypes.FORWARD_EMAIL: {
                'name': 'forward_email',
                'description': 'Forward an email to another recipient',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'recipient': {
                            'type': 'string',
                            'description': 'Email address to forward to'
                        },
                        'subject': {
                            'type': 'string',
                            'description': 'Subject line (usually prefixed with Fwd:)'
                        },
                        'content': {
                            'type': 'string',
                            'description': 'Any additional message to include'
                        },
                        'original_email': {
                            'type': 'string',
                            'description': 'Content of the email being forwarded'
                        }
                    },
                    'required': ['recipient', 'subject', 'content', 'original_email']
                },
                'instructions': """When forwarding an email:
                1. Maintain the original email content
                2. Add any necessary context
                3. Use this function to forward the email
                4. Include appropriate forwarding notation""",
                'handler_path': 'email_utility.function_routers.EmailFunctionRouter.forward_email'
            },
            
            AgentEmailConfiguration.TaskTypes.SAVE_EMAIL: {
                'name': 'save_email',
                'description': 'Save an email draft to the system',
                'parameters': {
                    'type': 'object',
                    'properties': {
                        'recipient': {
                            'type': 'string',
                            'description': 'Email address of the recipient'
                        },
                        'subject': {
                            'type': 'string',
                            'description': 'Subject line of the email'
                        },
                        'content': {
                            'type': 'string',
                            'description': 'Main body content of the email'
                        }
                    },
                    'required': ['recipient', 'subject', 'content']
                },
                'instructions': """When drafting a new email:
                1. Compose a professional email
                2. Include all necessary information
                3. Use this function to save the draft
                4. Confirm after saving""",
                'handler_path': 'email_utility.function_routers.EmailFunctionRouter.save_email'
            }
        }

        for task_type, schema_data in default_schemas.items():
            schema, created = EmailFunctionSchema.objects.get_or_create(
                task_type=task_type,
                defaults={
                    'name': schema_data['name'],
                    'description': schema_data['description'],
                    'parameters': schema_data['parameters'],
                    'instructions': schema_data['instructions'],
                    'handler_path': schema_data['handler_path']
                }
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created schema for {task_type}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Schema already exists for {task_type}')
                ) 