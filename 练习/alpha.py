class Shape:
    def __init__(self,name):
        self.name = name
    def calculate_area(self):
        return 0

class Rectangle(Shape):
    def __init__(self,length,width):
        super().__init__('矩形')
        self.length = length
        self.width = width
    def calculate_area(self):
        return self.length * self.width