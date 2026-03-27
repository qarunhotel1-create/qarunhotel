#!/usr/bin/env python3
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hotel import create_app, db
from hotel.models import Customer
from datetime import datetime
import tempfile
from werkzeug.datastructures import FileStorage
import io

def test_create_customer_with_document():
    app = create_app()
    
    with app.app_context():
        print("TESTING CREATE CUSTOMER WITH DOCUMENT...")
        print("=" * 50)
        
        # Count customers before
        customers_before = Customer.query.count()
        print(f"Customers before test: {customers_before}")
        
        # Create a test image file in memory
        test_image_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\nIDATx\x9cc\xf8\x00\x00\x00\x01\x00\x01\x00\x00\x00\x00IEND\xaeB`\x82'
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            temp_file.write(test_image_content)
            temp_file_path = temp_file.name
        
        try:
            # Create test customer directly using model
            test_customer = Customer(
                name='Test Customer With Document',
                id_number='TEST999999',
                phone='01111111111',
                nationality='Egyptian'
            )
            db.session.add(test_customer)
            db.session.flush()  # Get customer ID
            
            # Simulate document upload
            with open(temp_file_path, 'rb') as f:
                file_content = f.read()
            
            # Create upload directory
            upload_dir = os.path.join(app.static_folder, 'uploads', 'customers')
            os.makedirs(upload_dir, exist_ok=True)
            
            # Save document file
            import uuid
            from werkzeug.utils import secure_filename
            filename = f'document_{test_customer.id}_{uuid.uuid4().hex}.png'
            filename = secure_filename(filename)
            file_path = os.path.join(upload_dir, filename)
            
            with open(file_path, 'wb') as f:
                f.write(file_content)
            
            # Update customer with document info
            test_customer.document_filename = filename
            test_customer.document_type = 'id_card'
            test_customer.document_upload_date = datetime.utcnow()
            
            db.session.commit()
            
            print(f"Created test customer ID: {test_customer.id}")
            print(f"Document filename: {test_customer.document_filename}")
            print(f"Document type: {test_customer.document_type}")
            print(f"Has document: {test_customer.has_document}")
            
            # Verify file exists
            file_exists = os.path.exists(file_path)
            print(f"Document file exists: {file_exists}")
            if file_exists:
                file_size = os.path.getsize(file_path)
                print(f"Document file size: {file_size} bytes")
            
        finally:
            # Clean up temp file
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
        
        # Count customers after
        customers_after = Customer.query.count()
        customers_with_docs = Customer.query.filter(Customer.document_filename.isnot(None)).count()
        
        print(f"Customers after test: {customers_after}")
        print(f"Customers with documents: {customers_with_docs}")
        
        print("\n" + "=" * 50)
        print("TEST COMPLETE")

if __name__ == '__main__':
    test_create_customer_with_document()
