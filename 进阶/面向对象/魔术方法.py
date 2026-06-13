class Student():
    def __init__(self, name, age):
        self.name = name
        self.age = age

    #     def __str__(self):
    #         return f'Student类的对象，name:{self.name},age:{self.age}'
    #
    #
    # '''
    # 控制类转换为字符串的行为
    # '''
    #
    # stu = Student('周杰伦', 35)
    # print(stu)  # <__main__.Student object at 0x000002B68DEF3FD0>,不提供str，魔术方法的情况下输出内存地址
    # print(str(stu))

    #     def __lt__(self, other):
    #         return self.age < other.age
    #
    #
    # stu1 = Student('周杰伦', 35)
    # stu2 = Student('林俊杰', 36)
    # print(stu1 < stu2)
    # print(stu1 > stu2)

#     def __le__(self, other):
#         return self.age <= other.age
#
#
# stu1 = Student('周杰伦', 36)
# stu2 = Student('林俊杰', 36)
# print(stu1 <= stu2)
# print(stu1 >= stu2)

    def __eq__(self,other):
        return self.age==other.age

stu1 = Student('周杰伦', 36)
stu2 = Student('林俊杰', 36)
print(stu1 == stu2)