from __future__ import annotations
import inspect

import pytest
import rich
from types import FunctionType, MemberDescriptorType
from typing import Any, Callable

METHOD_MARKER_ATTRIBUTE_NAME = "__implements__"




class InterfaceMeta(type):
    def __new__(mcls, name, bases, namespace: dict[str, Any], /, **kwargs):
        # We know that all methods in an interface will be distinct, so there will
        # never be conflicts here.

        def _interface_init(self:Interface, impl):
            """
            1. Ensure the obj has an implementation.
                This can be by being registered, or having
                registration markers on all for all the interface methods
            2. Create members for mapping from the interface names to the
                obj methods.
            """
            impl_mapping = _collect_implementation(impl, type(self))
            for name, value in impl_mapping.items():
                setattr(self, name, value)

        # Create a new namespace with the modifications we need
        new_namespace = {}
        for key, value in namespace.items():
            if inspect.isfunction(value):
                continue
            new_namespace[key] = value

        interface_definition = {
            name: value
            for name, value in namespace.items()
            if inspect.isfunction(value) and name != "__init__"
        }

        slots = tuple(interface_definition.keys())
        new_namespace["__slots__"] = slots
        new_namespace["__init__"] = _interface_init
        new_namespace["__interface_definition__"] = interface_definition
        return super().__new__(mcls, name, bases, new_namespace, **kwargs)


class Interface(metaclass=InterfaceMeta):
    __interface_definition__:dict[str, Callable]
    def __init__(self, impl:Any): ...

def _get_interface_definition(interface:type[Interface])->dict[str, Callable]:
    return interface.__interface_definition__

def _typecheck_method(impl_method, interface_method)->bool:
    return True

def _collect_implementation(impl, interface:type[Interface]):
    interface_definition = _get_interface_definition(interface)
    impl_mapping = {}
    for name, value in inspect.getmembers(impl):
        # If a method of the object implements an interface method,
        # it will have that method registered in it's `__implements__`
        # member.
        member_implements = getattr(
            value, METHOD_MARKER_ATTRIBUTE_NAME, set()
        )
        for marker in member_implements:
            # First, ensure we're checking the right class
            if not isinstance(marker, MemberDescriptorType):
                raise TypeError(
                    f"Expected member_descriptor, got {type(marker)}"
                )
            if marker.__objclass__ is not interface:
                # Not a marker for this interface. Ignore it.
                continue
            if marker.__name__ not in interface_definition:
                # This should _never_ happen.
                raise NameError(
                    f"Where the fuck did that come from? {marker.__name__}"
                )
            if not _typecheck_method(value, interface_definition[marker.__name__]):
                raise TypeError(f"Method mismatch!")
            # Need to use names here, as we have a member descriptor and not the actual function!
            impl_mapping[marker.__name__] = value

    # Make sure we implemented everything!
    if set(interface_definition.keys()) != set(impl_mapping.keys()):
        raise TypeError("Missing methods!")

    return impl_mapping


def _implements_class(interface: type[Interface]):
    """
    Here we want to create the name mapping in advance, to save time
    on class instantiation.

    Additionally, we wanna ensure it implements the interface.
    """
    # First, ensure we implement the interface!
    def _decorator[C:type](cls:C)->C:
        _collect_implementation(cls, interface)
        return cls
    return _decorator


def _implements_method(method: Callable):
    def _decorator[F: FunctionType](f: F) -> F:
        setattr(
            f,
            METHOD_MARKER_ATTRIBUTE_NAME,
            getattr(f, METHOD_MARKER_ATTRIBUTE_NAME, set()) | {method},
        )
        return f

    return _decorator


def implements(interface_or_method: type[Interface] | Callable):
    if isinstance(interface_or_method, type) and issubclass(
        interface_or_method, Interface
    ):
        return _implements_class(interface_or_method)
    return _implements_method(interface_or_method)


def implement(interface, for_):
    return lambda x: x


class Duck(Interface):
    def quack(self): ...


@implements(Duck)
class Mallard:
    @implements(Duck.quack)
    def quack(self):
        print("Quack!")


class MandarinDuck:
    @implements(Duck.quack)
    def speak(self):
        print("Quack!")


class Dog:
    def bark(self):
        print("Woof!")


@implement(Duck, for_=Dog)
class _:
    quack = Dog.bark


def test_fully_explicit():
    mallard = Mallard()
    duck = Duck(mallard)
    duck.quack()


class TestExplicit:
    class IDog(Interface):
        def bark(self): ...
        def bite(self): ...

    @pytest.fixture(name="IDog")
    def _idog_fixture(self):
        return self.IDog

    def test_full_implementation(self, IDog:type[IDog]):
        @implements(IDog)
        class Dog:
            @implements(IDog.bark)
            def bark(self):
                pass
            @implements(IDog.bite)
            def bite(self):
                pass

        d = IDog(Dog())
        d.bark()

    def test_partial_implementation(self, IDog:type[IDog]):
        with pytest.raises(TypeError):
            @implements(IDog)
            class PartialDog:
                @implements(IDog.bark)
                def bark(self):
                    pass

    def test_different_name(self, IDog:type[IDog]):
        @implements(IDog)
        class Dog:
            @implements(IDog.bark)
            def speak(self):
                pass
            @implements(IDog.bite)
            def bite(self):
                pass
        d = IDog(Dog())
        d.bark()

    def test_has_other_methods(self, IDog:type[IDog]):
        @implements(IDog)
        class Dog:
            def __init__(self):
                pass

            @implements(IDog.bark)
            def bark(self):
                pass

            @implements(IDog.bite)
            def bite(self):
                pass

            def walk(self):
                pass

