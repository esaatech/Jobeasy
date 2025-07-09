from .subscription_messages import (
    PLUS_UPGRADE_TITLE, PLUS_UPGRADE_MESSAGE,
    ULTIMATE_UPGRADE_TITLE, ULTIMATE_UPGRADE_MESSAGE,
    RESUME_UPDATE_PLUS_TITLE, RESUME_UPDATE_PLUS_MESSAGE,
    RESUME_UPDATE_ULTIMATE_TITLE, RESUME_UPDATE_ULTIMATE_MESSAGE,
    PLUS_FEATURES, ULTIMATE_FEATURES
)

def get_plus_upgrade_dialog():
    """Returns a structured dialog for Plus plan upgrade."""
    return {
        "title": PLUS_UPGRADE_TITLE,
        "message": PLUS_UPGRADE_MESSAGE,
        "level": "info",
        "dialog_type": "subscription_upgrade",
        "plan": "plus",
        "features": PLUS_FEATURES,
        "upgrade_url": "/subscriptions/pricing/?plan=plus"
    }

def get_ultimate_upgrade_dialog():
    """Returns a structured dialog for Ultimate plan upgrade."""
    return {
        "title": ULTIMATE_UPGRADE_TITLE,
        "message": ULTIMATE_UPGRADE_MESSAGE,
        "level": "info",
        "dialog_type": "subscription_upgrade",
        "plan": "ultimate",
        "features": ULTIMATE_FEATURES,
        "upgrade_url": "/subscriptions/pricing/?plan=ultimate"
    }

def get_resume_update_plus_dialog():
    """Returns a structured dialog for resume update Plus requirement."""
    return {
        "title": RESUME_UPDATE_PLUS_TITLE,
        "message": RESUME_UPDATE_PLUS_MESSAGE,
        "level": "warning",
        "dialog_type": "feature_restriction",
        "plan": "plus",
        "features": PLUS_FEATURES
    }

def get_resume_update_ultimate_dialog():
    """Returns a structured dialog for resume update Ultimate requirement."""
    return {
        "title": RESUME_UPDATE_ULTIMATE_TITLE,
        "message": RESUME_UPDATE_ULTIMATE_MESSAGE,
        "level": "warning",
        "dialog_type": "feature_restriction",
        "plan": "ultimate",
        "features": ULTIMATE_FEATURES
    } 