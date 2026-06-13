# class Pc:
#     def caculation(self, a, b):
#         return a + b
#
#     def capitalization(self, strings):
#         return strings.upper()
#
#
# alpha = Pc()
# print(alpha.caculation(3, 4))
# print(alpha.capitalization('marvel'))

# 多继承
class Phone:
    IMEI = None
    producer = 'HM'

    def call_by_4g(self):
        print('开启4g通话')


class NFCReader:
    nfc_type = '第五代'
    producer = 'HM'

    def read_card(self):
        print('NFC读卡')

    def write_card(self):
        print('NFC写卡')


class Remote_Control:
    rc_type = '红外遥控'

    def control(self):
        print('红外遥控开启了')


class MYPhone(Phone, NFCReader, Remote_Control):
    producer = 'SH'  # 复写


phone = MYPhone()
# phone.call_by_4g()
# phone.read_card()
# phone.write_card()
# phone.control()
print(phone.producer)
# 调用父类成员
print(Phone.producer)
# 方法2
'''
super().成员变量
super.成员方法
'''
