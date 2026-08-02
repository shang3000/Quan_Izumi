# -*- coding: utf-8 -*-
"""
电影票数据分析 — 首映影院选择
作业二：K-means 聚类分析
"""
import os
import sys
sys.stdout.reconfigure(encoding='utf-8')

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
import warnings
warnings.filterwarnings('ignore')

# ============================================================
# 0. 中文字体设置
# ============================================================
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'STHeiti']
plt.rcParams['axes.unicode_minus'] = False

# ============================================================
# 1. 数据加载与清洗
# ============================================================
print('=' * 60)
print('1. 数据加载与清洗')
print('=' * 60)

# 学生信息
STUDENT_ID = '2406180229'
STUDENT_NAME = '商航'
STUDENT_CINEMA_CODE = 2406180229  # 学号作为影院编码

DATA_PATH = r'D:\pycharm\Person-Practice\电影票分析\电影票数据_含学生信息.csv'

# 脚本所在目录（保证图片保存路径正确，不论从哪里运行）
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(SCRIPT_DIR, 'images')
os.makedirs(IMAGES_DIR, exist_ok=True)

df_raw = pd.read_csv(DATA_PATH)
print(f'原始数据: {df_raw.shape[0]} 行, {df_raw.shape[1]} 列')

# 过滤异常值
df = df_raw.copy()
before = len(df)
df = df[df['capacity'] >= 0]
df = df[df['ticket_use'] >= 0]
df = df[df['occu_perc'] <= 100]
df = df[df['occu_perc'] >= 0]
after = len(df)
print(f'清洗后: {after} 行 (移除 {before - after} 条异常值)')

# ============================================================
# 2. 按影院聚合特征
# ============================================================
print('\n' + '=' * 60)
print('2. 按影院聚合特征')
print('=' * 60)

cinema_df = df.groupby('cinema_code').agg(
    total_sales=('total_sales', 'sum'),           # 总票房
    tickets_sold=('tickets_sold', 'sum'),          # 总售票数
    tickets_out=('tickets_out', 'sum'),            # 总退票数
    avg_occu=('occu_perc', 'mean'),                # 平均上座率
    avg_price=('ticket_price', 'mean'),            # 平均票价
    avg_capacity=('capacity', 'mean'),             # 平均座位容量
    show_count=('film_code', 'count'),             # 场次数
    film_count=('film_code', 'nunique'),           # 电影种类数
).reset_index()

# 衍生特征
cinema_df['refund_rate'] = cinema_df['tickets_out'] / cinema_df['tickets_sold'].clip(lower=1)
cinema_df['sales_per_show'] = cinema_df['total_sales'] / cinema_df['show_count'].clip(lower=1)

print(f'影院数量: {len(cinema_df)}')
print(cinema_df.describe().round(2).to_string())

# ============================================================
# 3. 特征标准化
# ============================================================
print('\n' + '=' * 60)
print('3. 特征标准化')
print('=' * 60)

features = ['total_sales', 'tickets_sold', 'avg_occu', 'avg_price', 'avg_capacity', 'show_count', 'film_count']
X = cinema_df[features].copy()

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
print(f'聚类特征: {features}')
print(f'标准化完成, 形状: {X_scaled.shape}')

# ============================================================
# 4. 肘部法确定最优 K
# ============================================================
print('\n' + '=' * 60)
print('4. 肘部法确定最优 K')
print('=' * 60)

inertias = []
K_range = range(2, 11)
for k in K_range:
    km = KMeans(n_clusters=k, random_state=42, n_init=10)
    km.fit(X_scaled)
    inertias.append(km.inertia_)
    print(f'  K={k}, Inertia={km.inertia_:.0f}')

# 绘制肘部图
fig, ax = plt.subplots(figsize=(8, 5))
ax.plot(list(K_range), inertias, 'bo-', linewidth=2, markersize=8)
ax.set_xlabel('聚类数 K', fontsize=12)
ax.set_ylabel('惯性值 (Inertia)', fontsize=12)
ax.set_title('肘部法确定最优聚类数', fontsize=14, fontweight='bold')
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(IMAGES_DIR, '03_elbow.png'), dpi=150, bbox_inches='tight')
plt.close()
print('肘部图已保存')

# ============================================================
# 5. K-means 聚类 (K=4)
# ============================================================
print('\n' + '=' * 60)
print('5. K-means 聚类 (K=4)')
print('=' * 60)

K = 4
kmeans = KMeans(n_clusters=K, random_state=42, n_init=10)
cinema_df['cluster'] = kmeans.fit_predict(X_scaled)

# 聚类中心
centers = pd.DataFrame(scaler.inverse_transform(kmeans.cluster_centers_), columns=features)
print('\n聚类中心 (逆标准化):')
print(centers.round(2).to_string())

# 各簇统计
print('\n各簇影院数量:')
print(cinema_df['cluster'].value_counts().sort_index())

# ============================================================
# 6. 可视化
# ============================================================
print('\n' + '=' * 60)
print('6. 生成可视化图表')
print('=' * 60)

colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
cluster_names = {0: '一般影院', 1: '热门影院', 2: '大型影院', 3: '精品影院'}

# 按平均票房排序簇名
cluster_mean_sales = cinema_df.groupby('cluster')['total_sales'].mean().sort_values(ascending=False)
name_pool = ['顶级影院', '热门影院', '中等影院', '普通影院']
for i, c in enumerate(cluster_mean_sales.index):
    cinema_df.loc[cinema_df['cluster'] == c, 'cluster_name'] = name_pool[i]
    cluster_names[c] = name_pool[i]

# --- 图1: 票房分布 ---
fig, axes = plt.subplots(1, 2, figsize=(14, 5))
axes[0].hist(cinema_df['total_sales'] / 1e8, bins=30, color='#45B7D1', edgecolor='white', alpha=0.8)
axes[0].set_xlabel('总票房 (亿元)', fontsize=11)
axes[0].set_ylabel('影院数量', fontsize=11)
axes[0].set_title('影院总票房分布', fontsize=13, fontweight='bold')
axes[0].grid(axis='y', alpha=0.3)

axes[1].hist(cinema_df['avg_occu'], bins=30, color='#FF6B6B', edgecolor='white', alpha=0.8)
axes[1].set_xlabel('平均上座率 (%)', fontsize=11)
axes[1].set_ylabel('影院数量', fontsize=11)
axes[1].set_title('影院平均上座率分布', fontsize=13, fontweight='bold')
axes[1].grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.savefig(os.path.join(IMAGES_DIR, '01_sales_dist.png'), dpi=150, bbox_inches='tight')
plt.close()
print('图1: 票房分布 - 已保存')

# --- 图2: 上座率 vs 票价 ---
fig, ax = plt.subplots(figsize=(10, 6))
for i in range(K):
    mask = cinema_df['cluster'] == i
    ax.scatter(cinema_df.loc[mask, 'avg_price'] / 10000,
               cinema_df.loc[mask, 'avg_occu'],
               c=colors[i], label=cluster_names[i],
               s=cinema_df.loc[mask, 'total_sales'] / 1e7,
               alpha=0.6, edgecolors='white', linewidth=0.5)
ax.set_xlabel('平均票价 (万元)', fontsize=12)
ax.set_ylabel('平均上座率 (%)', fontsize=12)
ax.set_title('上座率 vs 票价 (气泡大小=总票房)', fontsize=14, fontweight='bold')
ax.legend(fontsize=10)
ax.grid(True, alpha=0.3)

# 高亮学生数据点（学号:2406180229 商航）
stu = cinema_df[cinema_df['cinema_code'] == STUDENT_CINEMA_CODE]
if len(stu) > 0:
    ax.scatter(stu['avg_price'].values / 10000, stu['avg_occu'].values,
               c='gold', s=250, marker='*', edgecolors='#DAA520', linewidth=2, zorder=10, label=f'{STUDENT_NAME}({STUDENT_ID})')
    for _, srow in stu.iterrows():
        ax.annotate(f'{STUDENT_NAME}',
                    (srow['avg_price'] / 10000, srow['avg_occu']),
                    xytext=(10, -20), textcoords='offset points',
                    fontsize=9, fontweight='bold', color='#DAA520',
                    arrowprops=dict(arrowstyle='->', color='#DAA520', lw=1.2))
    ax.legend(fontsize=10)

plt.tight_layout()
plt.savefig(os.path.join(IMAGES_DIR, '02_occu_vs_price.png'), dpi=150, bbox_inches='tight')
plt.close()
print('图2: 上座率vs票价 - 已保存')

# --- 图3: PCA 降维聚类图 ---
pca = PCA(n_components=2)
X_pca = pca.fit_transform(X_scaled)

fig, ax = plt.subplots(figsize=(10, 7))
for i in range(K):
    mask = cinema_df['cluster'] == i
    ax.scatter(X_pca[mask, 0], X_pca[mask, 1],
               c=colors[i], label=cluster_names[i],
               s=80, alpha=0.7, edgecolors='white', linewidth=0.5)
# 画聚类中心
centers_pca = pca.transform(kmeans.cluster_centers_)
for i in range(K):
    ax.scatter(centers_pca[i, 0], centers_pca[i, 1],
               c=colors[i], s=300, marker='*', edgecolors='black', linewidth=1.5, zorder=5)
ax.set_xlabel(f'主成分1 ({pca.explained_variance_ratio_[0]*100:.1f}%)', fontsize=12)
ax.set_ylabel(f'主成分2 ({pca.explained_variance_ratio_[1]*100:.1f}%)', fontsize=12)
ax.set_title('K-means 聚类结果 (PCA 降维可视化)', fontsize=14, fontweight='bold')
ax.legend(fontsize=11, loc='best')
ax.grid(True, alpha=0.3)

# 高亮学生数据在PCA图中的位置
if len(stu) > 0:
    stu_scaled = scaler.transform(stu[features])
    stu_pca = pca.transform(stu_scaled)
    ax.scatter(stu_pca[:, 0], stu_pca[:, 1],
               c='gold', s=300, marker='*', edgecolors='#DAA520', linewidth=2, zorder=10, label=f'{STUDENT_NAME}({STUDENT_ID})')
    ax.legend(fontsize=11, loc='best')

plt.tight_layout()
plt.savefig(os.path.join(IMAGES_DIR, '04_cluster_pca.png'), dpi=150, bbox_inches='tight')
plt.close()
print('图3: PCA聚类图 - 已保存')

# --- 图4: 各簇特征对比 ---
fig, axes = plt.subplots(1, 3, figsize=(16, 5))
compare_features = [('total_sales', '总票房', 1e8, '亿'), ('avg_occu', '平均上座率', 1, '%'), ('avg_price', '平均票价', 10000, '万')]
for ax, (feat, label, div, unit) in zip(axes, compare_features):
    cluster_means = cinema_df.groupby('cluster_name')[feat].mean().sort_values(ascending=False)
    bars = ax.bar(range(len(cluster_means)), cluster_means.values / div, color=colors[:len(cluster_means)], edgecolor='white')
    ax.set_xticks(range(len(cluster_means)))
    ax.set_xticklabels(cluster_means.index, fontsize=10)
    ax.set_ylabel(f'{label} ({unit})', fontsize=11)
    ax.set_title(f'各簇平均{label}', fontsize=13, fontweight='bold')
    ax.grid(axis='y', alpha=0.3)
    for bar, val in zip(bars, cluster_means.values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                f'{val/div:.1f}', ha='center', va='bottom', fontsize=9)
plt.tight_layout()
plt.savefig(os.path.join(IMAGES_DIR, '05_cluster_compare.png'), dpi=150, bbox_inches='tight')
plt.close()
print('图4: 簇特征对比 - 已保存')

# --- 图5: TOP10 推荐影院 ---
# 综合评分: 标准化票房*0.3 + 标准化上座率*0.3 + 标准化场次数*0.2 + 标准化电影数*0.2
from sklearn.preprocessing import MinMaxScaler
mm = MinMaxScaler()
score_cols = ['total_sales', 'avg_occu', 'show_count', 'film_count']
score_data = mm.fit_transform(cinema_df[score_cols])
weights = np.array([0.3, 0.3, 0.2, 0.2])
cinema_df['score'] = score_data @ weights

top10 = cinema_df.nlargest(10, 'score')

fig, ax = plt.subplots(figsize=(12, 6))
y_pos = range(len(top10))
bars = ax.barh(y_pos, top10['score'].values, color='#45B7D1', edgecolor='white', height=0.6)
ax.set_yticks(y_pos)
ax.set_yticklabels([f"影院#{c}" for c in top10['cinema_code'].values], fontsize=11)
ax.set_xlabel('综合评分', fontsize=12)
ax.set_title('TOP10 推荐首映影院', fontsize=14, fontweight='bold')
ax.invert_yaxis()
ax.grid(axis='x', alpha=0.3)
for bar, val, cluster in zip(bars, top10['score'].values, top10['cluster_name'].values):
    ax.text(bar.get_width() + 0.005, bar.get_y() + bar.get_height()/2,
            f'{val:.3f} [{cluster}]', ha='left', va='center', fontsize=10)
plt.tight_layout()
plt.savefig(os.path.join(IMAGES_DIR, '06_top10_recommend.png'), dpi=150, bbox_inches='tight')
plt.close()
print('图5: TOP10推荐 - 已保存')

# ============================================================
# 7. 输出结果
# ============================================================
print('\n' + '=' * 60)
print('7. 分析结果')
print('=' * 60)

print('\n各簇特征概况:')
cluster_summary = cinema_df.groupby('cluster_name').agg(
    影院数=('cinema_code', 'count'),
    平均总票房=('total_sales', lambda x: f'{x.mean()/1e8:.2f}亿'),
    平均上座率=('avg_occu', lambda x: f'{x.mean():.1f}%'),
    平均票价=('avg_price', lambda x: f'{x.mean()/10000:.1f}万'),
    平均场次数=('show_count', lambda x: f'{x.mean():.0f}'),
    平均电影数=('film_count', lambda x: f'{x.mean():.0f}'),
)
print(cluster_summary.to_string())

print('\nTOP10 推荐首映影院:')
for i, row in top10.iterrows():
    print(f"  影院#{row['cinema_code']:>3d} | 评分:{row['score']:.3f} | "
          f"票房:{row['total_sales']/1e8:.2f}亿 | 上座率:{row['avg_occu']:.1f}% | "
          f"类型:{row['cluster_name']}")

# 保存聚类结果
cinema_df.to_csv(os.path.join(SCRIPT_DIR, 'cinema_cluster_result.csv'), index=False, encoding='utf-8-sig')
print('\n聚类结果已保存到 cinema_cluster_result.csv')
print('\n所有图表已保存到 images/ 目录')
print('分析完成!')
