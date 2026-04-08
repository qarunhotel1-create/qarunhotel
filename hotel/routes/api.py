from flask import Blueprint, jsonify, request
from flask_login import login_required
from sqlalchemy import or_

from hotel.models.customer import Customer
from hotel.models.booking_guest import BookingGuest

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/test')
def test_api():
    """اختبار API"""
    return jsonify({
        'success': True,
        'message': 'API is working!',
        'timestamp': str(request.args.get('t', 'no timestamp'))
    })

@api_bp.route('/test-search')
def test_search():
    """اختبار البحث"""
    try:
        query = request.args.get('q', 'محمد')
        customers = Customer.query.filter(Customer.name.ilike(f'%{query}%')).all()

        customers_data = []
        for customer in customers:
            customers_data.append({
                'id': customer.id,
                'name': customer.name,
                'id_number': customer.id_number
            })

        return jsonify({
            'success': True,
            'query': query,
            'customers': customers_data,
            'count': len(customers_data)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

@api_bp.route('/customers/available-for-booking/<int:booking_id>')
@login_required
def get_available_customers(booking_id):
    """الحصول على العملاء المتاحين للإضافة كمرافقين"""
    try:
        # الحصول على العملاء الذين ليسوا مرافقين نشطين في هذا الحجز
        existing_guests = BookingGuest.query.filter_by(
            booking_id=booking_id, is_active=True
        ).all()

        existing_guest_ids = [g.customer_id for g in existing_guests]

        # الحصول على جميع العملاء
        if existing_guest_ids:
            customers = Customer.query.filter(~Customer.id.in_(existing_guest_ids)).order_by(Customer.name).limit(20).all()
        else:
            customers = Customer.query.order_by(Customer.name).limit(20).all()

        customers_data = []
        for customer in customers:
            customers_data.append({
                'id': customer.id,
                'name': customer.name or '',
                'id_number': customer.id_number or '',
                'phone': customer.phone or '',
                'nationality': customer.nationality or '',
                'address': customer.address or ''
            })

        return jsonify({
            'success': True,
            'customers': customers_data,
            'count': len(customers_data)
        })

    except Exception as e:
        print(f"Error in get_available_customers: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/customers/search')
@login_required
def search_customers():
    """البحث عن العملاء"""
    try:
        query = request.args.get('q', '').strip()
        booking_id = request.args.get('booking_id', type=int)

        if not query or len(query) < 2:
            return jsonify({
                'success': False,
                'error': 'يجب أن يكون البحث أكثر من حرفين'
            }), 400

        # الحصول على معلومات الحجز
        from hotel.models.booking import Booking
        booking = Booking.query.get(booking_id) if booking_id else None

        # الحصول على العملاء الذين ليسوا مرافقين نشطين في هذا الحجز
        existing_guest_ids = []
        if booking_id:
            existing_guests = BookingGuest.query.filter_by(
                booking_id=booking_id, is_active=True
            ).all()
            existing_guest_ids = [g.customer_id for g in existing_guests]

            # إضافة العميل الأساسي للحجز إلى القائمة المستبعدة
            if booking and booking.customer_id:
                existing_guest_ids.append(booking.customer_id)

        # البحث البسيط في الاسم فقط أولاً
        customers_query = Customer.query.filter(
            Customer.name.contains(query)
        )

        if existing_guest_ids:
            customers_query = customers_query.filter(~Customer.id.in_(existing_guest_ids))

        customers = customers_query.order_by(Customer.name).limit(20).all()

        customers_data = []
        for customer in customers:
            customers_data.append({
                'id': customer.id,
                'name': customer.name or '',
                'id_number': customer.id_number or '',
                'phone': customer.phone or '',
                'nationality': customer.nationality or '',
                'address': customer.address or ''
            })

        return jsonify({
            'success': True,
            'customers': customers_data,
            'query': query,
            'count': len(customers_data)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@api_bp.route('/customers/<int:customer_id>')
@login_required
def get_customer(customer_id):
    """الحصول على معلومات عميل واحد"""
    try:
        customer = Customer.query.get(customer_id)
        if not customer:
            return jsonify({
                'success': False,
                'error': 'العميل غير موجود'
            }), 404

        customer_data = {
            'id': customer.id,
            'name': customer.name or '',
            'id_number': customer.id_number or '',
            'phone': customer.phone or '',
            'nationality': customer.nationality or '',
            'address': customer.address or ''
        }

        return jsonify({
            'success': True,
            'customer': customer_data
        })

    except Exception as e:
        print(f"Error in get_customer: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
