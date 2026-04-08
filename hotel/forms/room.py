from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, FloatField, IntegerField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, NumberRange, ValidationError

from hotel.models import Room, ROOM_TYPE_SINGLE, ROOM_TYPE_DOUBLE, ROOM_TYPE_TRIPLE

class RoomForm(FlaskForm):
    room_number = StringField('رقم الغرفة', validators=[DataRequired()])
    room_type = SelectField('نوع الغرفة', choices=[
        (ROOM_TYPE_SINGLE, 'Single'),
        (ROOM_TYPE_DOUBLE, 'Double'),
        (ROOM_TYPE_TRIPLE, 'Triple')
    ], validators=[DataRequired()])
    price_per_night = FloatField('السعر لليلة الواحدة', validators=[DataRequired(), NumberRange(min=0)])
    capacity = IntegerField('السعة (عدد الأشخاص)', validators=[DataRequired(), NumberRange(min=1, max=10)])
    description = TextAreaField('وصف الغرفة')
    submit = SubmitField('حفظ')
    
    def validate_room_number(self, room_number):
        room = Room.query.filter_by(room_number=room_number.data).first()
        # التحقق من وجود الغرفة وأنها ليست نفس الغرفة المُعدَّلة
        if room:
            # إذا كان هذا تعديل لغرفة موجودة، تحقق من أن الـ ID مختلف
            if hasattr(self, '_obj') and self._obj and hasattr(self._obj, 'id'):
                if room.id != self._obj.id:
                    raise ValidationError('رقم الغرفة مستخدم بالفعل، الرجاء اختيار رقم آخر')
            else:
                # إذا كان هذا إضافة غرفة جديدة
                raise ValidationError('رقم الغرفة مستخدم بالفعل، الرجاء اختيار رقم آخر')
