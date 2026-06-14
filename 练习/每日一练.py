import math


class Shape:
    def __init__(self, name):
        self.name = name

    def calculate_area(self):
        return 0


class Rectangle(Shape):
    def __init__(self, length, width):
        super().__init__('矩形')
        self.length = length
        self.width = width

    def calculate_area(self):
        return self.length * self.width


class Circle(Shape):
    def __init__(self, radius):
        super().__init__('圆形')
        self.radius = radius

    def calculate_area(self):
        return math.pi * self.radius ** 2


choice = input('请输入图形类型(矩形/圆形): ')
if choice == '矩形':
    length = float(input('长: '))
    width = float(input('宽: '))
    shape = Rectangle(length, width)
else:
    r = float(input('半径: '))
    shape = Circle(r)
print(f'面积: {shape.calculate_area()}')
