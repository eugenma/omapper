import collections
import inspect
from functools import partial
from typing import Any, Sequence, OrderedDict, Optional, MutableMapping, Dict, Mapping, Iterator, Tuple

from .omapper_types import DefaultMapper, MapEntry
from .exceptions import InstantiationError, AttributeMappingError


class Mapper:
    def __init__(self, src_type: type, dest_type: type, mappers: Optional[MutableMapping[str, MapEntry]] = None,
                 explicit: bool = False, default_mapper: Optional[DefaultMapper] = None):
        self.mappers = {}  # type: Dict[str, MapEntry]
        if mappers:
            self.mappers.update(mappers)

        dest_attrs = Mapper.__get_all_attrs(dest_type)
        if not dest_attrs:
            msg = f"The type of 'dest_type' {dest_type.__qualname__} does not has any parameters in the constructor."
            raise ValueError(msg)

        if explicit:
            self.__check_explicit_only(self.mappers, dest_attrs, dest_type)
        else:
            self.mappers.update(self.__get_implicit(default_mapper, self.mappers, dest_attrs))

        self.dest_type = dest_type
        self.source_type = src_type

        self.__check_missing_dest_attrs(self.mappers, dest_attrs, dest_type)

    def __call__(self, src: Any) -> Any:
        """Apply the mapping on src.

        :raise AttributeMappingError if map of an attribute failed.
        """
        values = self.__mapped_values(src)
        try:
            return self.dest_type(**values)
        except Exception:
            raise InstantiationError(self.dest_type, values)

    def __mapped_values(self, src: Any) -> OrderedDict[str, Any]:
        values_it = map(partial(self.__map_attribute, src), self.mappers.items())
        return collections.OrderedDict(values_it)

    def __map_attribute(self, src: Any, dest_attr_mapper: Tuple[str, MapEntry]) -> Tuple[str, Any]:
        dest_attr, mapper = dest_attr_mapper
        try:
            return dest_attr, mapper(src)
        except Exception:
            raise AttributeMappingError(self.dest_type, dest_attr, src, mapper)

    @staticmethod
    def __get_all_attrs(dest_type: type) -> Sequence[str]:
        # MyPy throws an error on Ctor __init__, but there are no other means to access it.
        dest_params = inspect.signature(dest_type.__init__).parameters  # type: ignore
        all_attrs = map(lambda e: e[0], dest_params.items())
        dest_attrs = [e for e in all_attrs if e != 'self']
        return dest_attrs

    @staticmethod
    def __check_explicit_only(mappers, dest_attrs: Sequence[str], dest_type: type) -> None:
        missing_attrs = [e for e in dest_attrs if e not in mappers]
        missing_attrs_str = ', '.join(f"'{e}'" for e in missing_attrs)
        if missing_attrs_str:
            msg = f"Explicit Mapper is missing maps to following target type '{dest_type.__qualname__}'" \
                + "and  fields {missing_attrs_str}."
            raise ValueError(msg)

    @staticmethod
    def __check_missing_dest_attrs(mappers, dest_attrs, dest_type):
        missing = [attr for attr in mappers.keys() if attr not in dest_attrs]
        if missing:
            mapper_keys = ', '.join((f"'{k}'" for k in missing))
            raise ValueError(
                f"Configured attributes {mapper_keys} not found in target ctor '{dest_type.__qualname__}'. "
                f"Available attributes {dest_attrs}.")

    @staticmethod
    def __get_implicit(
            default_mapper: Optional[DefaultMapper], existing_mappers: Mapping[str, MapEntry],
            dest_attrs: Sequence[str]) -> Iterator[Tuple[str, MapEntry]]:
        implicit_mapper = default_mapper if default_mapper else lambda name: lambda src: getattr(src, name)
        implicit_attrs = filter(lambda e: e not in existing_mappers, dest_attrs)
        return map(lambda a: (a, implicit_mapper(a)), implicit_attrs)
