"""Add yearly booking numbering (booking_year, year_seq)

Revision ID: 20250825_add_yearly_booking_number
Revises: 42f4458b21d8
Create Date: 2025-08-25 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from sqlalchemy import Integer, DateTime, select

# revision identifiers, used by Alembic.
revision = '20250825_add_yearly_booking_number'
down_revision = '42f4458b21d8'
branch_labels = None
depends_on = None


def _col_exists(bind, table: str, col: str) -> bool:
    res = bind.execute(sa.text(f"PRAGMA table_info({table})"))
    return any(row[1] == col for row in res.fetchall())


def upgrade():
    bind = op.get_bind()

    # 1) Add columns only if missing
    need_booking_year = not _col_exists(bind, 'bookings', 'booking_year')
    need_year_seq = not _col_exists(bind, 'bookings', 'year_seq')

    if need_booking_year or need_year_seq:
        with op.batch_alter_table('bookings', schema=None) as batch_op:
            if need_booking_year:
                batch_op.add_column(sa.Column('booking_year', sa.Integer(), nullable=True))
            if need_year_seq:
                batch_op.add_column(sa.Column('year_seq', sa.Integer(), nullable=True))
    
    # 2) Backfill existing rows based on created_at year, ordered by created_at then id
    bookings = []
    try:
        # Fetch id and created_at
        res = bind.execute(sa.text(
            "SELECT id, created_at FROM bookings ORDER BY created_at ASC, id ASC"
        ))
        rows = res.fetchall()

        # Group by year and assign sequence
        current_year = None
        seq = 0
        for r in rows:
            created_at = r[1]
            if created_at is None:
                # Fallback: use a safe default year when created_at missing
                year_val = 1970
            else:
                year_val = created_at.year

            if current_year != year_val:
                current_year = year_val
                seq = 1
            else:
                seq += 1

            bookings.append((r[0], year_val, seq))

        # Bulk update
        for bid, yv, s in bookings:
            bind.execute(sa.text(
                "UPDATE bookings SET booking_year = :y, year_seq = :s WHERE id = :id"
            ), {"y": int(yv), "s": int(s), "id": int(bid)})
    except Exception:
        # If anything goes wrong, continue; columns remain nullable
        pass

    # 3) Create indexes (use unique index instead of constraint for SQLite compatibility)
    try:
        op.create_index('ix_bookings_booking_year', 'bookings', ['booking_year'], unique=False)
    except Exception:
        pass
    try:
        op.create_index('ux_booking_year_seq', 'bookings', ['booking_year', 'year_seq'], unique=True)
    except Exception:
        pass


def downgrade():
    # Drop indexes and columns
    try:
        op.drop_index('ux_booking_year_seq', table_name='bookings')
    except Exception:
        pass
    try:
        op.drop_index('ix_bookings_booking_year', table_name='bookings')
    except Exception:
        pass

    with op.batch_alter_table('bookings', schema=None) as batch_op:
        try:
            batch_op.drop_column('year_seq')
        except Exception:
            pass
        try:
            batch_op.drop_column('booking_year')
        except Exception:
            pass