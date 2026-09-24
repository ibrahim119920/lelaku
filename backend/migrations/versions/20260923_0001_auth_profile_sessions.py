"""Initialize the LL-05 auth, profile, and session schema.

Revision ID: 20260923_0001
Revises:
Create Date: 2026-09-23
"""

from alembic import op
import sqlalchemy as sa


revision = "20260923_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("user_id", sa.Text(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("phone", sa.Text(), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("profile_photo", sa.Text(), nullable=True),
        sa.Column(
            "identity_status",
            sa.Text(),
            server_default="unverified",
            nullable=False,
        ),
        sa.Column("avg_rating", sa.Numeric(), nullable=True),
        sa.Column("total_ratings", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "total_trips_completed",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
        sa.CheckConstraint(
            "identity_status IN ('verified', 'unverified')",
            name="ck_users_identity_status",
        ),
        sa.CheckConstraint("total_ratings >= 0", name="ck_users_total_ratings_nonnegative"),
        sa.CheckConstraint(
            "total_trips_completed >= 0",
            name="ck_users_total_trips_nonnegative",
        ),
        sa.PrimaryKeyConstraint("user_id", name="pk_users"),
    )
    op.create_index(
        "uq_users_email_lower",
        "users",
        [sa.text("lower(email)")],
        unique=True,
    )

    op.create_table(
        "driver_profiles",
        sa.Column("user_id", sa.Text(), nullable=False),
        sa.Column("document_url", sa.Text(), nullable=True),
        sa.Column("verification_status", sa.Text(), nullable=False),
        sa.Column("avg_rating_driver", sa.Numeric(), nullable=True),
        sa.Column(
            "total_ratings_driver", sa.Integer(), server_default="0", nullable=False
        ),
        sa.Column(
            "total_trips_as_driver", sa.Integer(), server_default="0", nullable=False
        ),
        sa.CheckConstraint(
            "total_ratings_driver >= 0",
            name="ck_driver_profiles_total_ratings_nonnegative",
        ),
        sa.CheckConstraint(
            "total_trips_as_driver >= 0",
            name="ck_driver_profiles_total_trips_nonnegative",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.user_id"],
            ondelete="CASCADE",
            name="fk_driver_profiles_user_id_users",
        ),
        sa.PrimaryKeyConstraint("user_id", name="pk_driver_profiles"),
    )

    op.create_table(
        "user_sessions",
        sa.Column("session_token_hash", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "expires_at > created_at",
            name="ck_user_sessions_expiry_after_creation",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.user_id"],
            ondelete="CASCADE",
            name="fk_user_sessions_user_id_users",
        ),
        sa.PrimaryKeyConstraint("session_token_hash", name="pk_user_sessions"),
    )
    op.create_index(
        "ix_user_sessions_user_id_expires_at",
        "user_sessions",
        ["user_id", "expires_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_user_sessions_user_id_expires_at", table_name="user_sessions")
    op.drop_table("user_sessions")
    op.drop_table("driver_profiles")
    op.drop_index("uq_users_email_lower", table_name="users")
    op.drop_table("users")
