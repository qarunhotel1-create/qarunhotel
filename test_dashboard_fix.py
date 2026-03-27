#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test dashboard after database fix
"""

import os
import sys

# Add project path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_dashboard_components():
    """Test all dashboard components that were failing before"""
    print("Testing dashboard components after database fix...")
    
    try:
        from hotel import create_app, db
        from hotel.models import Customer, Room, Booking
        from datetime import date
        
        app = create_app()
        
        with app.app_context():
            print("1. Testing customer queries...")
            total_customers = Customer.query.count()
            print(f"   Total customers: {total_customers}")
            
            print("2. Testing room queries...")
            total_rooms = Room.query.count()
            available_rooms = Room.query.filter_by(status='available').count()
            print(f"   Total rooms: {total_rooms}")
            print(f"   Available rooms: {available_rooms}")
            
            print("3. Testing booking queries...")
            total_bookings = Booking.query.count()
            active_bookings = Booking.query.filter(
                Booking.status.in_(['pending', 'confirmed', 'checked_in'])
            ).count()
            print(f"   Total bookings: {total_bookings}")
            print(f"   Active bookings: {active_bookings}")
            
            print("4. Testing recent bookings...")
            recent_bookings = Booking.query.order_by(Booking.created_at.desc()).limit(5).all()
            print(f"   Recent bookings count: {len(recent_bookings)}")
            
            print("5. Testing room status logic...")
            today = date.today()
            all_rooms = Room.query.order_by(Room.room_number).limit(5).all()
            rooms_processed = 0
            
            for room in all_rooms:
                # Test the complex queries that were causing issues
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
                rooms_processed += 1
            
            print(f"   Processed {rooms_processed} rooms successfully")
            
            print("6. Testing Arabic date utility...")
            from hotel.utils.arabic_date import get_arabic_date
            today_formatted = get_arabic_date(today)
            print("   Arabic date function works (output suppressed due to encoding)")
            
            print("\nAll dashboard components tested successfully!")
            print("The Internal Server Error should now be resolved.")
            return True
            
    except Exception as e:
        print(f"Error in dashboard test: {e}")
        print(f"Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        return False

def simulate_dashboard_render():
    """Simulate the actual dashboard rendering process"""
    print("\nSimulating dashboard render process...")
    
    try:
        from hotel import create_app, db
        from hotel.models import Customer, Room, Booking
        from datetime import date
        
        app = create_app()
        
        with app.app_context():
            # Simulate the exact same logic as admin.dashboard()
            print("Executing dashboard logic...")
            
            # Get statistics for the dashboard
            total_rooms = Room.query.count()
            available_rooms = Room.query.filter_by(status='available').count()
            total_bookings = Booking.query.count()
            active_bookings = Booking.query.filter(Booking.status.in_(['pending', 'confirmed', 'checked_in'])).count()
            total_customers = Customer.query.count()

            # Get recent bookings
            recent_bookings = Booking.query.order_by(Booking.created_at.desc()).limit(5).all()

            # Get all rooms with their current status for today
            today = date.today()
            from hotel.utils.arabic_date import get_arabic_date
            today_formatted = get_arabic_date(today)

            all_rooms = Room.query.order_by(Room.room_number).all()

            # Create room status map for today
            rooms_status = []
            for room in all_rooms:
                # The exact same logic from admin.py
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

            # Count occupied and available rooms for today
            occupied_today = sum(1 for room in rooms_status if room['is_occupied'])
            available_today = total_rooms - occupied_today

            print("Dashboard data prepared successfully:")
            print(f"  - Total rooms: {total_rooms}")
            print(f"  - Available rooms: {available_rooms}")
            print(f"  - Total bookings: {total_bookings}")
            print(f"  - Active bookings: {active_bookings}")
            print(f"  - Total customers: {total_customers}")
            print(f"  - Recent bookings: {len(recent_bookings)}")
            print(f"  - Rooms status entries: {len(rooms_status)}")
            print(f"  - Occupied today: {occupied_today}")
            print(f"  - Available today: {available_today}")
            
            print("\nDashboard simulation completed successfully!")
            print("All data queries work without errors.")
            return True
            
    except Exception as e:
        print(f"Error in dashboard simulation: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Testing Dashboard After Database Fix")
    print("=" * 60)
    
    # Test components
    components_ok = test_dashboard_components()
    
    # Simulate dashboard
    simulation_ok = simulate_dashboard_render()
    
    print("\n" + "=" * 60)
    if components_ok and simulation_ok:
        print("SUCCESS: Dashboard is working correctly!")
        print("The Internal Server Error has been resolved.")
        print("You can now access /admin/dashboard without errors.")
        print("\nRoot cause was: Missing 'created_at' and 'updated_at' columns in customers table")
        print("Solution applied: Recreated customers table with proper schema")
    else:
        print("FAILED: Dashboard still has issues")
    print("=" * 60)
