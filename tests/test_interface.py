import inspect
import rich
from types import FunctionType

class Interface:
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
    def __init__(self, obj):
        """
        We need to:
        1. Find all the interface methods in the object
        2. Create a mapping from the interface to those methods
        """
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
    duck = Duck(Mallard())
    duck.quack()