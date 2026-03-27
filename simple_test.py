#!/usr/bin/env python3
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hotel import create_app, db
from hotel.models import Customer

def test_customer_documents():
    app = create_app()
    
    with app.app_context():
        print("Testing customer documents...")
        
        # Check all customers
        all_customers = Customer.query.all()
        print(f"Total customers: {len(all_customers)}")
        
        # Check customers with documents
        customers_with_docs = Customer.query.filter(Customer.document_filename.isnot(None)).all()
        print(f"Customers with documents: {len(customers_with_docs)}")
        
        # Show details
        for customer in customers_with_docs:
            print(f"ID: {customer.id}, Name: {customer.name}")
            print(f"Document filename: {customer.document_filename}")
            print(f"Document type: {customer.document_type}")
            print(f"Has document: {customer.has_document}")
            print(f"Document URL: {customer.document_url}")
            print("---")
        
        # Check upload directory
        upload_dir = os.path.join(app.static_folder, 'uploads', 'customers')
        print(f"Upload directory: {upload_dir}")
        print(f"Directory exists: {os.path.exists(upload_dir)}")
        
        if os.path.exists(upload_dir):
            files = os.listdir(upload_dir)
            print(f"Files in directory: {len(files)}")
            for file in files[:5]:
                print(f"  - {file}")

if __name__ == '__main__':
    test_customer_documents()

print("🎉 الاختبار البسيط مكتمل")
