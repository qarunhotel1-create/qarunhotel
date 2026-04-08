from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from hotel import db, login_manager
from hotel.models.permission import user_permissions, Permission
from hotel.utils.datetime_utils import get_egypt_now_naive

ROLE_ADMIN = 'admin'
ROLE_MANAGER = 'manager'
ROLE_RECEPTIONIST = 'receptionist'
ROLE_ACCOUNTANT = 'accountant'
ROLE_GUEST = 'guest'


class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), default=ROLE_GUEST)
    full_name = db.Column(db.String(120))
    is_guest = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=get_egypt_now_naive)

    # Relationships
    permissions = db.relationship('Permission', secondary=user_permissions,
                                  backref=db.backref('users', lazy='dynamic'), lazy='dynamic')
    bookings = db.relationship('Booking', backref='user', lazy='dynamic')

    def __init__(self, username, password, role=ROLE_GUEST, full_name=None, permissions=None, is_guest=False):
        self.username = username
        self.set_password(password)
        self.role = role
        self.full_name = full_name or username
        self.is_guest = is_guest
        if permissions:
            # permissions may be list of Permission objects
            for p in permissions:
                self.permissions.append(p)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == ROLE_ADMIN or self.has_permission('admin')

    # Permission helpers
    def has_permission(self, perm_name: str) -> bool:
        if self.role == ROLE_ADMIN:
            return True
        try:
            return any(p.name == perm_name for p in self.permissions)
        except Exception:
            # if relationship isn't loaded yet, fallback to query
            if hasattr(self.permissions, 'filter'):
                return self.permissions.filter(Permission.name == perm_name).count() > 0
            return False

    def can_add_payment(self):
        return self.has_permission('add_payment') or self.has_permission('manage_payments') or self.is_admin()

    def can_delete_payment(self):
        return self.has_permission('delete_payment') or self.has_permission('manage_payments') or self.is_admin()

    def can_create_booking(self):
        return self.has_permission('create_booking') or self.has_permission('manage_bookings') or self.is_admin()

    def can_edit_booking(self):
        return self.has_permission('edit_booking') or self.has_permission('manage_bookings') or self.is_admin()

    def can_check_in_out(self):
        return self.has_permission('check_in_out') or self.has_permission('manage_bookings') or self.is_admin()

    def can_view_reports(self):
        return self.has_permission('view_reports') or self.is_admin()

    def can_manage_customers(self):
        return self.has_permission('manage_customers') or self.is_admin()
        
    def can_manage_rooms(self):
        return self.has_permission('manage_rooms') or self.is_admin()
        
    def can_manage_users(self):
        return self.has_permission('manage_users') or self.is_admin()
        
    def can_manage_bookings(self):
        return self.has_permission('manage_bookings') or self.is_admin()
        
    def can_transfer_room(self):
        return self.has_permission('transfer_room') or self.has_permission('manage_bookings') or self.is_admin()

    def can_access_admin_panel(self):
        """Whether the user can access the admin panel/UI.

        Admins always have access. Otherwise, defer to a dedicated
        'access_admin_panel' permission if it exists in the system.
        """
        return self.is_admin() or self.has_permission('access_admin_panel')
        
    def get_role_display_name(self):
        """Return the display name for the user's role."""
        role_names = {
            ROLE_ADMIN: 'مدير النظام',
            ROLE_MANAGER: 'مدير عام',
            ROLE_RECEPTIONIST: 'موظف استقبال',
            ROLE_ACCOUNTANT: 'محاسب',
            ROLE_GUEST: 'عميل'
        }
        return role_names.get(self.role, self.role)

    def __repr__(self):
        return f'<User {self.username}>'


class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user_full_name = db.Column(db.String(120))
    action = db.Column(db.String(64), nullable=False)
    details = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=get_egypt_now_naive)

    def __repr__(self):
        return f'<ActivityLog {self.action} by {self.user_full_name}>'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
