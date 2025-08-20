import pytest

from explicit_interface import Interface, implements


class IDog(Interface):
    def bark(self): ...

    def bite(self): ...


def test_full_implementation():
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


def test_partial_implementation():
    with pytest.raises(TypeError):

        @implements(IDog)
        class PartialDog:
            @implements(IDog.bark)
            def bark(self):
                pass


def test_different_name():
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


def test_has_other_methods():
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


def test_implicit_full_implementation():
    class Dog:
        @implements(IDog.bark)
        def bark(self):
            pass

        @implements(IDog.bite)
        def bite(self):
            pass

    d = IDog(Dog())
    d.bark()


def test_with_args():
    class Speaker(Interface):
        def speak(self, words): ...

    @implements(Speaker)
    class Greeter:
        @implements(Speaker.speak)
        def greet(self, someone):
            return f"Hello, {someone}!"

    greeter = Greeter()
    speaker = Speaker(greeter)
    someone = "World"
    assert greeter.greet(someone) == speaker.speak(someone)


def test_conflicting_interfaces():
    class SinglePrinter(Interface):
        def print(self, msg): ...

    class DoublePrinter(Interface):
        def print(self, msg1, msg2): ...

    @implements(SinglePrinter)
    @implements(DoublePrinter)
    class Impl:
        @implements(SinglePrinter.print)
        def print_single(self, msg):
            print(msg)

        @implements(DoublePrinter.print)
        def print_double(self, msg1, msg2):
            self.print_single(msg1)
            self.print_single(msg2)

    impl = Impl()
    SinglePrinter(impl).print("a")
    DoublePrinter(impl).print("a", "b")


class TestImplementFor:
    def test_explicit(self):
        class Dog:
            def speak(self):
                pass

        @implements(IDog, for_=Dog)
        class _:
            @implements(IDog.bark)
            def bark(self, dog: Dog):
                return dog.speak()

            @implements(IDog.bite)
            def bite(self, dog: Dog):
                pass

        d = IDog(Dog())
        d.bark()

    @pytest.mark.xfail(reason="I don't know how to implement this yet.")
    def test_pure_mapping(self):
        class Dog:
            def speak(self):
                pass

            def eat(self):
                pass

        @implements(IDog, for_=Dog)
        class _:
            bark = Dog.speak
            bite = Dog.eat


def test_interface_from_same_interface():
    class Iface(Interface):
        def method(self): ...

    class Impl:
        @implements(Iface.method)
        def method(self):
            pass

    Iface(Iface(Impl()))
