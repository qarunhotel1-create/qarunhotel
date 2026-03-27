from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectMultipleField, widgets
from wtforms.validators import DataRequired, EqualTo, Length, ValidationError

from hotel.models import User, Permission

class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()

class BookingSearchForm(FlaskForm):
    """نموذج البحث عن الحجوزات"""
    search_query = StringField('البحث',
                              validators=[DataRequired(message='يرجى إدخال كلمة البحث')],
                              render_kw={'placeholder': 'ابحث برقم الحجز، الاسم، رقم التليفون، أو رقم الهوية...'})
    submit = SubmitField('بحث')

class UserForm(FlaskForm):
    username = StringField('اسم المستخدم', validators=[DataRequired(), Length(min=3, max=64)])
    full_name = StringField('الاسم الكامل للموظف', validators=[DataRequired(), Length(min=3, max=120)])
    password = PasswordField('كلمة المرور', validators=[DataRequired()])
    password2 = PasswordField('تأكيد كلمة المرور', validators=[DataRequired(), EqualTo('password')])
    permissions = MultiCheckboxField('الصلاحيات', coerce=int)
    submit = SubmitField('حفظ')

    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        self.permissions.choices = [(p.id, p.description) for p in Permission.query.all()]

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('اسم المستخدم مستخدم بالفعل، الرجاء اختيار اسم آخر')

class EditUserForm(UserForm):
    password = PasswordField('كلمة المرور الجديدة (اتركها فارغة إذا لم تريد تغييرها)')
    password2 = PasswordField('تأكيد كلمة المرور الجديدة', validators=[EqualTo('password')])

    def __init__(self, original_username, *args, **kwargs):
        super(EditUserForm, self).__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=username.data).first()
            if user is not None:
                raise ValidationError('اسم المستخدم مستخدم بالفعل، الرجاء اختيار اسم آخر')