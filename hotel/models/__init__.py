from hotel.models.user import User, ActivityLog, ROLE_GUEST, ROLE_ADMIN, ROLE_MANAGER, ROLE_RECEPTIONIST, ROLE_ACCOUNTANT
from hotel.models.room import Room, ROOM_TYPE_SINGLE, ROOM_TYPE_DOUBLE, ROOM_TYPE_TRIPLE, ROOM_STATUS_AVAILABLE, ROOM_STATUS_OCCUPIED, ROOM_STATUS_MAINTENANCE
from hotel.models.customer import Customer
from hotel.models.document import CustomerDocument
from hotel.models.booking import Booking, BOOKING_STATUS_PENDING, BOOKING_STATUS_CONFIRMED, BOOKING_STATUS_CHECKED_IN, BOOKING_STATUS_CHECKED_OUT, BOOKING_STATUS_CANCELLED
from hotel.models.booking_guest import BookingGuest
from hotel.models.payment import Payment, PAYMENT_TYPE_CASH, PAYMENT_TYPE_CARD, PAYMENT_TYPE_BANK_TRANSFER, PAYMENT_STATUS_PENDING, PAYMENT_STATUS_COMPLETED, PAYMENT_STATUS_CANCELLED
from hotel.models.room_transfer import RoomTransfer
from hotel.models.permission import Permission, user_permissions
from hotel.models.note import Note, NOTE_STATUS_PENDING, NOTE_STATUS_COMPLETED
