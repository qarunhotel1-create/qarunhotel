"""merge multiple heads

Revision ID: 42f4458b21d8
Revises: add_check_in_out_times, add_customer_documents, fix_room_transfers
Create Date: 2025-08-19 10:49:13.743764

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '42f4458b21d8'
down_revision = ('add_check_in_out_times', 'add_customer_documents', 'fix_room_transfers')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
