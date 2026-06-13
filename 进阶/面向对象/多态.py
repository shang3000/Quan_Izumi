'''抽象类'''


class AC:
    def cool_wind(self):
        pass

    def hot_wind(self):
        pass

    def wind(self):
        pass


class Deli_AC(AC):
    def cool_wind(self):
        print('得力空调制冷')

    def hot_wind(self):
        print('得力空调制热')

    def wind(self):
        print('得力空调左右摆风')


class Meidel_AC(AC):
    def cool_wind(self):
        print('美的空调制冷')

    def hot_wind(self):
        print('美的空调制热')

    def wind(self):
        print('美的空调左右摆风')


def make_cool(ac: AC):
    ac.cool_wind()


deli = Deli_AC()
meidel = Meidel_AC()

make_cool(deli)
make_cool(meidel)

"""
多态
"""
# class Animal:
#     def speak(self):
#         pass
#
#
# class Cat(Animal):
#     def speak(self):
#         print('喵喵喵')
#
#
# class Dog(Animal):
#     def speak(self):
#         print('汪汪汪')
#
#
# def make_noise(animal: Animal):
#     animal.speak()
#
#
# dog = Dog()
# cat = Cat()
#
# make_noise(cat)
# make_noise(dog)
