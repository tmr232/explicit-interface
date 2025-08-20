from __future__ import annotations
import inspect

from types import FunctionType, MemberDescriptorType
from typing import Any, Callable
from dataclasses import dataclass

_IMPL_MARKERS_ATTR = "__implements__"


@dataclass(frozen=True, slots=True)
class _KnownImpl:
    mapping: dict[str, FunctionType]
    adapter: type | None = None


class _InterfaceMeta(type):
    def __new__(mcls, name, bases, namespace: dict[str, Any], /, **kwargs):
        # We know that all methods in an interface will be distinct, so there will
        # never be conflicts here.

        def _interface_init(self: Interface, impl):
            # If we're given an adapted type, we can just use it!
            if type(impl) is type(self):
                for name in self.__slots__:  # type: ignore[attr-defined]
                    setattr(self, name, getattr(impl, name))
                return

            if type(impl) in self.__known_implementations__:
                # If the mapping for the given impl already exists, we use it.
                known_impl = self.__known_implementations__[type(impl)]
            else:
                # Otherwise, we create the mapping from scratch
                impl_mapping = _collect_implementation(type(impl), type(self))
                known_impl = _KnownImpl(impl_mapping)
                self.__known_implementations__[type(impl)] = known_impl

            # Once we have the mapping, we bind all the methods
            # and populate the interface.
            adapter = None
            if known_impl.adapter is not None:
                adapter = known_impl.adapter()
            for name, value in known_impl.mapping.items():
                if adapter is None:
                    # Bind the methods before assigning them
                    setattr(self, name, value.__get__(impl, type(impl)))
                else:
                    setattr(
                        self, name, lambda: value.__get__(adapter, type(adapter))(impl)
                    )

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

        # We need slots to ensure we have member-descriptors for our interface objects.
        slots = tuple(interface_definition.keys())
        new_namespace["__slots__"] = slots
        new_namespace["__init__"] = _interface_init
        new_namespace["__interface_definition__"] = interface_definition
        new_namespace["__known_implementations__"] = {}
        return super().__new__(mcls, name, bases, new_namespace, **kwargs)


class Interface(metaclass=_InterfaceMeta):
    """Baseclass for defining explicit interfaces."""

    # The contents here are strictly for typechecking.
    __interface_definition__: dict[str, Callable]
    __known_implementations__: dict[type, _KnownImpl]

    def __init__(self, impl: Any): ...


def _get_interface_definition(interface: type[Interface]) -> dict[str, Callable]:
    return interface.__interface_definition__


def _typecheck_method(impl_method, interface_method) -> bool:
    # TODO: Implement typechecking!
    return True


def _collect_implementation(impl: type, interface: type[Interface]):
    interface_definition = _get_interface_definition(interface)
    impl_mapping = {}
    for name, value in inspect.getmembers(impl):
        # If a method of the object implements an interface method,
        # it will have that method registered in it's `__implements__`
        # member.
        impl_markers: set[MemberDescriptorType] = getattr(
            value, _IMPL_MARKERS_ATTR, set()
        )
        for marker in impl_markers:
            # First, ensure we're checking the right class
            if not isinstance(marker, MemberDescriptorType):
                raise TypeError(f"Expected member_descriptor, got {type(marker)}")
            if marker.__objclass__ is not interface:
                # Not a marker for this interface. Ignore it.
                continue
            if marker.__name__ not in interface_definition:
                # This should _never_ happen.
                raise NameError(f"Where the fuck did that come from? {marker.__name__}")
            if not _typecheck_method(value, interface_definition[marker.__name__]):
                raise TypeError("Method mismatch!")
            # Need to use names here, as we have a member descriptor and not the actual function!
            impl_mapping[marker.__name__] = value

    # Make sure we implemented everything!
    if set(interface_definition.keys()) != set(impl_mapping.keys()):
        raise TypeError("Missing methods!")

    return impl_mapping


def _implements_class(interface: type[Interface]):
    """Registers a class as an interface implementation.

    Additionally, ensures that the implementation is full.

    This function is not necessary, but makes things more explicit.
    """

    def _decorator[C: type](cls: C) -> C:
        impl_mapping = _collect_implementation(cls, interface)
        interface.__known_implementations__[cls] = _KnownImpl(impl_mapping)
        return cls

    return _decorator


def _implements_for(interface: type[Interface], for_: type):
    """Registers an interface adapter for a type."""

    def _decorator(adapter: type):
        # 0. Ensure no custom `__init__`.
        if adapter.__init__ != object.__init__:  # type: ignore[misc]
            # We don't provide it any arguments, so this saves us some
            raise TypeError("Adapter objects should not have `__init__` methods.")
        # 1. Create mapping
        impl_mapping = _collect_implementation(adapter, interface)
        # 2. Register mapping
        interface.__known_implementations__[for_] = _KnownImpl(
            impl_mapping, adapter=adapter
        )

    return _decorator


def _implements_method(method: Callable):
    """Marks a method with the interface method it's implementing."""

    def _decorator[F: FunctionType](f: F) -> F:
        setattr(
            f,
            _IMPL_MARKERS_ATTR,
            getattr(f, _IMPL_MARKERS_ATTR, set()) | {method},
        )
        return f

    return _decorator


def implements(
    interface_or_method: type[Interface] | Callable,
    /,
    *,
    for_: type | None = None,
):
    """Declares an implementation of an interface.

    When used on a method, declares the interface-method that the
    method implements.

    When used on a class, declares that the class implements the interface.

    When used on a class with the `for_` keyword, declares that the
    class is an interface adapter for the `for_` class.

    Args:
        interface_or_method: The interface or method being implemented
        for_: If provided, the class for which this is an adapter

    Returns:
        A decorator for declaring interface implementations.
    """
    if for_ is not None:
        if not isinstance(interface_or_method, type) or not issubclass(
            interface_or_method, Interface
        ):
            raise TypeError("implements-for can only be used on classes")
        return _implements_for(interface_or_method, for_)

    if isinstance(interface_or_method, type) and issubclass(
        interface_or_method, Interface
    ):
        return _implements_class(interface_or_method)

    return _implements_method(interface_or_method)
