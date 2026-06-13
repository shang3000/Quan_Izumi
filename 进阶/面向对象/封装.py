class Phone:
    __current_voltage = 0.5

    def __keep_single_core(self):
        print('让CPU以单核模式运行')

    def call_by_sg(self):
        if self.__current_voltage >= 1:
            print('5g通话已经开启')
        else:
            self.__keep_single_core()
            print('电量不足，无法使用5g通话')


phone = Phone()
# phone.__keep_single_core
# print(phone.__current_voltage)  # AttributeError: 'Phone' object has no attribute '__current_voltage'
phone.call_by_sg()
'''
私有的内部成员和方法只有类中的其他成员可以使用
'''

'''
练习
'''
# class Phone:
#     __is_5g_enable = False
#
#     def __check_5g(self):
#         if self.__is_5g_enable:
#             print('5g开启')
#         else:
#             print('5g关闭，使用4g网络')
#
#     def call_by_5g(self):
#         self.__check_5g()
#         print('正在通话中')
#
#
# phone = Phone()
# phone.call_by_5g()
