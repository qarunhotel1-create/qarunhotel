# -*- coding: utf-8 -*-
import sys
import os
from hotel import create_app, db
from hotel.models import Customer

app = create_app()
with app.app_context():
    customers = Customer.query.all()
    print(f'Total customers: {len(customers)}')
    
    for c in customers:
        doc_status = c.document_filename if c.document_filename else "No document"
        try:
            print(f'Customer {c.id}: {c.name.encode("utf-8", "ignore").decode("utf-8")} - Document: {doc_status}')
        except:
            print(f'Customer {c.id}: [Name encoding issue] - Document: {doc_status}')
