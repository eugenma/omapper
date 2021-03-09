from typing import Callable, Any

MapEntry = Callable[[Any, ], Any]
DefaultMapper = Callable[[str], MapEntry]
