class Student():
    # name=None
    # age=None
    # gender=None
    def __init__(self, name, age, gender):
        self.name = name
        self.age = age
        self.gender = gender
        print('Student类创建了一个对象')


stu = Student('周杰伦', 35, '男')
print(stu.name)
print(stu.age)
print(stu.gender)