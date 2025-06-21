from abc import ABC, abstractmethod

class EmailProvider(ABC):
    """Base class for email providers"""
    
    @abstractmethod
    def connect(self):
        """Establish connection to email service"""
        pass
    
    @abstractmethod
    def get_messages(self):
        """Retrieve messages"""
        pass
    
    @abstractmethod
    def send_message(self, to, subject, body):
        """Send email message"""
        pass 