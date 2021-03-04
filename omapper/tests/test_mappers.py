from dataclasses import dataclass
from datetime import datetime
from typing import Sequence, Optional
from unittest import TestCase

from omapper import Mapper
from omapper.mapper import Mappers


class TestImplicitFullyAnnotated(TestCase):
    class Source:
        def __init__(self):
            self.first = 'Blub'
            self.second = datetime(2021, 1, 2, 1, 2, 3, 4)
            self.third = [1, 2, 7, 3]

    @dataclass
    class TargetDataclass:
        dt: Optional[str]
        third: Sequence[int]

    class TargetObj:
        def __init__(self, first: str, second: str):
            self.first = first
            self.second = second

    def test_implicit_object(self):
        source = self.Source()
        expected = self.TargetObj(source.first, str(source.second.date()))

        mapper = Mapper(self.Source, self.TargetObj, mappers={
            'second': Mappers.transform('second', lambda e: str(e.date()))
        })
        actual = mapper(source)

        self.assertEqual(expected.first, actual.first)
        self.assertEqual(expected.second, actual.second)

    def test_implicit_dataclass(self):
        source = self.Source()
        expected = self.TargetDataclass(str(source.second.date()), source.third)

        mapper = Mapper(self.Source, self.TargetDataclass, mappers={
            'dt': Mappers.transform('second', lambda s: str(s.date()))
        })
        actual = mapper(source)

        self.assertEqual(expected.dt, actual.dt)
        self.assertEqual(expected.third, actual.third)

    def test_explicit_erroneous(self):
        self.assertRaises(
            ValueError, lambda: Mapper(
                self.Source, self.TargetDataclass, mappers={
                    'dt': Mappers.transform('second', lambda s: str(s.date()))}, explicit=True)
        )

    def test_explicit_dataclass(self):
        source = self.Source()
        expected = self.TargetDataclass(str(source.second.date()), source.third)

        mapper = Mapper(self.Source, self.TargetDataclass, mappers={
            'dt': Mappers.transform('second', lambda s: str(s.date())),
            'third': Mappers.identity('third'),
        })
        actual = mapper(source)

        self.assertEqual(expected.dt, actual.dt)
        self.assertEqual(expected.third, actual.third)
