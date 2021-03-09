from typing import Mapping, Any

from .omapper_types import MapEntry


class OMapperError(Exception):
    """Base class for omapper errors"""
    pass


class InstantiationError(OMapperError):
    """Raised if creation of an object failed.
    """
    def __init__(self, klass: type, values: Mapping[str, Any]) -> None:
        self.klass = klass
        self.values = values
        self.message = InstantiationError.get_msg(klass, values)

    @staticmethod
    def get_msg(klass: type, values: Mapping[str, Any]) -> str:
        str_values = map(lambda e: f'"{e[0]}"="{str(e[1])}"', values.items())
        joined = ', '.join(str_values)
        return f"Failed to create dest '{klass.__qualname__}' with params {joined}."


class AttributeMappingError(OMapperError):
    """Mapping of a particular attribute failed."""
    def __init__(self, dest_type: type, dest_attribute: str, src: Any, mapper: MapEntry) -> None:
        self.dest_type = dest_type
        self.dest_attribute = dest_attribute
        self.src = src
        self.mapper = mapper

        self.message = AttributeMappingError.get_msg(dest_type, dest_attribute, src, mapper)

    @staticmethod
    def get_msg(dest_type: type, dest_attribute: str, src: Any, mapper: MapEntry) -> str:
        return f"Applying mapper failed for target '{dest_type.__qualname__}.{dest_attribute}'. " \
              + f"Mapped via '{mapper.__qualname__}'. " \
              + f"From source type '{type(src).__qualname__}' representation {str(src)}."
