"""Fix room_transfers table structure

Revision ID: fix_room_transfers
Revises: 7f0357e763a2
Create Date: 2025-08-05 04:55:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = 'fix_room_transfers'
down_revision = '7f0357e763a2'
branch_labels = None
depends_on = None

def upgrade():
    # Check if room_transfers table exists
    conn = op.get_bind()
    
    # Check if table exists
    result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='room_transfers'"))
    table_exists = result.fetchone() is not None
    
    if not table_exists:
        # Create the table if it doesn't exist
        op.create_table('room_transfers',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('booking_id', sa.Integer(), nullable=False),
            sa.Column('from_room_id', sa.Integer(), nullable=False),
            sa.Column('to_room_id', sa.Integer(), nullable=False),
            sa.Column('transfer_time', sa.DateTime(), nullable=False),
            sa.Column('transferred_by_user_id', sa.Integer(), nullable=False),
            sa.Column('reason', sa.Text(), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.ForeignKeyConstraint(['booking_id'], ['bookings.id'], ),
            sa.ForeignKeyConstraint(['from_room_id'], ['rooms.id'], ),
            sa.ForeignKeyConstraint(['to_room_id'], ['rooms.id'], ),
            sa.ForeignKeyConstraint(['transferred_by_user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
    else:
        # Check existing columns
        result = conn.execute(text("PRAGMA table_info(room_transfers)"))
        columns = [row[1] for row in result.fetchall()]
        
        # Add missing columns
        if 'transfer_time' not in columns:
            op.add_column('room_transfers', sa.Column('transfer_time', sa.DateTime(), nullable=True))
            # Update existing records with current time
            conn.execute(text("UPDATE room_transfers SET transfer_time = datetime('now') WHERE transfer_time IS NULL"))
        
        if 'transferred_by_user_id' not in columns:
            op.add_column('room_transfers', sa.Column('transferred_by_user_id', sa.Integer(), nullable=True))
            # Set default user ID for existing records
            conn.execute(text("UPDATE room_transfers SET transferred_by_user_id = 1 WHERE transferred_by_user_id IS NULL"))
        
        if 'reason' not in columns:
            op.add_column('room_transfers', sa.Column('reason', sa.Text(), nullable=True))
        
        if 'notes' not in columns:
            op.add_column('room_transfers', sa.Column('notes', sa.Text(), nullable=True))

def downgrade():
    # Remove the columns we added
    with op.batch_alter_table('room_transfers', schema=None) as batch_op:
        batch_op.drop_column('notes')
        batch_op.drop_column('reason')
        batch_op.drop_column('transferred_by_user_id')
        batch_op.drop_column('transfer_time')
