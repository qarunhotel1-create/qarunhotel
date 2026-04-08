from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import FloatField, SelectField, TextAreaField, SubmitField, HiddenField
from wtforms.validators import DataRequired, NumberRange, ValidationError

from hotel.models.payment import PAYMENT_TYPE_CASH, PAYMENT_TYPE_CARD, PAYMENT_TYPE_BANK_TRANSFER

class PaymentForm(FlaskForm):
    booking_id = HiddenField()
    amount = FloatField('المبلغ المدفوع', validators=[
        DataRequired(message='يرجى إدخال المبلغ'),
        NumberRange(min=1, message='يجب أن يكون المبلغ أكبر من صفر')
    ])
    payment_type = SelectField('طريقة الدفع', choices=[
        (PAYMENT_TYPE_CASH, 'نقدي'),
        (PAYMENT_TYPE_CARD, 'بطاقة ائتمان'),
        (PAYMENT_TYPE_BANK_TRANSFER, 'تحويل بنكي')
    ], validators=[DataRequired()])
    notes = TextAreaField('ملاحظات')
    attachment = FileField('إرفاق ملف (صورة أو PDF)', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'pdf'], 'يُسمح فقط بملفات الصور (JPG, PNG, GIF) أو PDF')
    ])
    submit = SubmitField('تسجيل الدفعة')
    
    def __init__(self, booking=None, *args, **kwargs):
        super(PaymentForm, self).__init__(*args, **kwargs)
        self.booking = booking
    
    def validate_amount(self, amount):
        if self.booking and amount.data > self.booking.remaining_amount:
            raise ValidationError(f'المبلغ المدخل أكبر من المبلغ المتبقي ({self.booking.remaining_amount} جنيه مصري)')
