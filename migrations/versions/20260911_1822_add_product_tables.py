"""add product tables

Revision ID: 23b6d70c6b0d
Revises: 75c5f03bb246
Create Date: 2026-09-11 18:22:13.284230

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = '23b6d70c6b0d'
down_revision: str | Sequence[str] | None = '75c5f03bb246'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


ARTICLE_SEQUENCE = sa.Sequence("product_article_seq")


def upgrade() -> None:
    op.execute(sa.schema.CreateSequence(ARTICLE_SEQUENCE))
    op.create_table('products',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('catalog_id', sa.SmallInteger(), nullable=False),
    sa.Column('category_id', sa.SmallInteger(), nullable=False),
    sa.Column('brand_id', sa.SmallInteger(), nullable=True),
    sa.Column('article', sa.String(length=16), nullable=False),
    sa.Column('title', sa.String(length=48), nullable=False),
    sa.Column('description', sa.String(length=1024), nullable=False),
    sa.Column('price', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('old_price', sa.Numeric(precision=12, scale=2), nullable=True),
    sa.Column('currency', sa.String(length=3), nullable=False),
    sa.Column('variant_label', sa.String(length=48), nullable=True),
    sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('is_visible', sa.Boolean(), nullable=False),
    sa.Column('is_in_stock', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("currency IN ('RUB', 'USD')", name=op.f('ck_products_known_currency')),
    sa.ForeignKeyConstraint(['brand_id'], ['brands.id'], name=op.f('fk_products_brand_id_brands'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['catalog_id'], ['catalogs.id'], name=op.f('fk_products_catalog_id_catalogs'), ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['category_id'], ['categories.id'], name=op.f('fk_products_category_id_categories'), ondelete='RESTRICT'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_products')),
    sa.UniqueConstraint('article', name=op.f('uq_products_article'))
    )
    op.create_index(op.f('ix_products_brand_id'), 'products', ['brand_id'], unique=False)
    op.create_index(op.f('ix_products_catalog_id'), 'products', ['catalog_id'], unique=False)
    op.create_index(op.f('ix_products_category_id'), 'products', ['category_id'], unique=False)
    op.create_table('product_media',
    sa.Column('id', sa.Integer(), sa.Identity(always=False), nullable=False),
    sa.Column('product_id', sa.Uuid(), nullable=False),
    sa.Column('kind', sa.String(length=8), nullable=False),
    sa.Column('file_id', sa.Text(), nullable=False),
    sa.Column('position', sa.SmallInteger(), server_default='0', nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("kind IN ('photo', 'video')", name=op.f('ck_product_media_known_kind')),
    sa.ForeignKeyConstraint(['product_id'], ['products.id'], name=op.f('fk_product_media_product_id_products'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_product_media'))
    )
    op.create_index(op.f('ix_product_media_product_id'), 'product_media', ['product_id'], unique=False)
    op.create_table('product_variants',
    sa.Column('id', sa.Integer(), sa.Identity(always=False), nullable=False),
    sa.Column('product_id', sa.Uuid(), nullable=False),
    sa.Column('title', sa.String(length=48), nullable=False),
    sa.Column('price_override', sa.Numeric(precision=12, scale=2), nullable=True),
    sa.Column('currency', sa.String(length=3), nullable=False),
    sa.Column('position', sa.SmallInteger(), server_default='0', nullable=False),
    sa.Column('is_available', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("currency IN ('RUB', 'USD')", name=op.f('ck_product_variants_known_currency')),
    sa.ForeignKeyConstraint(['product_id'], ['products.id'], name=op.f('fk_product_variants_product_id_products'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_product_variants')),
    sa.UniqueConstraint('product_id', 'title', name=op.f('uq_product_variants_product_id'))
    )
    op.create_index(op.f('ix_product_variants_product_id'), 'product_variants', ['product_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_product_variants_product_id'), table_name='product_variants')
    op.drop_table('product_variants')
    op.drop_index(op.f('ix_product_media_product_id'), table_name='product_media')
    op.drop_table('product_media')
    op.drop_index(op.f('ix_products_category_id'), table_name='products')
    op.drop_index(op.f('ix_products_catalog_id'), table_name='products')
    op.drop_index(op.f('ix_products_brand_id'), table_name='products')
    op.drop_table('products')
    op.execute(sa.schema.DropSequence(ARTICLE_SEQUENCE))
