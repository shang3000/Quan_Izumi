import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from scipy.stats import pearsonr

# 解决图表中文乱码（考试必加，否则图表无中文扣分）
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# 1. 读取Excel原始数据
df = pd.read_excel("锦江.xlsx")

# 2. 清洗总价：去除"万"字，转为浮点数值
# 转数字失败 → 转为 NaN 缺失值
df["总价"] = pd.to_numeric(df["总价"].str.replace("万", ""), errors="coerce")
# df["总价"] = df["总价"].str.replace("万", "").astype(float)
# 3. 清洗单价：去除"单价"前缀、"元/平米"单位，转为浮点数值
df["单价"] = pd.to_numeric(df["单价"].str.replace("单价|元/平米", ""), errors="coerce")

# 4. 清洗关注信息：提取关注人数，转为整数
df["关注人数"] = pd.to_numeric(df["关注信息"].str.replace("人关注", ""), errors="coerce")

# 5. 规范户型列：将"房屋信息"列重命名为"户型"，更清晰
df = df.rename(columns={"房屋信息": "户型"})

# 6. 删除存在缺失值的脏数据，避免后续建模报错
df = df.dropna()

# 7. 保存预处理后的文件（考试把"自己的姓名"改成你的真名）
df.to_excel("自己的姓名.xlsx", index=False)

# 统计各户型的房源数量
house_type_cnt = df["户型"].value_counts()
# 绘制柱状图
plt.bar(house_type_cnt.index, house_type_cnt.values, color="#0070C0")
plt.title("房源户型分布")
plt.ylabel("房源数量")
plt.xlabel("户型")
plt.xticks(rotation=45) # 户型名称旋转，避免重叠
plt.show()

# 取总价最高的10条数据
top10_price = df.nlargest(10, "总价")
# 绘制水平条形图
plt.barh(top10_price["位置信息"], top10_price["总价"], color="#ED7D31")
plt.gca().invert_yaxis() # 反转Y轴，总价最高的在最上方
plt.title("二手房总价前10名")
plt.xlabel("总价（万元）")
plt.ylabel("小区名称")
plt.show()

# 绘制单价-总价散点图
plt.scatter(df["单价"], df["总价"], color="#70AD47", alpha=0.6)
plt.title("房屋单价与总价关系散点图")
plt.xlabel("单价（元/平米）")
plt.ylabel("总价（万元）")
plt.show()

# 1. 特征工程：文本特征转数值（独热编码）
X = pd.get_dummies(df[["区域", "户型", "关注人数"]], drop_first=True)
y = df["单价"]

# 2. 划分训练集和测试集（8:2，固定随机种子保证结果可复现）
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 3. 训练线性回归模型
model = LinearRegression()
model.fit(X_train, y_train)

# 4. 模型预测
y_pred = model.predict(X_test)

# 5. 计算评价指标
mse = mean_squared_error(y_test, y_pred)
mae = mean_absolute_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)
r, _ = pearsonr(y_test, y_pred)

# 6. 输出结果（考试直接打印，清晰明了）
print("===== 模型评价指标 =====")
print(f"均方误差 MSE: {round(mse, 2)}")
print(f"平均绝对误差 MAE: {round(mae, 2)}")
print(f"相关系数 R: {round(r, 4)}")
print(f"决定系数 R²: {round(r2, 4)}")