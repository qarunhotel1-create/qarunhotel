from flask_wtf import FlaskForm
from wtforms import SelectField, DateField, TextAreaField, SubmitField, HiddenField, StringField, IntegerField, FloatField, BooleanField
from wtforms.validators import DataRequired, ValidationError, Optional, NumberRange
from datetime import datetime, timedelta

class BookingForm(FlaskForm):
    # حقل البحث اليدوي عن العميل
    customer_search = StringField('البحث عن العميل',
                                 render_kw={'placeholder': 'ابحث بالاسم أو رقم الهوية أو الهاتف...'})
    customer_id = HiddenField('معرف العميل', validators=[DataRequired(message='يجب اختيار عميل')])
    room_id = SelectField('الغرفة', coerce=lambda x: int(x) if x else None, validators=[DataRequired()])
    occupancy_type = SelectField('نوع الإقامة',
                                choices=[('', 'اختر نوع الإقامة...'),
                                        ('single', 'Single - إقامة مفردة'),
                                        ('double', 'Double - إقامة مزدوجة'),
                                        ('triple', 'Triple - إقامة ثلاثية')],
                                validators=[DataRequired()])
    check_in_date = DateField('تاريخ الوصول', format='%Y-%m-%d', validators=[DataRequired()])
    check_out_date = DateField('تاريخ المغادرة', format='%Y-%m-%d', validators=[DataRequired()])
    discount_percentage = FloatField('نسبة الخصم (%)',
                                   validators=[Optional(), NumberRange(min=0, max=100)],
                                   default=0.0)
    discount_amount = FloatField('مبلغ الخصم (جنيه)',
                               validators=[Optional(), NumberRange(min=0)],
                               default=0.0)
    discount_amount = FloatField('مبلغ الخصم (جنيه)',
                               validators=[Optional(), NumberRange(min=0)],
                               default=0.0)
    include_tax = BooleanField('إضافة ضريبة 14%', default=False)
    is_deus = BooleanField('ديوز', default=False)
    notes = TextAreaField('ملاحظات', validators=[Optional()])
    submit = SubmitField('تأكيد الحجز')

    def validate_check_in_date(self, check_in_date):
        # إزالة قيد منع التواريخ في الماضي - يمكن اختيار أي تاريخ
        pass

    def validate_check_out_date(self, check_out_date):
        # إزالة قيد التواريخ - يمكن اختيار أي تاريخ
        pass


class BookingSearchForm(FlaskForm):
    start_date = DateField('من تاريخ', format='%Y-%m-%d', validators=[DataRequired()])
    end_date = DateField('إلى تاريخ', format='%Y-%m-%d', validators=[DataRequired()])
    submit = SubmitField('بحث')
