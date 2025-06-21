from .gmail_provider import GmailProvider
from ..models import UserEmailConfiguration

class EmailProviderFactory:
    """Factory for creating email provider instances based on model configuration"""
    
    @classmethod
    def get_provider(cls, provider_type, config=None):
        """
        Get email provider instance based on provider type from model
        
        Args:
            provider_type: Must match UserEmailConfiguration.PROVIDER_CHOICES
            config: UserEmailConfiguration instance
        """
        # Use the same providers as defined in the model
        providers = {
            UserEmailConfiguration.PROVIDER_CHOICES[0][0]: GmailProvider,  # gmail
            # Add other providers here matching model choices
        }
        
        provider_class = providers.get(provider_type.lower())
        if not provider_class:
            raise ValueError(f"Unsupported email provider: {provider_type}. "
                           f"Must be one of: {[choice[0] for choice in UserEmailConfiguration.PROVIDER_CHOICES]}")
            
        return provider_class(config)