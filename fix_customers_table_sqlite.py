#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix customers table for SQLite - recreate table with missing columns
"""

import os
import sys
from datetime import datetime

# Add project path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def fix_customers_table_sqlite():
    """Fix customers table by recreating it with proper structure"""
    print("Starting customers table fix for SQLite...")
    
    try:
        from hotel import create_app, db
        from hotel.models.customer import Customer
        
        app = create_app()
        
        with app.app_context():
            # Check current table structure
            print("Checking current customers table structure...")
            
            inspector = db.inspect(db.engine)
            columns = inspector.get_columns('customers')
            column_names = [col['name'] for col in columns]
            
            print(f"Current columns: {column_names}")
            
            # Check which columns are missing
            required_columns = ['created_at', 'updated_at']
            missing_columns = [col for col in required_columns if col not in column_names]
            
            if not missing_columns:
                print("All required columns already exist!")
                return True
            
            print(f"Missing columns: {missing_columns}")
            
            # SQLite approach: recreate table with proper structure
            print("Recreating customers table with proper structure...")
            
            with db.engine.connect() as conn:
                # Start transaction
                trans = conn.begin()
                
                try:
                    # Step 1: Create new table with correct structure
                    print("Creating new customers table...")
                    conn.execute(db.text("""
                        CREATE TABLE customers_new (
                            id INTEGER PRIMARY KEY,
                            name VARCHAR(100) NOT NULL,
                            id_number VARCHAR(20) UNIQUE NOT NULL,
                            nationality VARCHAR(50),
                            marital_status VARCHAR(20),
                            phone VARCHAR(20),
                            email VARCHAR(120),
                            address VARCHAR(200),
                            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                            document_filename VARCHAR(255),
                            document_original_name VARCHAR(255),
                            document_upload_date DATETIME
                        )
                    """))
                    
                    # Step 2: Copy data from old table to new table
                    print("Copying data from old table...")
                    current_time = datetime.utcnow().isoformat()
                    
                    conn.execute(db.text(f"""
                        INSERT INTO customers_new (
                            id, name, id_number, nationality, marital_status, 
                            phone, email, address, created_at, updated_at,
                            document_filename, document_upload_date
                        )
                        SELECT 
                            id, name, id_number, nationality, marital_status,
                            phone, email, address, 
                            '{current_time}' as created_at,
                            '{current_time}' as updated_at,
                            document_filename, document_upload_date
                        FROM customers
                    """))
                    
                    # Step 3: Drop old table
                    print("Dropping old table...")
                    conn.execute(db.text("DROP TABLE customers"))
                    
                    # Step 4: Rename new table
                    print("Renaming new table...")
                    conn.execute(db.text("ALTER TABLE customers_new RENAME TO customers"))
                    
                    # Commit transaction
                    trans.commit()
                    print("Transaction committed successfully!")
                    
                except Exception as e:
                    # Rollback on error
                    trans.rollback()
                    print(f"Error during table recreation, rolling back: {e}")
                    raise e
            
            # Verify the fix
            print("Verifying the fix...")
            inspector = db.inspect(db.engine)
            columns = inspector.get_columns('customers')
            column_names = [col['name'] for col in columns]
            
            print(f"Updated columns: {column_names}")
            
            # Test query
            customer_count = Customer.query.count()
            print(f"Customer count test: {customer_count}")
            
            print("Customers table fix completed successfully!")
            return True
            
    except Exception as e:
        print(f"Error fixing customers table: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_dashboard_after_fix():
    """Test dashboard functionality after fix"""
    print("\nTesting dashboard after fix...")
    
    try:
        from hotel import create_app, db
        from hotel.models import Customer, Room, Booking
        from datetime import date
        
        app = create_app()
        
        with app.app_context():
            # Test all the queries that were failing
            print("Testing customer count...")
            total_customers = Customer.query.count()
            print(f"Total customers: {total_customers}")
            
            print("Testing room count...")
            total_rooms = Room.query.count()
            print(f"Total rooms: {total_rooms}")
            
            print("Testing booking count...")
            total_bookings = Booking.query.count()
            print(f"Total bookings: {total_bookings}")
            
            print("Testing active bookings...")
            active_bookings = Booking.query.filter(
                Booking.status.in_(['pending', 'confirmed', 'checked_in'])
            ).count()
            print(f"Active bookings: {active_bookings}")
            
            print("Testing recent bookings...")
            recent_bookings = Booking.query.order_by(Booking.created_at.desc()).limit(5).all()
            print(f"Recent bookings: {len(recent_bookings)}")
            
            # Test arabic date
            print("Testing arabic date...")
            from hotel.utils.arabic_date import get_arabic_date
            today = date.today()
            today_formatted = get_arabic_date(today)
            print(f"Arabic date: {today_formatted}")
            
            # Test room status logic (simplified)
            print("Testing room status logic...")
            all_rooms = Room.query.order_by(Room.room_number).limit(3).all()
            rooms_tested = 0
            
            for room in all_rooms:
                try:
                    # Test booking queries for this room
                    normal_booking = Booking.query.filter(
                        Booking.room_id == room.id,
                        Booking.check_in_date <= date.today(),
                        Booking.check_out_date > date.today(),
                        Booking.is_deus == False,
                        Booking.status.in_(['confirmed', 'checked_in'])
                    ).first()
                    
                    deus_booking = Booking.query.filter(
                        Booking.room_id == room.id,
                        Booking.check_in_date <= date.today(),
                        Booking.check_out_date >= date.today(),
                        Booking.is_deus == True,
                        Booking.status == 'checked_in'
                    ).first()
                    
                    active_booking = normal_booking or deus_booking
                    rooms_tested += 1
                    
                except Exception as e:
                    print(f"Error testing room {room.room_number}: {e}")
                    return False
            
            print(f"Successfully tested {rooms_tested} rooms")
            
            print("All dashboard tests passed!")
            return True
            
    except Exception as e:
        print(f"Error in dashboard test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Fixing Customers Table for SQLite")
    print("=" * 60)
    
    # Fix the table
    fix_success = fix_customers_table_sqlite()
    
    if fix_success:
        # Test dashboard
        test_success = test_dashboard_after_fix()
        
        print("\n" + "=" * 60)
        if test_success:
            print("SUCCESS: Customers table fixed and dashboard working!")
            print("The Internal Server Error should now be resolved.")
            print("You can now access /admin/dashboard without errors.")
        else:
            print("PARTIAL: Table fixed but dashboard still has issues.")
    else:
        print("FAILED: Could not fix customers table.")
    
    print("=" * 60)
