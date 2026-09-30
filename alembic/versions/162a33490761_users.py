"""users

Revision ID: 162a33490761
Revises: 4dd9494c8a2e
Create Date: 2026-09-28 23:00:01.937022

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "162a33490761"
down_revision: str | Sequence[str] | None = "4dd9494c8a2e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("""
    CREATE TABLE users (
      id SERIAL PRIMARY KEY, username TEXT NOT NULL UNIQUE, password_hash TEXT NOT NULL);
    ALTER TABLE cars ADD COLUMN user_id INT REFERENCES users(id) ON DELETE CASCADE;
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE cars DROP COLUMN user_id; DROP TABLE users;")
