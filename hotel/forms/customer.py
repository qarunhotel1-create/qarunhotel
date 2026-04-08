from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SubmitField, SelectField
from wtforms.validators import DataRequired, Optional, ValidationError, Length

from hotel.models import Customer


class CustomerForm(FlaskForm):
    name = StringField('الاسم الكامل', validators=[
        DataRequired(), Length(min=2, max=100)])
    id_number = StringField('رقم بطاقة الرقم القومي / جواز سفر', validators=[
        Optional(), Length(max=14)])
    nationality = SelectField('الجنسية',
                               choices=[
                                   ('مصري', 'مصري'),
                                   ('جنسية أخرى', 'جنسية أخرى')
                               ],
                               default='مصري',
                               validators=[DataRequired()])

    nationality_other = StringField('اكتب الجنسية', validators=[
        Optional(), Length(max=50)])
    gender = SelectField('الجنس',
                        choices=[
                            ('', 'اختر الجنس'),
                            ('ذكر', 'ذكر'),
                            ('أنثى', 'أنثى')
                        ],
                        validators=[Optional()])
    marital_status = SelectField('الحالة الاجتماعية',
                                 choices=[('', 'اختر الحالة'),
                                          ('متزوج/ة', 'متزوج/ة'),
                                          ('أعزب', 'أعزب'),
                                          ('أرمل/ة', 'أرمل/ة')],
                                 validators=[Optional()])
    phone = StringField('رقم الهاتف', validators=[
        Optional(), Length(min=8, max=20)])
    address = TextAreaField('العنوان', validators=[Optional()])

    # حقول الوثائق - دعم عدة وثائق
    document_files = FileField('رفع الوثائق',
                              validators=[FileAllowed(['jpg', 'jpeg', 'png', 'pdf'],
                                                    'يُسمح فقط بملفات الصور (JPG, PNG) وملفات PDF')],
                              render_kw={'multiple': True, 'accept': '.jpg,.jpeg,.png,.pdf'})
    
    # للتوافق مع الكود القديم
    document_type = SelectField('نوع الوثيقة الأساسية',
                               choices=[('', 'اختر نوع الوثيقة'),
                                       ('id_card', 'بطاقة الهوية'),
                                       ('passport', 'جواز السفر'),
                                       ('driving_license', 'رخصة القيادة'),
                                       ('birth_certificate', 'شهادة الميلاد'),
                                       ('marriage_certificate', 'شهادة الزواج'),
                                       ('work_permit', 'تصريح العمل'),
                                       ('residence_permit', 'تصريح الإقامة'),
                                       ('other', 'أخرى')],
                               validators=[Optional()])

    document_file = FileField('رفع وثيقة واحدة',
                             validators=[FileAllowed(['jpg', 'jpeg', 'png', 'pdf'],
                                                   'يُسمح فقط بملفات الصور (JPG, PNG) وملفات PDF')])

    submit = SubmitField('حفظ')

    def __init__(self, *args, **kwargs):
        super(CustomerForm, self).__init__(*args, **kwargs)
        # This is needed for the validate_id_number validator to work correctly on edits
        if 'obj' in kwargs and kwargs['obj'] is not None:
            self.customer_id = kwargs['obj'].id
        else:
            self.customer_id = None
        
    def validate_id_number(self, id_number):
        # Skip validation if no data is provided
        if not id_number.data or not id_number.data.strip():
            return
            
        # Clean the ID number by removing any whitespace
        clean_id = id_number.data.strip()
        
        # Check if ID number already exists for another customer
        query = Customer.query.filter(Customer.id_number == clean_id)
        
        # If this is an update (customer_id exists), exclude the current customer from the check
        if hasattr(self, 'customer_id') and self.customer_id is not None:
            query = query.filter(Customer.id != self.customer_id)
        
        # If we find any matching customer (other than the current one), raise validation error
        if query.first() is not None:
            raise ValidationError('رقم الهوية مستخدم بالفعل، الرجاء التحقق من الرقم')
