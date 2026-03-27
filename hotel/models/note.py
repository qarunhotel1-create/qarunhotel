from datetime import datetime
from flask_login import current_user
from hotel import db
from hotel.utils.datetime_utils import get_egypt_now_naive


NOTE_STATUS_PENDING = 'pending'
NOTE_STATUS_COMPLETED = 'completed'


class Note(db.Model):
    __tablename__ = 'notes'

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default=NOTE_STATUS_PENDING, nullable=False)
    created_at = db.Column(db.DateTime, default=get_egypt_now_naive)
    completed_at = db.Column(db.DateTime, nullable=True)

    # Optional relationships for convenience (no backrefs to keep it simple)
    # These require User model to be imported only at runtime if needed to avoid circular imports

    def mark_completed(self):
        self.status = NOTE_STATUS_COMPLETED
        self.completed_at = get_egypt_now_naive()

    @property
    def is_completed(self) -> bool:
        return self.status == NOTE_STATUS_COMPLETED

    def __repr__(self):
        return f'<Note {self.id} from {self.sender_id} to {self.receiver_id}>'