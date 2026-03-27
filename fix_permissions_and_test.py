#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix for permissions and booking confirmation button
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from hotel import create_app, db
from hotel.models import User, Permission, Booking

def fix_permissions():
    """Fix user permissions and add missing permissions"""
    app = create_app()
    
    with app.app_context():
        print("Starting permissions fix...")
        
        # Check for edit_booking permission
        edit_booking_perm = Permission.query.filter_by(name='edit_booking').first()
        if not edit_booking_perm:
            edit_booking_perm = Permission(name='edit_booking', description='Edit bookings')
            db.session.add(edit_booking_perm)
            print("Created edit_booking permission")
        
        # Check for manage_bookings permission
        manage_bookings_perm = Permission.query.filter_by(name='manage_bookings').first()
        if not manage_bookings_perm:
            manage_bookings_perm = Permission(name='manage_bookings', description='Manage bookings')
            db.session.add(manage_bookings_perm)
            print("Created manage_bookings permission")
        
        # Add permissions to all active users (except guests)
        users = User.query.filter_by(is_guest=False).all()
        
        for user in users:
            # Add edit_booking permission if not exists
            if edit_booking_perm not in user.permissions:
                user.permissions.append(edit_booking_perm)
                print(f"Added edit_booking permission to user: {user.username}")
            
            # Add manage_bookings permission for managers
            if user.username in ['admin', 'manager', 'receptionist']:
                if manage_bookings_perm not in user.permissions:
                    user.permissions.append(manage_bookings_perm)
                    print(f"Added manage_bookings permission to user: {user.username}")
        
        # Save changes
        db.session.commit()
        print("Saved all changes to database")
        
        # Test permissions
        print("\nTesting current permissions:")
        for user in users:
            print(f"User {user.username} ({user.full_name}):")
            print(f"   - can_edit_booking: {user.can_edit_booking()}")
            print(f"   - has manage_bookings: {user.has_permission('manage_bookings')}")
            print(f"   - has edit_booking: {user.has_permission('edit_booking')}")
            print()

def test_arabic_text():
    """Test Arabic text processing"""
    print("Testing Arabic text processing...")
    
    import arabic_reshaper
    from bidi.algorithm import get_display
    
    test_texts = [
        "مرحباً بكم في فندق قارون",
        "تقرير الحجوزات - 2024",
        "العميل: أحمد محمد",
        "Room 101 - غرفة رقم 101",
        "Total: 1500 جنيه"
    ]
    
    for text in test_texts:
        print(f"Original: {text}")
        
        # Current method (improved)
        has_arabic = any('\u0600' <= char <= '\u06FF' for char in text)
        if has_arabic:
            reshaped = arabic_reshaper.reshape(text, configuration={
                'delete_harakat': False,
                'support_zwj': True,
                'use_unshaped_instead_of_isolated': False
            })
            bidi_text = get_display(reshaped, base_dir='R')
            print(f"Processed: {bidi_text}")
        else:
            print(f"Processed: {text}")
        print("-" * 50)

def test_booking_confirmation():
    """Test booking confirmation functionality"""
    app = create_app()
    
    with app.app_context():
        print("Testing pending bookings...")
        
        pending_bookings = Booking.query.filter_by(status='pending').all()
        print(f"Number of pending bookings: {len(pending_bookings)}")
        
        for booking in pending_bookings[:3]:  # First 3 bookings only
            customer_name = booking.customer.name if booking.customer else 'Not specified'
            print(f"Booking #{booking.id} - Customer: {customer_name}")
            print(f"   Status: {booking.status}")
            print(f"   Created: {booking.created_at}")

if __name__ == "__main__":
    print("Starting radical fix for problems...")
    print("=" * 60)
    
    # Fix permissions
    fix_permissions()
    
    print("\n" + "=" * 60)
    
    # Test Arabic text
    test_arabic_text()
    
    print("\n" + "=" * 60)
    
    # Test bookings
    test_booking_confirmation()
    
    print("\nRadical fix completed!")
    print("Please restart the server to apply changes")
