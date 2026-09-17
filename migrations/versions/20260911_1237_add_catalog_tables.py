"""add catalog tables

Revision ID: 75c5f03bb246
Revises: b3c8d5e91af2
Create Date: 2026-09-11 12:37:03.821268

"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "75c5f03bb246"
down_revision: str | Sequence[str] | None = "b3c8d5e91af2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TITLE_LENGTH = 48


def upgrade() -> None:
    op.create_table(
        "brands",
        sa.Column("id", sa.SmallInteger(), sa.Identity(always=False), nullable=False),
        sa.Column("title", sa.String(length=TITLE_LENGTH), nullable=False),
        sa.Column(
            "sort_order", sa.SmallInteger(), server_default="0", nullable=False
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_brands")),
        sa.UniqueConstraint("title", name=op.f("uq_brands_title")),
    )
    op.create_table(
        "catalogs",
        sa.Column("id", sa.SmallInteger(), sa.Identity(always=False), nullable=False),
        sa.Column("title", sa.String(length=TITLE_LENGTH), nullable=False),
        sa.Column(
            "sort_order", sa.SmallInteger(), server_default="0", nullable=False
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_catalogs")),
        sa.UniqueConstraint("title", name=op.f("uq_catalogs_title")),
    )
    op.create_table(
        "categories",
        sa.Column("id", sa.SmallInteger(), sa.Identity(always=False), nullable=False),
        sa.Column("catalog_id", sa.SmallInteger(), nullable=False),
        sa.Column("parent_id", sa.SmallInteger(), nullable=True),
        sa.Column("title", sa.String(length=TITLE_LENGTH), nullable=False),
        sa.Column(
            "sort_order", sa.SmallInteger(), server_default="0", nullable=False
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["catalog_id"],
            ["catalogs.id"],
            name=op.f("fk_categories_catalog_id_catalogs"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["parent_id"],
            ["categories.id"],
            name=op.f("fk_categories_parent_id_categories"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_categories")),
        sa.UniqueConstraint(
            "catalog_id",
            "parent_id",
            "title",
            name=op.f("uq_categories_catalog_id"),
            postgresql_nulls_not_distinct=True,
        ),
    )
    op.create_index(
        op.f("ix_categories_catalog_id"), "categories", ["catalog_id"], unique=False
    )
    op.create_index(
        op.f("ix_categories_parent_id"), "categories", ["parent_id"], unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_categories_parent_id"), table_name="categories")
    op.drop_index(op.f("ix_categories_catalog_id"), table_name="categories")
    op.drop_table("categories")
    op.drop_table("catalogs")
    op.drop_table("brands")
