"""
和文件相关的类定义
"""
import json

from data_define import Record


# 抽象类作顶层设计
class FileReader:
    def read_data(self) -> list[Record]:  # 读取的每一条文件数据转换为Record对象，并封装到list返回即可
        pass


class TextFileReader(FileReader):
    def __init__(self, path):
        self.path = path  # 定义成员变量记录文件路径

    # 复写
    def read_data(self) -> list[Record]:
        record_list: list[Record] = []
        with open(self.path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()  # 消除读取到的每一行数据的/n
                # print(line)
                data_list = line.split(",")
                record = Record(data_list[0], data_list[1], int(data_list[2]), data_list[3])
                record_list.append(record)
        return record_list


class JsonFileReader(FileReader):
    def __init__(self, path):
        self.path = path

    def read_data(self) -> list[Record]:
        record_list: list[Record] = []
        with open(self.path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                data_dict = json.loads(line)
                recdord = Record(data_dict['date'], data_dict['order_id'], int(data_dict['money']),
                                 data_dict['province'])
                record_list.append(recdord)
        return record_list


if __name__ == '__main__':
    text_file_reader = TextFileReader("D:/2011年1月销售数据.txt")
    json_file_reader = JsonFileReader("D:/2011年2月销售数据JSON.txt")
    list1 = text_file_reader.read_data()
    list2 = json_file_reader.read_data()
    for l in list1:
        print(l)
    for l in list2:
        print(l)
