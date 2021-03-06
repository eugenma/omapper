import collections
import inspect
from typing import Callable, Any, Sequence, OrderedDict, Optional, MutableMapping, Dict

try:
    from typing import get_origin, get_args
except ImportError:
    raise ImportError("Requires Python Version >= 3.8")


MapEntry = Callable[[Any, ], Any]
DefaultMapper = Callable[[str], Callable[[Any], Any]]


class Mapper:
    def __init__(self, src_type: type, dest_type: type, mappers: Optional[MutableMapping[str, MapEntry]] = None,
                 explicit: bool = False, default_mapper: Optional[DefaultMapper] = None):
        self.mappers = {}  # type: Dict[str, MapEntry]
        if mappers:
            self.mappers.update(mappers)

        self.dest_attrs = Mapper.get_all_attrs(dest_type)
        if not self.dest_attrs:
            raise ValueError(f"The type of 'dest_type' {dest_type} does not has any parameters in the constructor.")

        if explicit:
            self.__check_explicit_only(self.dest_attrs, dest_type)
        else:
            implicit_mapper = default_mapper if default_mapper else lambda name: lambda src: getattr(src, name)

            implicit_attrs = filter(lambda e: e not in self.mappers, self.dest_attrs)
            self.mappers.update((a, implicit_mapper(a)) for a in implicit_attrs)

        missing = [attr for attr in self.mappers.keys() if attr not in self.dest_attrs]
        if missing:
            mapper_keys = ', '.join((f"'{k}'" for k in missing))
            raise ValueError(
                f"Configured attributes {mapper_keys} not found in target ctor '{dest_type}'. "
                f"Available attributes {self.dest_attrs}.")

        self.dest_type = dest_type
        self.source_type = src_type

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
    def get_all_attrs(dest_type: type) -> Sequence[str]:
        # MyPy throws an error on Ctor __init__, but there are no other means to access it.
        dest_params = inspect.signature(dest_type.__init__).parameters  # type: ignore
        all_attrs = map(lambda e: e[0], dest_params.items())
        dest_attrs = [e for e in all_attrs if e != 'self']
        return dest_attrs

    def __check_explicit_only(self, dest_attrs: Sequence[str], dest_type: type):
        missing_attrs = [e for e in dest_attrs if e not in self.mappers]
        missing_attrs_str = ', '.join(f"'{dest_type.__name__}.{e}'" for e in missing_attrs)
        if missing_attrs_str:
            raise ValueError(f"Explicit Mapper is missing maps to following target fields {missing_attrs_str}.")
