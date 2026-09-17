from abc import ABC, abstractmethod

from telegramsales.shared.infrastructure.database.base import BaseORM


class IEntityMapper[EntityType, ModelType: BaseORM](ABC):
    @staticmethod
    @abstractmethod
    def to_entity(model: ModelType) -> EntityType: ...

    @staticmethod
    @abstractmethod
    def to_model(entity: EntityType) -> ModelType: ...
