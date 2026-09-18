"""add trigram search indexes

Revision ID: 3dde7a08c6a4
Revises: 8823e8efaef9
Create Date: 2026-09-18 21:52:17.440603

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3dde7a08c6a4'
down_revision: Union[str, Sequence[str], None] = '8823e8efaef9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("create extension if not exists pg_trgm")
    op.execute(
        "create index ix_products_title_trgm "
        "on products using gin (title gin_trgm_ops)"
    )
    op.execute(
        "create index ix_brands_title_trgm "
        "on brands using gin (title gin_trgm_ops)"
    )
    op.execute(
        "create index ix_products_article_lower "
        "on products (lower(article) text_pattern_ops)"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("drop index if exists ix_products_article_lower")
    op.execute("drop index if exists ix_brands_title_trgm")
    op.execute("drop index if exists ix_products_title_trgm")
