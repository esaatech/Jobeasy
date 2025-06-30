from .network_error_messages import (
    NETWORK_TIMEOUT_TITLE, NETWORK_TIMEOUT_MESSAGE,
    NETWORK_CONNECTION_TITLE, NETWORK_CONNECTION_MESSAGE,
    NETWORK_GENERIC_TITLE, NETWORK_GENERIC_MESSAGE
)

def get_network_timeout_dialog():
    """Returns a structured dialog for network timeout errors."""
    return {
        "title": NETWORK_TIMEOUT_TITLE,
        "message": NETWORK_TIMEOUT_MESSAGE,
        "level": "warning",
        "error_type": "network_timeout"
    }

def get_network_connection_dialog():
    """Returns a structured dialog for network connection errors."""
    return {
        "title": NETWORK_CONNECTION_TITLE,
        "message": NETWORK_CONNECTION_MESSAGE,
        "level": "error",
        "error_type": "network_connection"
    }

def get_network_generic_dialog():
    """Returns a structured dialog for generic network errors."""
    return {
        "title": NETWORK_GENERIC_TITLE,
        "message": NETWORK_GENERIC_MESSAGE,
        "level": "error",
        "error_type": "network_generic"
    } 