from dataclasses import dataclass
from datetime import datetime
from typing import Sequence, Optional
from unittest import TestCase

from omapper import Mapper
from omapper.exceptions import AttributeMappingError, InstantiationError


class TestImplicitFullyAnnotated(TestCase):
    class Source:
        def __init__(self, first=None, second=None, third=None):
            self.first = 'Blub' if not first else first
            self.second = datetime(2021, 1, 2, 1, 2, 3, 4) if not second else second
            self.third = [1, 2, 7, 3] if not third else third

    @dataclass
    class TargetDataclass:
        dt: Optional[str]
        third: Sequence[int]

    class TargetObj:
        def __init__(self, first: str, second: str):
            self.first = first
            self.second = second

    class Simple:
        def __init__(self, attr):
            self.attr = attr

    def test_implicit_object(self):
        source = self.Source()
        expected = self.TargetObj(source.first, str(source.second.date()))

        mapper = Mapper(self.Source, self.TargetObj, mappers={
            'second': lambda s: str(s.second.date())
        })
        actual = mapper(source)

        self.assertEqual(expected.first, actual.first)
        self.assertEqual(expected.second, actual.second)

    def test_implicit_dataclass(self):
        source = self.Source()
        expected = self.TargetDataclass(str(source.second.date()), source.third)

        mapper = Mapper(self.Source, self.TargetDataclass, mappers={
            'dt': lambda s: str(s.second.date())
        })
        actual = mapper(source)

        self.assertEqual(expected.dt, actual.dt)
        self.assertEqual(expected.third, actual.third)

    def test_mapping_with_exception(self):
        # noinspection PyUnusedLocal
        def exception(src):
            raise ValueError("Failed!!")

        mapper = Mapper(self.Simple, self.Simple, mappers={
            'attr': exception
        })

        src = self.Simple(123)
        self.assertRaises(AttributeMappingError, lambda: mapper(src))

    def test_explicit_erroneous(self):
        self.assertRaises(
            ValueError, lambda: Mapper(
                self.Source, self.TargetDataclass, mappers={
                    'dt': lambda s: str(s.second.date())}, explicit=True)
        )

    def test_explicit_dataclass(self):
        source = self.Source()
        expected = self.TargetDataclass(str(source.second.date()), source.third)

        mapper = Mapper(self.Source, self.TargetDataclass, mappers={
            'dt': lambda s: str(s.second.date()),
            'third': lambda s: s.third,
        })
        actual = mapper(source)

        self.assertEqual(expected.dt, actual.dt)
        self.assertEqual(expected.third, actual.third)

    def test_check_identity_dest_attr(self):
        source = self.Source()
        expected = self.TargetDataclass(str(source.second.date()), source.third)

        mapper = Mapper(self.Source, self.TargetDataclass, mappers={
            'dt': lambda src: str(src.second.date()),
            'third': lambda src: src.third,  # We test this method here
        })
        actual = mapper(source)

        self.assertEqual(expected.dt, actual.dt)
        self.assertEqual(expected.third, actual.third)

    def test_identity_reference(self):
        mapper = Mapper(self.Source, self.TargetDataclass, mappers={
            'dt': lambda s: str(s.second.date())
        })

        source = self.Source()
        dest = mapper(source)

        original_source = list(source.third)  # Create copy
        dest.third.append(111)

        self.assertNotEqual(original_source, dest.third, msg="Just a self check that '111' was not already in source.")
        self.assertEqual(source.third, dest.third, msg="Identity map should pass references and not values.")
        self.assertEqual(source.third[-1], 111, "Value was added through 'dest'")

    def test_implicit_default_mapper(self):
        mapper = Mapper(self.Source, self.Source, default_mapper=lambda dest_attr: lambda src: getattr(src, dest_attr))

        source = self.Source("AAA", "BBB", "CCC")
        dest = mapper(source)
        self.assertEqual(dest.first, "AAA")
        self.assertEqual(dest.second, "BBB")
        self.assertEqual(dest.third, "CCC")

    def test_missing_target_mapper_key(self):
        def create_exception():
            return Mapper(self.Simple, self.Simple, mappers={
                'missing_target': lambda s: s.attr,
            })
        self.assertRaises(ValueError, create_exception)

    def test_exception_in_ctor(self):
        class Target:
            def __init__(self, first):
                raise AttributeError(f"Raise with value '{first}'.")

        mapper = Mapper(self.Source, Target)

        src = self.Source()
        self.assertRaises(InstantiationError, lambda: mapper(src))

    def test_target_has_empty_ctor(self):
        class Target:
            def __init__(self):
                pass

        self.assertRaises(ValueError, lambda: Mapper(self.Source, Target))
