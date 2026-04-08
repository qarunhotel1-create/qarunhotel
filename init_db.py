from datetime import datetime, timedelta
from hotel import create_app, db
from hotel.models import User, Room, Customer, Booking, Payment
from hotel.models import ROLE_ADMIN, ROLE_GUEST, ROLE_MANAGER, ROLE_RECEPTIONIST, ROLE_ACCOUNTANT
from hotel.models.room import ROOM_TYPE_SINGLE, ROOM_TYPE_DOUBLE, ROOM_TYPE_TRIPLE

def init_db():
    app = create_app()
    with app.app_context():
        # Drop all tables
        db.drop_all()

        # Create all tables
        db.create_all()

        # Create admin user
        admin = User(
            username='admin',
            password='admin',
            role=ROLE_ADMIN
        )

        # Create guest user
        guest = User(
            username='guest',
            password='guest123',
            role=ROLE_GUEST
        )

        # Create manager user
        manager = User(
            username='manager',
            password='manager123',
            role=ROLE_MANAGER
        )

        # Create receptionist user
        receptionist = User(
            username='receptionist',
            password='receptionist123',
            role=ROLE_RECEPTIONIST
        )

        # Create accountant user
        accountant = User(
            username='accountant',
            password='accountant123',
            role=ROLE_ACCOUNTANT
        )

        db.session.add(admin)
        db.session.add(guest)
        db.session.add(manager)
        db.session.add(receptionist)
        db.session.add(accountant)

        # Create rooms
        rooms = [
            Room(room_number='101', room_type=ROOM_TYPE_SINGLE, price_per_night=500, capacity=1,
                 description='غرفة مفردة مع سرير واحد وحمام خاص وتلفزيون وواي فاي'),
            Room(room_number='102', room_type=ROOM_TYPE_SINGLE, price_per_night=500, capacity=1,
                 description='غرفة مفردة مع سرير واحد وحمام خاص وتلفزيون وواي فاي'),
            Room(room_number='201', room_type=ROOM_TYPE_DOUBLE, price_per_night=800, capacity=2,
                 description='غرفة مزدوجة مع سريرين وحمام خاص وتلفزيون وواي فاي وثلاجة صغيرة'),
            Room(room_number='202', room_type=ROOM_TYPE_DOUBLE, price_per_night=800, capacity=2,
                 description='غرفة مزدوجة مع سريرين وحمام خاص وتلفزيون وواي فاي وثلاجة صغيرة'),
            Room(room_number='301', room_type=ROOM_TYPE_TRIPLE, price_per_night=1200, capacity=3,
                 description='غرفة ثلاثية مع ثلاثة أسرة وحمام خاص وتلفزيون وواي فاي وثلاجة'),
            Room(room_number='302', room_type=ROOM_TYPE_TRIPLE, price_per_night=1200, capacity=3,
                 description='غرفة ثلاثية مع ثلاثة أسرة وحمام خاص وتلفزيون وواي فاي وثلاجة')
        ]

        # Set amenities for rooms
        for room in rooms:
            room.has_wifi = True
            room.has_ac = True
            room.has_tv = True
            if room.room_type == ROOM_TYPE_TRIPLE:
                room.has_minibar = True
            db.session.add(room)

        # لا نقوم بإنشاء عملاء افتراضيين

        # Commit to get IDs
        db.session.commit()

        # لا نقوم بإنشاء حجوزات افتراضية

        # Commit all changes
        db.session.commit()

        print('Database initialized with sample data!')

if __name__ == '__main__':
    init_db()