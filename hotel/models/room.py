from hotel import db

# Room types
ROOM_TYPE_SINGLE = 'single'
ROOM_TYPE_DOUBLE = 'double'
ROOM_TYPE_TRIPLE = 'triple'

# Room status
ROOM_STATUS_AVAILABLE = 'available'
ROOM_STATUS_OCCUPIED = 'occupied'
ROOM_STATUS_MAINTENANCE = 'maintenance'

class Room(db.Model):
    __tablename__ = 'rooms'

    id = db.Column(db.Integer, primary_key=True)
    room_number = db.Column(db.String(10), unique=True, nullable=False)
    room_type = db.Column(db.String(20), nullable=False)
    price_per_night = db.Column(db.Float, nullable=False)  # السعر الأساسي

    # أسعار حسب نوع الإقامة
    price_single = db.Column(db.Float, nullable=True)  # سعر Single
    price_double = db.Column(db.Float, nullable=True)  # سعر Double
    price_triple = db.Column(db.Float, nullable=True)  # سعر Triple

    status = db.Column(db.String(20), default=ROOM_STATUS_AVAILABLE)
    capacity = db.Column(db.Integer, default=1)
    description = db.Column(db.Text)
    
    # Room amenities
    has_wifi = db.Column(db.Boolean, default=True)
    has_ac = db.Column(db.Boolean, default=True)
    has_tv = db.Column(db.Boolean, default=True)
    has_minibar = db.Column(db.Boolean, default=False)

    # Relationships
    bookings = db.relationship('Booking', backref='room', lazy='dynamic')

    @property
    def current_booking(self):
        """
        الحصول على الحجز الحالي للغرفة بمنطق محسّن يعتمد على الوقت.
        - تعتبر الغرفة متاحة حتى الساعة 12 ظهراً في يوم وصول حجز مؤكد.
        - تعتبر الغرفة مشغولة حتى الساعة 12 ظهراً في يوم مغادرة حجز مسجل دخوله.
        """
        from hotel.models.booking import Booking, BOOKING_STATUS_CHECKED_IN, BOOKING_STATUS_CONFIRMED
        from hotel.utils.datetime_utils import get_egypt_now

        now = get_egypt_now()
        today = now.date()
        current_hour = now.hour

        # البحث عن كل الحجوزات النشطة اليوم (المسجلة دخول أو المؤكدة)
        # يتم الترتيب لإعطاء الأولوية للمسجل دخوله ثم الأحدث
        bookings = Booking.query.filter(
            Booking.room_id == self.id,
            Booking.status.in_([BOOKING_STATUS_CHECKED_IN, BOOKING_STATUS_CONFIRMED]),
            Booking.check_in_date <= today,
            Booking.check_out_date >= today
        ).order_by(Booking.status.desc(), Booking.id.desc()).all()

        for booking in bookings:
            # الحالة الأولى: نزيل مسجل دخوله (checked_in)
            if booking.status == BOOKING_STATUS_CHECKED_IN:
                # إذا كان يوم المغادرة هو اليوم، فالغرفة مشغولة حتى 12 ظهراً فقط
                if booking.check_out_date == today and current_hour >= 12:
                    continue  # بعد 12 ظهراً، لم يعد هذا الحجز هو "الحالي"، ابحث عن حجز آخر
                else:
                    return booking # في كل الحالات الأخرى، الحجز ساري

            # الحالة الثانية: حجز مؤكد (confirmed)
            elif booking.status == BOOKING_STATUS_CONFIRMED:
                # إذا كان يوم الوصول هو اليوم، فالغرفة محجوزة فقط بعد 12 ظهراً
                if booking.check_in_date == today and current_hour < 12:
                    continue  # قبل 12 ظهراً، الغرفة لا تزال متاحة، تجاهل هذا الحجز
                
                # إذا كان يوم المغادرة هو اليوم، فالغرفة محجوزة حتى 12 ظهراً
                if booking.check_out_date == today and current_hour >= 12:
                    continue # بعد 12 ظهراً، لم يعد هذا الحجز "الحالي"

                # إذا كان الحجز مؤكد لأيام سابقة (ولم يسجل دخوله) أو لأيام قادمة، فهو ساري
                return booking

        # إذا لم يتم العثور على أي حجز ساري حسب المنطق أعلاه
        return None
    
    def __init__(self, room_number, room_type, price_per_night, capacity=1, description=None):
        self.room_number = room_number
        self.room_type = room_type
        self.price_per_night = price_per_night
        self.capacity = capacity
        self.description = description
        self.status = ROOM_STATUS_AVAILABLE
    
    def is_available(self):
        return self.status == ROOM_STATUS_AVAILABLE

    def get_type_display(self):
        """إرجاع اسم نوع الغرفة بالعربية"""
        type_mapping = {
            'single': 'فردية',
            'double': 'مزدوجة',
            'triple': 'ثلاثية',
            'suite': 'جناح',
            'family': 'عائلية'
        }
        return type_mapping.get(self.room_type, self.room_type)

    def get_price_by_occupancy(self, occupancy_type):
        """الحصول على السعر حسب نوع الإقامة"""
        if occupancy_type == 'single':
            return self.price_single or self.price_per_night
        elif occupancy_type == 'double':
            return self.price_double or self.price_per_night
        elif occupancy_type == 'triple':
            return self.price_triple or self.price_per_night
        else:
            return self.price_per_night

    def get_room_type_display(self):
        """الحصول على اسم نوع الغرفة"""
        type_names = {
            ROOM_TYPE_SINGLE: 'Single',
            ROOM_TYPE_DOUBLE: 'Double',
            ROOM_TYPE_TRIPLE: 'Triple'
        }
        return type_names.get(self.room_type, self.room_type)

    def get_status_display(self):
        """الحصول على اسم حالة الغرفة باللغة العربية"""
        status_names = {
            ROOM_STATUS_AVAILABLE: 'متاحة',
            ROOM_STATUS_OCCUPIED: 'مشغولة',
            ROOM_STATUS_MAINTENANCE: 'صيانة'
        }
        return status_names.get(self.status, self.status)

    def __repr__(self):
        return f'<Room {self.room_number}>'
