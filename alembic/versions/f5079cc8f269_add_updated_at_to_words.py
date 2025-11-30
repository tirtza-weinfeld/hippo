"""add_updated_at_to_words

Revision ID: f5079cc8f269
Revises: 3872c9d26720
Create Date: 2025-11-30 18:23:00.700938

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f5079cc8f269"
down_revision: Union[str, Sequence[str], None] = "3872c9d26720"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add updated_at column to words table
    # Set default to created_at for existing rows, then change to now() for new rows
    op.add_column(
        "words",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("words", "updated_at")
