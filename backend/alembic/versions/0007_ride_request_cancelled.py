"""ride request cancelled status

Revision ID: 0007
Revises: 0006
Create Date: 2026-11-28
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint(op.f("ck_ride_requests_status_valid"), "ride_requests", type_="check")
    op.create_check_constraint(
        op.f("ck_ride_requests_status_valid"),
        "ride_requests",
        "status IN ('pending', 'accepted', 'rejected', 'cancelled')",
    )


def downgrade() -> None:
    op.execute("UPDATE ride_requests SET status = 'rejected' WHERE status = 'cancelled'")
    op.drop_constraint(op.f("ck_ride_requests_status_valid"), "ride_requests", type_="check")
    op.create_check_constraint(
        op.f("ck_ride_requests_status_valid"),
        "ride_requests",
        "status IN ('pending', 'accepted', 'rejected')",
    )
