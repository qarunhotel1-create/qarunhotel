"""Add check in out times

Revision ID: add_check_in_out_times
Revises: 
Create Date: 2025-08-19 10:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'add_check_in_out_times'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Add check_in_time and check_out_time columns to bookings table
    with op.batch_alter_table('bookings', schema=None) as batch_op:
        batch_op.add_column(sa.Column('check_in_time', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('check_out_time', sa.DateTime(), nullable=True))
    
    # Create an index for better query performance
    op.create_index(op.f('ix_bookings_check_in_time'), 'bookings', ['check_in_time'], unique=False)
    op.create_index(op.f('ix_bookings_check_out_time'), 'bookings', ['check_out_time'], unique=False)

def downgrade():
    # Drop the indexes first
    op.drop_index(op.f('ix_bookings_check_out_time'), table_name='bookings')
    op.drop_index(op.f('ix_bookings_check_in_time'), table_name='bookings')
    
    # Drop the columns
    with op.batch_alter_table('bookings', schema=None) as batch_op:
        batch_op.drop_column('check_out_time')
        batch_op.drop_column('check_in_time')
