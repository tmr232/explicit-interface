## Member Descriptors

If we add slots for a non-existing member of a class, it'll be a `member_descriptor`


## Example!

```python
from explicit_interface.explicit import Interface, implements


class Duck(Interface):
    def quack(self): ...


@implements(Duck)
class Mallard:
    @implements(Duck.quack)
    def quack(self):
        print("Quack!")


class HumanInDuckCustome:
    def speak(self):
        print("I am a duck!")


@implements(Duck, for_=HumanInDuckCustome)
class _:
    @implements(Duck.quack)
    def quack(self, human: HumanInDuckCustome):
        return human.speak()


def make_ducks_quack(*ducks: Duck):
    for duck in ducks:
        duck.quack()


def main():
    mallard = Mallard()
    human = HumanInDuckCustome()

    make_ducks_quack(Duck(mallard), Duck(human))


if __name__ == "__main__":
    main()

```