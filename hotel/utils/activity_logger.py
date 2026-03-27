"""
وحدة تسجيل النشاطات
"""

from hotel import db
from hotel.models.user import ActivityLog


def log_activity(user, action, details):
    """Helper function to log user activity."""
    if not user.is_authenticated or user.is_guest:
        return
        
    log = ActivityLog(
        user_id=user.id,
        user_full_name=user.full_name,
        action=action,
        details=details
    )
    db.session.add(log)
    # We don't commit here, the commit should happen with the main action
