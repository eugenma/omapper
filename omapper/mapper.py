import collections
import inspect
from typing import Callable, Any, Sequence, OrderedDict, Optional, MutableMapping, Dict, Mapping, Iterator, Tuple


MapEntry = Callable[[Any, ], Any]
DefaultMapper = Callable[[str], MapEntry]


class Mapper:
    def __init__(self, src_type: type, dest_type: type, mappers: Optional[MutableMapping[str, MapEntry]] = None,
                 explicit: bool = False, default_mapper: Optional[DefaultMapper] = None):
        self.mappers = {}  # type: Dict[str, MapEntry]
        if mappers:
            self.mappers.update(mappers)

        dest_attrs = Mapper.__get_all_attrs(dest_type)
        if not dest_attrs:
            raise ValueError(f"The type of 'dest_type' {dest_type} does not has any parameters in the constructor.")

        if explicit:
            self.__check_explicit_only(self.mappers, dest_attrs, dest_type)
        else:
            self.mappers.update(self.__get_implicit(default_mapper, self.mappers, dest_attrs))

        self.dest_type = dest_type
        self.source_type = src_type

        self.__check_missing_dest_attrs(self.mappers, dest_attrs, dest_type)

    def __call__(self, src: Any) -> Any:
        values = self._mapped_values(src)
        try:
            return self.dest_type(**values)
        except Exception:
            str_values = map(lambda e: f'"{e[0]}"="{repr(e[1])}"', values.items())
            joined = ', '.join(str_values)
            msg = f"Failed to create dest '{self.dest_type}' with params {joined}."
            raise ValueError(msg)

    def _mapped_values(self, src: Any) -> OrderedDict[str, Any]:
        values = collections.OrderedDict()
        for dest_attr, mapper in self.mappers.items():
            dest_value = mapper(src)
            values[dest_attr] = dest_value
        return values

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
        missing_attrs_str = ', '.join(f"'{dest_type.__name__}.{e}'" for e in missing_attrs)
        if missing_attrs_str:
            raise ValueError(f"Explicit Mapper is missing maps to following target fields {missing_attrs_str}.")

    @staticmethod
    def __check_missing_dest_attrs(mappers, dest_attrs, dest_type):
        missing = [attr for attr in mappers.keys() if attr not in dest_attrs]
        if missing:
            mapper_keys = ', '.join((f"'{k}'" for k in missing))
            raise ValueError(
                f"Configured attributes {mapper_keys} not found in target ctor '{dest_type}'. "
                f"Available attributes {dest_attrs}.")

    @staticmethod
    def __get_implicit(
            default_mapper: Optional[DefaultMapper], existing_mappers: Mapping[str, MapEntry],
            dest_attrs: Sequence[str]) -> Iterator[Tuple[str, MapEntry]]:
        implicit_mapper = default_mapper if default_mapper else lambda name: lambda src: getattr(src, name)
        implicit_attrs = filter(lambda e: e not in existing_mappers, dest_attrs)
        return map(lambda a: (a, implicit_mapper(a)), implicit_attrs)
