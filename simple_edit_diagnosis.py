#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hotel import create_app, db
from hotel.models import Customer
from hotel.forms.customer import CustomerForm
import traceback

def diagnose_edit_error():
    print("Starting diagnosis...")
    
    try:
        app = create_app()
        
        with app.app_context():
            print("\n1. Checking database...")
            
            # Check customers table
            try:
                customer_count = Customer.query.count()
                print(f"Customers table exists - count: {customer_count}")
            except Exception as e:
                print(f"ERROR in customers table: {str(e)}")
                traceback.print_exc()
                return False
            
            # Check first customer
            if customer_count > 0:
                try:
                    first_customer = Customer.query.first()
                    print(f"First customer: {first_customer.name} (ID: {first_customer.id})")
                    
                    # Check required fields
                    required_fields = ['name', 'id_number', 'nationality', 'created_at', 'updated_at']
                    for field in required_fields:
                        if hasattr(first_customer, field):
                            value = getattr(first_customer, field)
                            print(f"   - {field}: {value}")
                        else:
                            print(f"MISSING field: {field}")
                            
                except Exception as e:
                    print(f"ERROR reading customer data: {str(e)}")
                    traceback.print_exc()
                    return False
            
            print("\n2. Checking CustomerForm...")
            
            # Test creating empty form
            try:
                form = CustomerForm()
                print("Empty form created successfully")
            except Exception as e:
                print(f"ERROR creating empty form: {str(e)}")
                traceback.print_exc()
                return False
            
            # Test creating form with customer data
            if customer_count > 0:
                try:
                    customer = Customer.query.first()
                    form_with_data = CustomerForm(obj=customer)
                    print("Form with customer data created successfully")
                    
                    # Check loaded data
                    print(f"   - Name: {form_with_data.name.data}")
                    print(f"   - ID Number: {form_with_data.id_number.data}")
                    print(f"   - Nationality: {form_with_data.nationality.data}")
                    
                except Exception as e:
                    print(f"ERROR creating form with customer data: {str(e)}")
                    traceback.print_exc()
                    return False
            
            print("\n3. Checking edit template...")
            
            # Check template file exists
            template_path = os.path.join("hotel", "templates", "customer", "edit.html")
            if os.path.exists(template_path):
                print("Template file exists")
            else:
                print(f"Template file missing: {template_path}")
                return False
            
            print("\n4. Testing GET request to edit page...")
            
            # Try to simulate request
            try:
                with app.test_client() as client:
                    if customer_count > 0:
                        customer = Customer.query.first()
                        response = client.get(f'/customers/{customer.id}/edit')
                        print(f"   - Response code: {response.status_code}")
                        
                        if response.status_code == 302:
                            print("   - Redirected (probably to login page)")
                        elif response.status_code == 500:
                            print("CONFIRMED: Internal Server Error")
                            print(f"   - Response content: {response.data.decode('utf-8')[:200]}...")
                        else:
                            print("Page works normally")
                    else:
                        print("No customers to test with")
                        
            except Exception as e:
                print(f"ERROR in request simulation: {str(e)}")
                traceback.print_exc()
                return False
            
            print("\n5. Checking users and permissions...")
            
            # Check users table
            try:
                from hotel.models import User
                user_count = User.query.count()
                print(f"Users count: {user_count}")
                
                if user_count > 0:
                    admin_user = User.query.filter_by(is_admin=True).first()
                    if admin_user:
                        print(f"Admin user exists: {admin_user.username}")
                    else:
                        print("No admin user found")
                        
            except Exception as e:
                print(f"ERROR checking users: {str(e)}")
                # Not critical error
            
            print("\nDiagnosis complete. If no clear errors shown, the problem might be in:")
            print("   1. Template edit.html issues")
            print("   2. Permissions or login issues")
            print("   3. Flask configuration issues")
            print("   4. Missing database fields")
            
            return True
            
    except Exception as e:
        print(f"GENERAL ERROR in diagnosis: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == '__main__':
    diagnose_edit_error()
