import pytest

from explicit_interface.explicit import Interface, implements


class TestImplementFor:
    class IDog(Interface):
        def bark(self): ...
        def bite(self): ...

    @pytest.fixture(name="IDog")
    def _idog_fixture(self):
        return self.IDog

    @pytest.mark.xfail(reason="I don't know how to implement this yet.")
    def test_pure_mapping(self, IDog: type[IDog]):
        class Dog:
            def speak(self):
                pass

            def eat(self):
                pass

        @implements(IDog, for_=Dog)
        class _:
            bark = Dog.speak
            bite = Dog.eat

    def test_explicit(self, IDog: type[IDog]):
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


class TestExplicit:
    class IDog(Interface):
        def bark(self): ...
        def bite(self): ...

    @pytest.fixture(name="IDog")
    def _idog_fixture(self):
        return self.IDog

    def test_full_implementation(self, IDog: type[IDog]):
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

    def test_partial_implementation(self, IDog: type[IDog]):
        with pytest.raises(TypeError):
            @implements(IDog)
            class PartialDog:
                @implements(IDog.bark)
                def bark(self):
                    pass

    def test_different_name(self, IDog: type[IDog]):
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

    def test_has_other_methods(self, IDog: type[IDog]):
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


class TestImplicit:
    class IDog(Interface):
        def bark(self): ...
        def bite(self): ...

    @pytest.fixture(name="IDog")
    def _idog_fixture(self):
        return self.IDog

    def test_full_implementation(self, IDog: type[IDog]):
        class Dog:
            @implements(IDog.bark)
            def bark(self):
                pass

            @implements(IDog.bite)
            def bite(self):
                pass

        d = IDog(Dog())
        d.bark()