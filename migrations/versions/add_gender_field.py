"""add gender field

Revision ID: add_gender_field
Revises: 
Create Date: 2023-11-15

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_gender_field'
down_revision = '42f4458b21d8'
branch_labels = None
depends_on = None


def _column_exists(bind, table_name: str, column_name: str) -> bool:
    """Check if a column exists in an SQLite table using PRAGMA."""
    res = bind.execute(sa.text(f"PRAGMA table_info({table_name})"))
    return any(row[1] == column_name for row in res.fetchall())


def upgrade():
    # إضافة حقل الجنس إلى جدول العملاء بشكل آمن (يتجنب التكرار إن كان العمود موجودًا)
    bind = op.get_bind()
    if not _column_exists(bind, 'customers', 'gender'):
        op.add_column('customers', sa.Column('gender', sa.String(10), nullable=True))


def downgrade():
    # حذف حقل الجنس من جدول العملاء إن وُجد
    bind = op.get_bind()
    if _column_exists(bind, 'customers', 'gender'):
        op.drop_column('customers', 'gender')