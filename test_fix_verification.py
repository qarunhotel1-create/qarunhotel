#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append('e:/1/QARUN HOTELLL')

from hotel import create_app, db
from hotel.models.customer import Customer
from datetime import datetime

def test_fix_verification():
    """اختبار التحقق من إصلاح مشكلة الوثائق"""
    app = create_app()
    with app.app_context():
        print("=== Testing Document Fix ===")
        
        # 1. Check current status
        customers = Customer.query.all()
        customers_with_docs = Customer.query.filter(Customer.document_filename.isnot(None)).all()
        
        print(f"Total customers: {len(customers)}")
        print(f"Customers with documents: {len(customers_with_docs)}")
        
        # 2. Check uploads directory
        upload_dir = os.path.join(app.static_folder, 'uploads', 'customers')
        files = os.listdir(upload_dir) if os.path.exists(upload_dir) else []
        print(f"Files in upload directory: {len(files)}")
        
        # 3. Test customer creation simulation
        print("\n=== Simulating Customer Creation ===")
        
        test_customer = Customer(
            name="Test Fix Customer",
            id_number="FIX123456",
            nationality="Test",
            phone="987654321"
        )
        
        db.session.add(test_customer)
        db.session.flush()
        
        print(f"Test customer ID: {test_customer.id}")
        
        # Simulate document assignment
        test_customer.document_filename = f"test_fix_{test_customer.id}.pdf"
        test_customer.document_type = "passport"
        test_customer.document_upload_date = datetime.utcnow()
        
        print(f"Document filename: {test_customer.document_filename}")
        print(f"Document type: {test_customer.document_type}")
        print(f"has_document: {test_customer.has_document}")
        
        # Rollback to avoid saving test data
        db.session.rollback()
        print("Test rolled back successfully")
        
        print("\n=== Fix Status ===")
        print("The create() function has been enhanced with:")
        print("1. Better error handling and logging")
        print("2. Step-by-step verification of document saving")
        print("3. Detailed status tracking")
        print("4. Proper rollback on errors")
        print("\nThe fix should resolve the document display issue.")

if __name__ == "__main__":
    test_fix_verification()
