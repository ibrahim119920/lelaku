"""auth identity: portasi LL-05 dari develop ke skema UUID

Mengubah tabel placeholder dari 0001 menjadi skema auth sungguhan, TANPA mengubah
riwayat revision 0001-0005:

- users: email jadi unik per lower(email) (bukan unique biasa), panjang 320, kolom
  identity_status ('verified' | 'unverified').
- user_sessions: primary key jadi hash token (SHA-256, 64 hex); kolom session_id dibuang;
  created_at diisi default now(); check expires_at > created_at; index (user_id, expires_at).

Revision ID: 0006
Revises: 0005
Create Date: 2026-11-19
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # --- users ---
    # Gagal di sini kalau ada dua email yang hanya beda huruf besar/kecil; rapikan datanya dulu.
    op.drop_constraint(op.f("uq_users_email"), "users", type_="unique")
    op.alter_column(
        "users", "email", existing_type=sa.String(255), type_=sa.String(320), existing_nullable=False
    )
    op.create_index("uq_users_email_lower", "users", [sa.text("lower(email)")], unique=True)
    op.add_column(
        "users",
        sa.Column("identity_status", sa.String(16), server_default="unverified", nullable=False),
    )
    op.create_check_constraint(
        op.f("ck_users_identity_status"), "users", "identity_status IN ('verified', 'unverified')"
    )

    # --- user_sessions ---
    # Token lama (placeholder) disimpan tanpa skema hash yang sama, jadi tidak bisa dipakai lagi.
    op.execute("DELETE FROM user_sessions")
    op.drop_index(op.f("ix_user_sessions_user_id"), table_name="user_sessions")
    op.drop_constraint(op.f("pk_user_sessions"), "user_sessions", type_="primary")
    op.drop_column("user_sessions", "session_id")
    op.alter_column(
        "user_sessions",
        "session_token_hash",
        existing_type=sa.String(255),
        type_=sa.String(64),
        existing_nullable=False,
    )
    op.create_primary_key(op.f("pk_user_sessions"), "user_sessions", ["session_token_hash"])
    op.alter_column(
        "user_sessions",
        "created_at",
        existing_type=sa.DateTime(timezone=True),
        server_default=sa.text("now()"),
        existing_nullable=False,
    )
    op.create_check_constraint(
        op.f("ck_user_sessions_expiry_after_creation"), "user_sessions", "expires_at > created_at"
    )
    op.create_index(
        "ix_user_sessions_user_id_expires_at", "user_sessions", ["user_id", "expires_at"]
    )


def downgrade() -> None:
    # --- user_sessions ---
    op.drop_index("ix_user_sessions_user_id_expires_at", table_name="user_sessions")
    op.drop_constraint(op.f("ck_user_sessions_expiry_after_creation"), "user_sessions", type_="check")
    op.alter_column(
        "user_sessions",
        "created_at",
        existing_type=sa.DateTime(timezone=True),
        server_default=None,
        existing_nullable=False,
    )
    op.execute("DELETE FROM user_sessions")  # tidak ada session_id untuk dipulihkan
    op.drop_constraint(op.f("pk_user_sessions"), "user_sessions", type_="primary")
    op.alter_column(
        "user_sessions",
        "session_token_hash",
        existing_type=sa.String(64),
        type_=sa.String(255),
        existing_nullable=False,
    )
    op.add_column("user_sessions", sa.Column("session_id", sa.Uuid(), nullable=False))
    op.create_primary_key(op.f("pk_user_sessions"), "user_sessions", ["session_id"])
    op.create_index(op.f("ix_user_sessions_user_id"), "user_sessions", ["user_id"])

    # --- users ---
    op.drop_constraint(op.f("ck_users_identity_status"), "users", type_="check")
    op.drop_column("users", "identity_status")
    op.drop_index("uq_users_email_lower", table_name="users")
    op.alter_column(
        "users", "email", existing_type=sa.String(320), type_=sa.String(255), existing_nullable=False
    )
    op.create_unique_constraint(op.f("uq_users_email"), "users", ["email"])
