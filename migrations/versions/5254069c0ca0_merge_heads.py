"""merge heads

Revision ID: 5254069c0ca0
Revises: 20250825_add_yearly_booking_number, 41534446f7ee, add_gender_field
Create Date: 2025-08-26 00:52:02.642533

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5254069c0ca0'
down_revision = ('20250825_add_yearly_booking_number', '41534446f7ee', 'add_gender_field')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
