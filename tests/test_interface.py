import inspect
import rich
from types import FunctionType, MemberDescriptorType
from abc import ABC
from typing import Any, Iterator


class InterfaceMeta(type):
    def __new__(mcls, name, bases, namespace:dict[str, Any], /, **kwargs):
        # We know that all methods in an interface will be distinct, so there will
        # never be conflicts here.
        interface_definitions = {value:name for name, value in namespace.items() if inspect.isfunction(value)}
        # We'll need the values later for type-checking, but for a first go, we can do with names alone.
        interface_names = {name for name, value in namespace.items() if inspect.isfunction(value)}
        class _Adapter:
            def __init__(self, obj):
                """
                1. Ensure the obj has an implementation.
                    This can be by being registered, or having
                    registration markers on all for all the interface methods
                2. Create members for mapping from the interface names to the
                    obj methods.
                """
                # Currently we only support direct implementations, not implement-for.
                obj_implementations = set()
                for name, value in inspect.getmembers(obj):
                    rich.print(name, value)
                    # If a method of the object implements an interface method,
                    # it will have that method registered in it's `__implements__`
                    # member.
                    member_implements = getattr(value, "__implements__", set())
                    for marker in member_implements:
                        # First, ensure we're checking the right class
                        if not isinstance(marker, MemberDescriptorType):
                            raise TypeError(f"Expected member_descriptor, got {type(marker)}")
                        if marker.__objclass__ != type(self):
                            # Not a marker for this interface. Ignore it.
                            continue
                        if marker.__name__ not in interface_names:
                            # This should _never_ happen.
                            raise NameError(f"Where the fuck did that come from? {marker.__name__}")
                        # Need to use names here, as we have a member descriptor and not the actual function!
                        setattr(self, marker.__name__, value)
                        obj_implementations.add(marker.__name__)
                    rich.print(obj_implementations)
                if interface_names != obj_implementations:
                    raise TypeError(f"Interface not implemented fully! {type(obj)}")

        # Create a new namespace with the modifications we need
        new_namespace = {}
        for key, value in namespace.items():
            if inspect.isfunction(value):
                continue
            new_namespace[key] = value


        slots = tuple(interface_definitions.values())
        new_namespace["__slots__"] = slots
        new_namespace['__init__'] = _Adapter.__init__


        rich.print(name,bases, new_namespace, kwargs)
        return super().__new__(mcls, name, bases, new_namespace, **kwargs)

class Interface(metaclass=InterfaceMeta):
    pass

def _implements_class(interface:type[Interface]):
    # TODO: Register!
    return lambda x:x

def _implements_method(method:FunctionType):
    def _decorator[F:FunctionType](f:F)->F:
        f.__implements__ = getattr(f, "__implements__", set()) | {method}
        return f
    return _decorator

def implements(interface_or_method: type[Interface] | FunctionType):
    if isinstance(interface_or_method, type) and issubclass(interface_or_method, Interface):
        return _implements_class(interface_or_method)
    return _implements_method(interface_or_method)

def implement(interface, for_):
    return lambda x:x

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
    rich.inspect(mallard.quack, all=True)
    for m in mallard.quack.__implements__:
        rich.inspect(m, all=True)
        print(m.__objclass__)
    duck = Duck(mallard)
    duck.quack()