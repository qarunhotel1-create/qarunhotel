"""Add customer documents table

Revision ID: add_customer_documents
Revises: 
Create Date: 2025-01-11 02:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = 'add_customer_documents'
down_revision = None  # Replace with actual previous revision ID if needed
branch_labels = None
depends_on = None


def upgrade():
    # إنشاء جدول الوثائق الجديد
    op.create_table('customer_documents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('customer_id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('original_filename', sa.String(length=255), nullable=False),
        sa.Column('document_type', sa.String(length=50), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('upload_date', sa.DateTime(), nullable=True),
        sa.Column('is_primary', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['customer_id'], ['customers.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # إنشاء فهرس على customer_id لتحسين الأداء
    op.create_index(op.f('ix_customer_documents_customer_id'), 'customer_documents', ['customer_id'], unique=False)
    
    # نقل البيانات الموجودة من جدول العملاء إلى جدول الوثائق الجديد
    # هذا سيحافظ على الوثائق الموجودة
    connection = op.get_bind()
    
    # البحث عن العملاء الذين لديهم وثائق
    result = connection.execute(sa.text("""
        SELECT id, document_filename, document_type, document_upload_date 
        FROM customers 
        WHERE document_filename IS NOT NULL AND document_filename != ''
    """))
    
    # نقل كل وثيقة إلى الجدول الجديد
    for row in result:
        customer_id, filename, doc_type, upload_date = row
        
        # تقدير حجم الملف إذا كان الملف موجوداً
        import os
        from flask import current_app
        
        file_size = None
        try:
            if current_app:
                file_path = os.path.join(current_app.static_folder, 'uploads', 'customers', filename)
                if os.path.exists(file_path):
                    file_size = os.path.getsize(file_path)
        except:
            pass  # تجاهل الأخطاء في حساب حجم الملف
        
        # إدراج الوثيقة في الجدول الجديد
        connection.execute(sa.text("""
            INSERT INTO customer_documents 
            (customer_id, filename, original_filename, document_type, file_size, upload_date, is_primary)
            VALUES (:customer_id, :filename, :original_filename, :document_type, :file_size, :upload_date, :is_primary)
        """), {
            'customer_id': customer_id,
            'filename': filename,
            'original_filename': filename,  # نفس اسم الملف كاسم أصلي
            'document_type': doc_type or 'other',
            'file_size': file_size,
            'upload_date': upload_date or datetime.utcnow(),
            'is_primary': True  # الوثيقة الموجودة تصبح أساسية
        })


def downgrade():
    # حذف الفهرس
    op.drop_index(op.f('ix_customer_documents_customer_id'), table_name='customer_documents')
    
    # حذف جدول الوثائق
    op.drop_table('customer_documents')
