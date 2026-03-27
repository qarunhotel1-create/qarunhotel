from hotel import create_app
from hotel.models.payment import Payment
from hotel.models.booking import Booking

app = create_app()

with app.app_context():
    rows = (
        Payment.query
        .join(Booking, Payment.booking_id == Booking.id)
        .filter(Booking.id == 33)
        .order_by(Payment.id)
        .all()
    )
    print('count=', len(rows))
    for p in rows:
        print('id=', p.id, 'type=', p.payment_type, 'file=', repr(p.attachment_file), 'amount=', p.amount)