#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple dashboard error diagnosis
"""

import os
import sys
import traceback
from datetime import date

# Add project path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_dashboard():
    """Test dashboard components step by step"""
    print("Starting dashboard diagnosis...")
    
    try:
        # 1. Basic imports
        print("\n1. Testing basic imports...")
        from hotel import create_app, db
        from hotel.models import User, Room, Booking, Customer, Payment, Permission, ActivityLog
        print("Basic imports: OK")
        
        # 2. Create app
        print("\n2. Creating app...")
        app = create_app()
        print("App creation: OK")
        
        # 3. Database connection
        print("\n3. Testing database connection...")
        with app.app_context():
            total_rooms = Room.query.count()
            print(f"Total rooms: {total_rooms}")
            
            total_bookings = Booking.query.count()
            print(f"Total bookings: {total_bookings}")
            
            total_customers = Customer.query.count()
            print(f"Total customers: {total_customers}")
        
        # 4. Test arabic_date
        print("\n4. Testing arabic_date...")
        from hotel.utils.arabic_date import get_arabic_date
        today = date.today()
        today_formatted = get_arabic_date(today)
        print(f"Arabic date: {today_formatted}")
        
        # 5. Test complex queries
        print("\n5. Testing complex queries...")
        with app.app_context():
            all_rooms = Room.query.order_by(Room.room_number).all()
            print(f"Ordered rooms count: {len(all_rooms)}")
            
            # Test active bookings query
            active_bookings = Booking.query.filter(
                Booking.status.in_(['pending', 'confirmed', 'checked_in'])
            ).count()
            print(f"Active bookings: {active_bookings}")
            
            # Test recent bookings
            recent_bookings = Booking.query.order_by(Booking.created_at.desc()).limit(5).all()
            print(f"Recent bookings: {len(recent_bookings)}")
        
        # 6. Test room status logic
        print("\n6. Testing room status logic...")
        with app.app_context():
            rooms_tested = 0
            for room in all_rooms[:3]:  # Test first 3 rooms only
                try:
                    # Search for normal booking
                    normal_booking = Booking.query.filter(
                        Booking.room_id == room.id,
                        Booking.check_in_date <= today,
                        Booking.check_out_date > today,
                        Booking.is_deus == False,
                        Booking.status.in_(['confirmed', 'checked_in'])
                    ).first()
                    
                    # Search for deus booking
                    deus_booking = Booking.query.filter(
                        Booking.room_id == room.id,
                        Booking.check_in_date <= today,
                        Booking.check_out_date >= today,
                        Booking.is_deus == True,
                        Booking.status == 'checked_in'
                    ).first()
                    
                    active_booking = normal_booking or deus_booking
                    rooms_tested += 1
                    
                except Exception as e:
                    print(f"Error testing room {room.room_number}: {e}")
                    return False
            
            print(f"Successfully tested {rooms_tested} rooms")
        
        # 7. Full dashboard simulation
        print("\n7. Full dashboard simulation...")
        with app.app_context():
            # Basic statistics
            total_rooms = Room.query.count()
            available_rooms = Room.query.filter_by(status='available').count()
            total_bookings = Booking.query.count()
            active_bookings = Booking.query.filter(Booking.status.in_(['pending', 'confirmed', 'checked_in'])).count()
            total_customers = Customer.query.count()
            recent_bookings = Booking.query.order_by(Booking.created_at.desc()).limit(5).all()
            
            # Room status
            all_rooms = Room.query.order_by(Room.room_number).all()
            rooms_status = []
            
            for room in all_rooms:
                normal_booking = Booking.query.filter(
                    Booking.room_id == room.id,
                    Booking.check_in_date <= today,
                    Booking.check_out_date > today,
                    Booking.is_deus == False,
                    Booking.status.in_(['confirmed', 'checked_in'])
                ).first()
                
                deus_booking = Booking.query.filter(
                    Booking.room_id == room.id,
                    Booking.check_in_date <= today,
                    Booking.check_out_date >= today,
                    Booking.is_deus == True,
                    Booking.status == 'checked_in'
                ).first()
                
                active_booking = normal_booking or deus_booking
                
                room_class = 'available'
                status_text = 'Available'
                status_icon = 'fas fa-door-open'
                
                if active_booking:
                    if active_booking.is_deus:
                        room_class = 'occupied'
                        status_text = 'Deus Active'
                        status_icon = 'fas fa-clock'
                    else:
                        room_class = 'occupied'
                        status_text = 'Occupied'
                        status_icon = 'fas fa-user'
                
                room_info = {
                    'room': room,
                    'is_occupied': active_booking is not None,
                    'booking': active_booking,
                    'status_class': room_class,
                    'status_text': status_text,
                    'status_icon': status_icon
                }
                rooms_status.append(room_info)
            
            occupied_today = sum(1 for room in rooms_status if room['is_occupied'])
            available_today = total_rooms - occupied_today
            
            print(f"Dashboard simulation successful:")
            print(f"   - Total rooms: {total_rooms}")
            print(f"   - Available rooms: {available_rooms}")
            print(f"   - Total bookings: {total_bookings}")
            print(f"   - Active bookings: {active_bookings}")
            print(f"   - Total customers: {total_customers}")
            print(f"   - Occupied today: {occupied_today}")
            print(f"   - Available today: {available_today}")
            print(f"   - Date: {today_formatted}")
        
        print("\nAll tests passed! Dashboard should work normally.")
        return True
        
    except Exception as e:
        print(f"\nError in diagnosis: {e}")
        print(f"Error type: {type(e).__name__}")
        print("\nError details:")
        traceback.print_exc()
        return False

def test_permissions():
    """Test user permissions for dashboard access"""
    print("\nTesting user permissions...")
    
    try:
        from hotel import create_app, db
        from hotel.models import User, Permission
        
        app = create_app()
        
        with app.app_context():
            # Check if admin user exists
            admin_user = User.query.filter_by(username='admin').first()
            if admin_user:
                print(f"Admin user found: {admin_user.username}")
                print(f"Admin permissions count: {len(admin_user.permissions)}")
                
                # Check for dashboard permission
                dashboard_perm = Permission.query.filter_by(name='dashboard').first()
                if dashboard_perm:
                    print("Dashboard permission exists in database")
                    if dashboard_perm in admin_user.permissions:
                        print("Admin has dashboard permission")
                    else:
                        print("ERROR: Admin does NOT have dashboard permission!")
                        return False
                else:
                    print("ERROR: Dashboard permission does NOT exist in database!")
                    return False
            else:
                print("ERROR: Admin user not found!")
                return False
        
        print("Permission test: OK")
        return True
        
    except Exception as e:
        print(f"Error in permission test: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Dashboard Internal Server Error Diagnosis")
    print("=" * 60)
    
    # Test components
    components_ok = test_dashboard()
    
    # Test permissions
    permissions_ok = test_permissions()
    
    print("\n" + "=" * 60)
    if components_ok and permissions_ok:
        print("DIAGNOSIS: No obvious problems in code")
        print("The issue might be:")
        print("   - User permissions (permission_required)")
        print("   - Login state (login_required)")
        print("   - Server or environment issue")
        print("   - Template rendering problem")
    else:
        print("PROBLEMS FOUND - Check errors above")
    print("=" * 60)
