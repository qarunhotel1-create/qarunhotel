#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix customers table - add missing columns
"""

import os
import sys
from datetime import datetime

# Add project path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def fix_customers_table():
    """Add missing columns to customers table"""
    print("Starting customers table fix...")
    
    try:
        from hotel import create_app, db
        from hotel.models.customer import Customer
        
        app = create_app()
        
        with app.app_context():
            # Check current table structure
            print("Checking current customers table structure...")
            
            # Get table info
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
            
            # Add missing columns using raw SQL
            print("Adding missing columns...")
            
            if 'created_at' in missing_columns:
                print("Adding created_at column...")
                with db.engine.connect() as conn:
                    conn.execute(db.text("""
                        ALTER TABLE customers 
                        ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    """))
                    
                    # Update existing records with current timestamp
                    conn.execute(db.text("""
                        UPDATE customers 
                        SET created_at = CURRENT_TIMESTAMP 
                        WHERE created_at IS NULL
                    """))
                    conn.commit()
            
            if 'updated_at' in missing_columns:
                print("Adding updated_at column...")
                with db.engine.connect() as conn:
                    conn.execute(db.text("""
                        ALTER TABLE customers 
                        ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    """))
                    
                    # Update existing records with current timestamp
                    conn.execute(db.text("""
                        UPDATE customers 
                        SET updated_at = CURRENT_TIMESTAMP 
                        WHERE updated_at IS NULL
                    """))
                    conn.commit()
            
            # Commit changes
            db.session.commit()
            
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
            
            print("All dashboard tests passed!")
            return True
            
    except Exception as e:
        print(f"Error in dashboard test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("Fixing Customers Table - Missing Columns")
    print("=" * 60)
    
    # Fix the table
    fix_success = fix_customers_table()
    
    if fix_success:
        # Test dashboard
        test_success = test_dashboard_after_fix()
        
        print("\n" + "=" * 60)
        if test_success:
            print("SUCCESS: Customers table fixed and dashboard working!")
            print("The Internal Server Error should now be resolved.")
        else:
            print("PARTIAL: Table fixed but dashboard still has issues.")
    else:
        print("FAILED: Could not fix customers table.")
    
    print("=" * 60)
