from typing import NewType
from uuid import UUID

CatalogId = NewType("CatalogId", int)
CategoryId = NewType("CategoryId", int)
BrandId = NewType("BrandId", int)
ProductId = NewType("ProductId", UUID)
VariantId = NewType("VariantId", int)
MediaId = NewType("MediaId", int)
