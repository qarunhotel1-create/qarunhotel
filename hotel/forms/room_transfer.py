from flask_wtf import FlaskForm
from wtforms import SelectField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Length

class RoomTransferForm(FlaskForm):
    to_room_id = SelectField('الغرفة الجديدة',
                            coerce=int,
                            validators=[DataRequired(message='يرجى اختيار الغرفة الجديدة')])

    new_occupancy_type = SelectField('نوع الإقامة الجديد',
                                   choices=[
                                       ('single', 'Single'),
                                       ('double', 'Double'),
                                       ('triple', 'Triple')
                                   ],
                                   validators=[DataRequired(message='يرجى اختيار نوع الإقامة')])

    reason = TextAreaField('سبب النقل',
                          validators=[Length(max=500, message='سبب النقل يجب أن يكون أقل من 500 حرف')])

    notes = TextAreaField('ملاحظات إضافية',
                         validators=[Length(max=1000, message='الملاحظات يجب أن تكون أقل من 1000 حرف')])

    submit = SubmitField('تنفيذ النقل')
