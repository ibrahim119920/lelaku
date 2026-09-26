"""Add vehicles after the LL-05 auth/profile/session schema.

Revision ID: 20260924_0002_vehicles
Revises: 20260923_0001
"""

from alembic import op
import sqlalchemy as sa


revision = "20260924_0002_vehicles"
down_revision = "20260923_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "vehicles",
        sa.Column("vehicle_id", sa.Uuid(), nullable=False),
        sa.Column("driver_id", sa.Text(), nullable=False),
        sa.Column("type", sa.String(length=32), nullable=False),
        sa.Column("brand", sa.String(length=64), nullable=False),
        sa.Column("model", sa.String(length=64), nullable=False),
        sa.Column("plate_number", sa.String(length=32), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["driver_id"],
            ["users.user_id"],
            name="fk_vehicles_driver_id_users",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("vehicle_id", name="pk_vehicles"),
        sa.UniqueConstraint("plate_number", name="uq_vehicles_plate_number"),
    )
    op.create_index("ix_vehicles_driver_id", "vehicles", ["driver_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_vehicles_driver_id", table_name="vehicles")
    op.drop_table("vehicles")
