from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, TextAreaField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Length, Email, Optional, ValidationError
from wtforms.widgets import TextArea

from hotel.models.customer import Customer

class AddExistingGuestForm(FlaskForm):
    """نموذج إضافة عميل موجود كمرافق"""
    customer_search = StringField('البحث عن العميل',
                                 validators=[DataRequired()],
                                 render_kw={'placeholder': 'ابحث بالاسم أو رقم الهوية أو الهاتف...'})
    customer_id = HiddenField('معرف العميل', validators=[DataRequired()])
    guest_type = SelectField('نوع المرافق',
                            choices=[
                                ('companion', 'مرافق'),
                                ('family', 'عائلة'),
                                ('friend', 'صديق'),
                                ('colleague', 'زميل'),
                                ('other', 'آخر')
                            ],
                            default='companion',
                            validators=[DataRequired()])
    relationship = StringField('العلاقة',
                              validators=[Optional(), Length(max=100)],
                              render_kw={'placeholder': 'مثل: أخ، زوج، صديق...'})
    notes = TextAreaField('ملاحظات',
                         validators=[Optional(), Length(max=500)],
                         render_kw={'placeholder': 'ملاحظات إضافية عن المرافق...', 'rows': 3})
    submit = SubmitField('إضافة المرافق')

class AddNewGuestForm(FlaskForm):
    """نموذج إضافة عميل جديد كمرافق"""
    name = StringField('الاسم الكامل', 
                      validators=[DataRequired(), Length(min=2, max=100)])
    
    id_number = StringField('رقم الهوية/الجواز',
                           validators=[DataRequired(), Length(min=10, max=20)])

    national_id = StringField('رقم الهوية الوطنية',
                             validators=[DataRequired(), Length(min=10, max=20)])
    
    phone = StringField('رقم الهاتف', 
                       validators=[Optional(), Length(max=20)])
    
    email = StringField('البريد الإلكتروني', 
                       validators=[Optional(), Email(), Length(max=120)])
    
    address = TextAreaField('العنوان', 
                           validators=[Optional(), Length(max=500)],
                           widget=TextArea())
    
    nationality = SelectField('الجنسية',
                               choices=[
                                   ('', 'اختر الجنسية...'),
                                   ('مصري', 'مصري'),
                                   ('سعودي', 'سعودي'),
                                   ('كويتي', 'كويتي'),
                                   ('إماراتي', 'إماراتي'),
                                   ('قطري', 'قطري'),
                                   ('بحريني', 'بحريني'),
                                   ('عماني', 'عماني'),
                                   ('أردني', 'أردني'),
                                   ('لبناني', 'لبناني'),
                                   ('سوري', 'سوري'),
                                   ('عراقي', 'عراقي'),
                                   ('فلسطيني', 'فلسطيني'),
                                   ('ليبي', 'ليبي'),
                                   ('تونسي', 'تونسي'),
                                   ('جزائري', 'جزائري'),
                                   ('مغربي', 'مغربي'),
                                   ('سوداني', 'سوداني'),
                                   ('يمني', 'يمني'),
                                   ('other', 'جنسية أخرى')
                               ],
                               validators=[Optional()])
    
    guest_type = SelectField('نوع المرافق',
                            choices=[
                                ('companion', 'مرافق'),
                                ('family', 'عائلة'),
                                ('friend', 'صديق'),
                                ('colleague', 'زميل'),
                                ('other', 'آخر')
                            ],
                            default='companion',
                            validators=[DataRequired()])

    relationship = StringField('العلاقة',
                              validators=[Optional(), Length(max=100)],
                              render_kw={'placeholder': 'مثل: أخ، زوج، صديق...'})

    notes = TextAreaField('ملاحظات',
                         validators=[Optional(), Length(max=500)],
                         render_kw={'placeholder': 'ملاحظات إضافية عن المرافق...', 'rows': 3})

    submit = SubmitField('إضافة العميل كمرافق')
    
    def validate_id_number(self, field):
        """التحقق من عدم تكرار رقم الهوية"""
        customer = Customer.query.filter_by(id_number=field.data).first()
        if customer:
            raise ValidationError('رقم الهوية موجود بالفعل. استخدم نموذج "إضافة عميل موجود" بدلاً من ذلك.')

    def validate_national_id(self, field):
        """التحقق من عدم تكرار رقم الهوية الوطنية"""
        customer = Customer.query.filter_by(id_number=field.data).first()
        if customer:
            raise ValidationError('رقم الهوية موجود بالفعل. استخدم نموذج "إضافة عميل موجود" بدلاً من ذلك.')

class GuestSearchForm(FlaskForm):
    """نموذج البحث عن العملاء للمرافقين"""
    search_query = StringField('البحث', 
                              validators=[DataRequired(), Length(min=2, max=100)],
                              render_kw={'placeholder': 'ابحث بالاسم أو رقم الهوية أو الهاتف...'})
    submit = SubmitField('بحث')
