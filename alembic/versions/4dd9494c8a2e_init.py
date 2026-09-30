"""init

Revision ID: 4dd9494c8a2e
Revises:
Create Date: 2026-09-24 11:40:02.988417

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4dd9494c8a2e"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("""
    CREATE TABLE cars (
      id SERIAL PRIMARY KEY, brand TEXT NOT NULL, model TEXT NOT NULL,
      year INT, mileage INT NOT NULL DEFAULT 0);
    CREATE TABLE records (
      id SERIAL PRIMARY KEY, car_id INT NOT NULL REFERENCES cars(id) ON DELETE CASCADE,
      date DATE NOT NULL, kind TEXT NOT NULL, cost DECIMAL(10,2) NOT NULL DEFAULT 0, note TEXT);
    """)


def downgrade() -> None:
    op.execute("DROP TABLE records; DROP TABLE cars;")
