#!/usr/bin/env python3
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hotel import create_app, db
from hotel.models import Customer
from hotel.forms.customer import CustomerForm
from werkzeug.datastructures import FileStorage
import io
import tempfile

def test_real_customer_creation():
    """Test the actual customer creation process using the form"""
    
    app = create_app()
    
    with app.app_context():
        print("TESTING REAL CUSTOMER CREATION PROCESS...")
        print("=" * 50)
        
        # Count customers before
        customers_before = Customer.query.count()
        customers_with_docs_before = Customer.query.filter(Customer.document_filename.isnot(None)).count()
        print(f"Customers before: {customers_before}")
        print(f"Customers with docs before: {customers_with_docs_before}")
        
        # Create test image content
        test_image_content = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\nIDATx\x9cc\xf8\x00\x00\x00\x01\x00\x01\x00\x00\x00\x00IEND\xaeB`\x82'
        
        # Create a file-like object
        file_obj = io.BytesIO(test_image_content)
        file_storage = FileStorage(
            stream=file_obj,
            filename='test_document.png',
            content_type='image/png'
        )
        
        # Create form data
        form_data = {
            'name': 'Real Test Customer',
            'id_number': 'REAL123456',
            'phone': '01111111111',
            'nationality': 'مصري',
            'marital_status': 'أعزب',
            'address': 'Test Address',
            'document_type': 'id_card'
        }
        
        # Create form with file (disable CSRF for testing)
        app.config['WTF_CSRF_ENABLED'] = False
        with app.test_request_context(method='POST', data=form_data):
            form = CustomerForm()
            
            # Manually populate form
            form.name.data = form_data['name']
            form.id_number.data = form_data['id_number']
            form.phone.data = form_data['phone']
            form.nationality.data = form_data['nationality']
            form.marital_status.data = form_data['marital_status']
            form.address.data = form_data['address']
            form.document_type.data = form_data['document_type']
            form.document_file.data = file_storage
            
            print(f"Form name: {form.name.data}")
            print(f"Form id_number: {form.id_number.data}")
            print(f"Form document_type: {form.document_type.data}")
            print(f"Form document_file: {form.document_file.data}")
            print(f"Form document_file filename: {form.document_file.data.filename if form.document_file.data else 'None'}")
            
            # Test form validation
            is_valid = form.validate()
            print(f"Form is valid: {is_valid}")
            if not is_valid:
                print(f"Form errors: {form.errors}")
            
            # Test the actual create logic
            if is_valid:
                try:
                    # Create customer
                    customer = Customer(
                        name=form.name.data,
                        id_number=form.id_number.data,
                        phone=form.phone.data,
                        nationality=form.nationality.data,
                        marital_status=form.marital_status.data,
                        address=form.address.data
                    )
                    db.session.add(customer)
                    db.session.flush()
                    
                    print(f"Customer created with ID: {customer.id}")
                    
                    # Test document handling
                    document_saved = False
                    if form.document_file.data and form.document_file.data.filename != '':
                        print("Processing document...")
                        
                        file = form.document_file.data
                        print(f"File: {file}")
                        print(f"Filename: {file.filename}")
                        
                        # Check file type
                        allowed_extensions = {'pdf', 'png', 'jpg', 'jpeg', 'gif'}
                        if '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed_extensions:
                            print("File type is allowed")
                            
                            # Create filename
                            import uuid
                            from werkzeug.utils import secure_filename
                            ext = os.path.splitext(file.filename)[1].lower()
                            filename = f'document_{customer.id}_{uuid.uuid4().hex}{ext}'
                            filename = secure_filename(filename)
                            print(f"Generated filename: {filename}")
                            
                            # Create upload directory
                            upload_dir = os.path.join(app.static_folder, 'uploads', 'customers')
                            os.makedirs(upload_dir, exist_ok=True)
                            print(f"Upload directory: {upload_dir}")
                            
                            # Save file
                            file_path = os.path.join(upload_dir, filename)
                            file.save(file_path)
                            print(f"File saved to: {file_path}")
                            
                            # Check if file exists
                            if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                                print("File saved successfully!")
                                
                                # Update customer
                                customer.document_filename = filename
                                customer.document_type = form.document_type.data or 'other'
                                from datetime import datetime
                                customer.document_upload_date = datetime.utcnow()
                                document_saved = True
                                print("Customer updated with document info")
                            else:
                                print("ERROR: File was not saved properly!")
                        else:
                            print("ERROR: File type not allowed!")
                    else:
                        print("No document file provided")
                    
                    db.session.commit()
                    print("Database committed")
                    
                    print(f"Document saved: {document_saved}")
                    print(f"Customer has_document: {customer.has_document}")
                    
                except Exception as e:
                    db.session.rollback()
                    print(f"ERROR: {str(e)}")
                    import traceback
                    traceback.print_exc()
        
        # Check results
        customers_after = Customer.query.count()
        customers_with_docs_after = Customer.query.filter(Customer.document_filename.isnot(None)).count()
        print(f"Customers after: {customers_after}")
        print(f"Customers with docs after: {customers_with_docs_after}")
        
        print("\n" + "=" * 50)
        print("TEST COMPLETE")

if __name__ == '__main__':
    test_real_customer_creation()
