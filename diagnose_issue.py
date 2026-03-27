#!/usr/bin/env python3
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hotel import create_app, db
from hotel.models import Customer
from datetime import datetime

def diagnose_customer_document_issue():
    app = create_app()
    
    with app.app_context():
        print("DIAGNOSING CUSTOMER DOCUMENT ISSUE...")
        print("=" * 50)
        
        # Check all customers
        all_customers = Customer.query.all()
        print(f"Total customers in database: {len(all_customers)}")
        
        # Check customers with documents
        customers_with_docs = Customer.query.filter(Customer.document_filename.isnot(None)).all()
        print(f"Customers with documents: {len(customers_with_docs)}")
        
        # Check customers without documents
        customers_without_docs = Customer.query.filter(Customer.document_filename.is_(None)).all()
        print(f"Customers without documents: {len(customers_without_docs)}")
        
        print("\nCUSTOMERS WITH DOCUMENTS:")
        for i, customer in enumerate(customers_with_docs, 1):
            print(f"{i}. Customer ID: {customer.id}")
            print(f"   Document filename: {customer.document_filename}")
            print(f"   Document type: {customer.document_type}")
            print(f"   Upload date: {customer.document_upload_date}")
            print(f"   has_document property: {customer.has_document}")
            
            # Check if file exists
            if customer.document_filename:
                file_path = os.path.join(app.static_folder, 'uploads', 'customers', customer.document_filename)
                file_exists = os.path.exists(file_path)
                print(f"   File exists on disk: {file_exists}")
                if file_exists:
                    file_size = os.path.getsize(file_path)
                    print(f"   File size: {file_size} bytes")
            print()
        
        print("CUSTOMERS WITHOUT DOCUMENTS:")
        for i, customer in enumerate(customers_without_docs, 1):
            print(f"{i}. Customer ID: {customer.id}")
            print(f"   Document filename: {customer.document_filename}")
            print(f"   Document type: {customer.document_type}")
            print()
        
        # Check upload directory
        upload_dir = os.path.join(app.static_folder, 'uploads', 'customers')
        print(f"Upload directory: {upload_dir}")
        print(f"Directory exists: {os.path.exists(upload_dir)}")
        
        if os.path.exists(upload_dir):
            files = os.listdir(upload_dir)
            print(f"Files in upload directory: {len(files)}")
            for file in files:
                file_path = os.path.join(upload_dir, file)
                file_size = os.path.getsize(file_path)
                print(f"  - {file} ({file_size} bytes)")
        
        print("\n" + "=" * 50)
        print("DIAGNOSIS COMPLETE")

if __name__ == '__main__':
    diagnose_customer_document_issue()
