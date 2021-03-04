import collections
import inspect
from typing import Callable, Any, Sequence, OrderedDict, Optional, MutableMapping

try:
    from typing import get_origin, get_args
except ImportError:
    raise ImportError("Requires Python Version >= 3.8")


MapEntry = Callable[[str, Any], Any]


class Mappers:
    @classmethod
    def identity(cls, dest_attr: str, src_attr: Optional[str] = None) -> MapEntry:
        return cls.transform(dest_attr, lambda e: e, src_attr)

    @classmethod
    def transform(cls, dest_attr: str, by: Callable[[Any, ], Any], src_attr: Optional[str] = None) -> MapEntry:
        if not src_attr:
            src_attr = dest_attr

        def map_transform(_: str, src: Any) -> Any:
            src_value = getattr(src, src_attr)
            return by(src_value)

        return map_transform


class Mapper:
    def __init__(self, src_type: type, dest_type: type, mappers: MutableMapping[str, MapEntry], explicit: bool = False):
        self.mappers = mappers

        dest_attrs = Mapper.get_attrs(dest_type)
        if explicit:
            self.__check_explicit_only(dest_attrs, dest_type)
        else:
            implicit_attrs = filter(lambda e: e not in mappers, dest_attrs)
            for attr in implicit_attrs:
                self.mappers[attr] = Mappers.identity(attr)

        self.dest_type = dest_type
        self.source_type = src_type

    def __check_explicit_only(self, dest_attrs: Sequence[str], dest_type: type):
        missing_attrs = [e for e in dest_attrs if e not in self.mappers]
        missing_attrs_str = ', '.join(f"'{dest_type.__name__}.{e}'" for e in missing_attrs)
        if missing_attrs_str:
            raise ValueError(f"Explicit Mapper is missing maps to following target fields {missing_attrs_str}.")

    def _mapped_values(self, src: Any) -> OrderedDict[str, Any]:
        values = collections.OrderedDict()
        for dest_attr, mapper in self.mappers.items():
            dest_value = mapper(dest_attr, src)
            values[dest_attr] = dest_value
        return values

    def __call__(self, src: Any) -> Any:
        values = self._mapped_values(src)
        return self.dest_type(**values)

    @staticmethod
    def get_attrs(dest_type: type) -> Sequence[str]:
        dest_params = inspect.signature(dest_type.__init__).parameters
        all_attrs = map(lambda e: e[0], dest_params.items())
        dest_attrs = [e for e in all_attrs if e != 'self']
        return dest_attrs
