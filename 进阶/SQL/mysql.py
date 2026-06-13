from pymysql import Connection

# 建立连接
conn = Connection(
    host='localhost',  # 主机名
    port=3306,  # 端口（注意：3306 是标准端口，你写的是 3306，不是 33006）
    user='root',  # 用户名
    password='162572',  # 密码
    autocommit=True  # 自动提交（适合简单测试）
)

# 获取游标
cursor = conn.cursor()

# 选择数据库
conn.select_db('py_sql')

# 执行查询（查询你之前成功导入的 orders 表）
cursor.execute("SELECT * FROM orders LIMIT 20")

# 获取所有结果并打印
results = cursor.fetchall()
print("查询到的记录数：", len(results))
print("前几行数据示例：")
for row in results:
    print(row)

# 如果你想看到字段名，可以这样：
# cursor.execute("SELECT * FROM orders LIMIT 1")
# columns = [desc[0] for desc in cursor.description]
# print("字段名：", columns)

# 关闭连接（好习惯）
conn.close()
