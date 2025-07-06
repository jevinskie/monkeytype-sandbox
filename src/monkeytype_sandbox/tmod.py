from rich import print

print(locals())


class Foo:
    print(locals())
    from . import imamod as alice

    print(locals())

    def speak(self):
        print(f"foo i: {self.alice.i}")

    print(locals())


print(locals())
print(locals())


class Bar:
    from . import imamod as bob

    def speak(self):
        print(f"bar i: {self.bob.i}")


f = Foo()
b = Bar()
f.speak()
b.speak()

print(Foo.speak)
print(f.speak)
