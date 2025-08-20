# Explicit Interface

Python's [ABC]'s and [Protocol]s are great.
They are clean, simple, and straightforward.

But like all good things - they are not without faults.

Maybe your method names don't _quite_ match the protocol;
maybe you're using a 3rd party type and need to write an adapter;
or maybe you want to extend your ABC,
but your users already have a method with the same name!

What if you could simplify those edge-cases by baking-in the extra complexity?

Introducing - Explicit Interfaces!

Be explicit about the interfaces you implement,
and create adapters with ease!

## Example

```python
from explicit_interface import Interface, implements


class Duck(Interface):
    def walk(self): ...
    def talk(self): ...

    
@implements(Duck)
class Mallard:
    @implements(Duck.walk)
    def walk(self):
        print("Walks like a duck")

    @implements(Duck.talk)
    def talk(self):
        print("Talks like a duck")

class Human:
    def walk(self):
        print("Walks like a human")
        
    def talk(self):
        print("Talks like a human")

        
def interact_with_duck(duck: Duck):
    duck = Duck(duck) # Adapt the duck
    duck.walk()
    duck.talk()

    
mallard = Mallard()
interact_with_duck(mallard)  # Walks like a duck
                             # Talks like a duck
                            
human = Human()
interact_with_duck(human)    # TypeError


@implements(Duck, for_=Human)
class _:
    @implements(Duck.walk)
    def walk(self, human: Human):
        return human.walk()
    
    @implements(Duck.talk)
    def talk(self, human: Human):
        return human.talk() 


interact_with_duck(human)    # Walks like a human
                             # Talks like a human
```

[ABC]: https://docs.python.org/3/library/abc.html#abc.ABC
[Protocol]: https://docs.python.org/3/library/typing.html#typing.Protocol