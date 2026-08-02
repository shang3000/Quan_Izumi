const pptxgen = require("pptxgenjs");
const path = require("path");

const C = {
  green: "8BAF56", greenDark: "6B8F3A", greenLight: "C5D9A4",
  cream: "FAF8F4", white: "FFFFFF", dark: "2C3E2D", gray: "7A8B7C",
  red: "E74C3C", orange: "F39C12", blue: "3498DB",
};
const mkSh = () => ({ type: "outer", color: "000000", blur: 8, offset: 2, angle: 135, opacity: 0.1 });
let pres = new pptxgen();
pres.layout = "LAYOUT_16x9";
pres.author = "不如吃茶去";
pres.title = "电影首映影院选择 — 数据分析全流程详解";

// ======================== S1 封面 ========================
let s1 = pres.addSlide();
s1.background = { color: C.green };
s1.addShape(pres.shapes.OVAL, { x: -1.5, y: -1.5, w: 4, h: 4, fill: { color: C.greenDark, transparency: 30 } });
s1.addShape(pres.shapes.OVAL, { x: 8, y: 3.5, w: 3.5, h: 3.5, fill: { color: C.greenDark, transparency: 30 } });
s1.addShape(pres.shapes.RECTANGLE, { x: 1.2, y: 1.0, w: 7.6, h: 3.2, fill: { color: C.white }, shadow: mkSh() });
s1.addText("电影首映影院选择分析", { x: 1.5, y: 1.3, w: 7, h: 1.0, fontSize: 36, fontFace: "Microsoft YaHei", bold: true, color: C.dark, margin: 0 });
s1.addText("从原始数据到决策推荐 — 全流程技术详解", { x: 1.5, y: 2.3, w: 7, h: 0.5, fontSize: 16, fontFace: "Microsoft YaHei", color: C.green, margin: 0 });
s1.addText("Python 大数据分析  ·  K-means 聚类  ·  数据可视化", { x: 1.5, y: 2.9, w: 7, h: 0.4, fontSize: 13, fontFace: "Microsoft YaHei", color: C.gray, margin: 0 });
s1.addText("不如吃茶去", { x: 1.5, y: 3.4, w: 7, h: 0.4, fontSize: 12, fontFace: "Microsoft YaHei", color: C.gray, margin: 0 });

// ======================== S2 整体流程 ========================
let s2 = pres.addSlide();
s2.background = { color: C.cream };
s2.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.06, fill: { color: C.green } });
s2.addText("整体流程", { x: 0.6, y: 0.25, w: 5, h: 0.55, fontSize: 26, fontFace: "Microsoft YaHei", bold: true, color: C.dark, margin: 0 });
s2.addText("数据分析的五个阶段", { x: 0.6, y: 0.78, w: 5, h: 0.35, fontSize: 12, fontFace: "Microsoft YaHei", color: C.gray, margin: 0 });
const flowSteps = [
  { num: "01", title: "数据清洗", desc: "发现并修复\n数据中的错误" },
  { num: "02", title: "特征工程", desc: "从原始数据中\n提取有用指标" },
  { num: "03", title: "聚类分析", desc: "用算法自动\n给影院分群" },
  { num: "04", title: "结果可视化", desc: "把分析结果\n变成直观图表" },
  { num: "05", title: "决策推荐", desc: "基于数据\n做出业务决策" },
];
flowSteps.forEach((st, i) => {
  const fx = 0.4 + i * 1.88;
  s2.addShape(pres.shapes.RECTANGLE, { x: fx, y: 1.35, w: 1.68, h: 1.8, fill: { color: C.white }, shadow: mkSh() });
  s2.addShape(pres.shapes.OVAL, { x: fx + 0.56, y: 1.5, w: 0.55, h: 0.55, fill: { color: C.green } });
  s2.addText(st.num, { x: fx + 0.56, y: 1.5, w: 0.55, h: 0.55, fontSize: 16, fontFace: "Microsoft YaHei", bold: true, color: C.white, align: "center", valign: "middle", margin: 0 });
  s2.addText(st.title, { x: fx + 0.05, y: 2.1, w: 1.58, h: 0.3, fontSize: 13, fontFace: "Microsoft YaHei", bold: true, color: C.dark, align: "center", margin: 0 });
  s2.addText(st.desc, { x: fx + 0.05, y: 2.45, w: 1.58, h: 0.6, fontSize: 10.5, fontFace: "Microsoft YaHei", color: C.gray, align: "center", lineSpacingMultiple: 1.3, margin: 0 });
  if (i < 4) s2.addText("→", { x: fx + 1.68, y: 1.8, w: 0.2, h: 0.3, fontSize: 14, color: C.green, align: "center", valign: "middle", margin: 0 });
});
s2.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 3.4, w: 9.0, h: 1.9, fill: { color: C.white }, shadow: mkSh() });
s2.addText("数据概况", { x: 0.7, y: 3.5, w: 4, h: 0.35, fontSize: 14, fontFace: "Microsoft YaHei", bold: true, color: C.green, margin: 0 });
s2.addText([
  { text: "电影票销售数据：记录了 239 家影院对 48 部电影的 7520 场放映的销售情况。", options: { breakLine: true } },
  { text: "每条记录包含：影院编号、电影编号、总票房、售出票数、退票数、上座率、票价、座位容量等 11 个字段。", options: { breakLine: true } },
  { text: "", options: { breakLine: true, fontSize: 4 } },
  { text: "目标：通过数据挖掘，找出最适合举办电影首映的影院。首映需要高票房、高上座率、大容量的影院来保证影响力。", options: {} },
], { x: 0.7, y: 3.9, w: 8.5, h: 1.3, fontSize: 11.5, fontFace: "Microsoft YaHei", color: C.dark, lineSpacingMultiple: 1.35, margin: 0 });

// ======================== S3 数据清洗 - 为什么 ========================
let s3 = pres.addSlide();
s3.background = { color: C.cream };
s3.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.06, fill: { color: C.green } });
s3.addText("阶段一：数据清洗", { x: 0.6, y: 0.25, w: 6, h: 0.55, fontSize: 26, fontFace: "Microsoft YaHei", bold: true, color: C.dark, margin: 0 });
s3.addText("为什么不能直接用原始数据？", { x: 0.6, y: 0.78, w: 6, h: 0.35, fontSize: 12, fontFace: "Microsoft YaHei", color: C.gray, margin: 0 });

s3.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 1.25, w: 9.0, h: 2.0, fill: { color: C.white }, shadow: mkSh() });
s3.addText("垃圾进，垃圾出（Garbage In, Garbage Out）", { x: 0.7, y: 1.35, w: 8.6, h: 0.35, fontSize: 15, fontFace: "Microsoft YaHei", bold: true, color: C.red, margin: 0 });
s3.addText([
  { text: "这是数据科学的第一定律。如果输入的数据有问题，无论算法多先进，输出的结果都是错的。", options: { breakLine: true } },
  { text: "", options: { breakLine: true, fontSize: 4 } },
  { text: "举个例子：", options: { bold: true, breakLine: true } },
  { text: "假设你要计算班级平均分，但有一个同学的成绩被错误录入为 -20 分。这一个异常值就会把全班平均分拉低好几分。", options: { breakLine: true } },
  { text: "在聚类分析中，异常值的影响更大——它会「拽偏」聚类中心的位置，导致整个分群结果失真。", options: { breakLine: true } },
  { text: "", options: { breakLine: true, fontSize: 4 } },
  { text: "所以，数据清洗不是「可选步骤」，而是分析的地基。地基不稳，上面的楼再漂亮也会塌。", options: { bold: true, color: C.green } }
], { x: 0.7, y: 1.75, w: 8.6, h: 1.4, fontSize: 11.5, fontFace: "Microsoft YaHei", color: C.dark, lineSpacingMultiple: 1.3, margin: 0 });

// 三个具体问题
const cleanProblems = [
  { title: "座位数为负", example: "capacity = -2", impact: "拉低均值，扭曲聚类中心", count: "3条" },
  { title: "使用票数为负", example: "ticket_use = -26", impact: "逻辑错误，干扰售票统计", count: "4条" },
  { title: "上座率超100%", example: "occu_perc = 109%", impact: "物理不可能，数据采集错误", count: "7条" },
];
cleanProblems.forEach((p, i) => {
  const px = 0.5 + i * 3.1;
  s3.addShape(pres.shapes.RECTANGLE, { x: px, y: 3.5, w: 2.85, h: 1.7, fill: { color: C.white }, shadow: mkSh() });
  s3.addShape(pres.shapes.RECTANGLE, { x: px, y: 3.5, w: 2.85, h: 0.06, fill: { color: C.red } });
  s3.addText(p.title, { x: px + 0.15, y: 3.65, w: 2.55, h: 0.3, fontSize: 13, fontFace: "Microsoft YaHei", bold: true, color: C.dark, margin: 0 });
  s3.addText(`示例：${p.example}`, { x: px + 0.15, y: 4.0, w: 2.55, h: 0.25, fontSize: 10.5, fontFace: "Consolas", color: C.red, margin: 0 });
  s3.addText(`影响：${p.impact}`, { x: px + 0.15, y: 4.3, w: 2.55, h: 0.25, fontSize: 10.5, fontFace: "Microsoft YaHei", color: C.gray, margin: 0 });
  s3.addShape(pres.shapes.RECTANGLE, { x: px + 0.15, y: 4.65, w: 0.8, h: 0.3, fill: { color: C.greenLight } });
  s3.addText(p.count, { x: px + 0.15, y: 4.65, w: 0.8, h: 0.3, fontSize: 11, fontFace: "Microsoft YaHei", bold: true, color: C.greenDark, align: "center", valign: "middle", margin: 0 });
});

// ======================== S4 数据清洗 - 结果 ========================
let s4 = pres.addSlide();
s4.background = { color: C.cream };
s4.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.06, fill: { color: C.green } });
s4.addText("清洗结果", { x: 0.6, y: 0.25, w: 6, h: 0.55, fontSize: 26, fontFace: "Microsoft YaHei", bold: true, color: C.dark, margin: 0 });
s4.addText("清洗前后的对比", { x: 0.6, y: 0.78, w: 6, h: 0.35, fontSize: 12, fontFace: "Microsoft YaHei", color: C.gray, margin: 0 });

// 清洗前
s4.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 1.3, w: 4.3, h: 2.2, fill: { color: C.white }, shadow: mkSh() });
s4.addText("清洗前", { x: 0.7, y: 1.4, w: 3.9, h: 0.35, fontSize: 15, fontFace: "Microsoft YaHei", bold: true, color: C.red, margin: 0 });
s4.addText([
  { text: "总记录：7,520 条", options: { breakLine: true } },
  { text: "影院数：239 家", options: { breakLine: true } },
  { text: "包含异常值：", options: { breakLine: true } },
  { text: "  · 座位数为负（3条）", options: { breakLine: true } },
  { text: "  · 使用票数为负（4条）", options: { breakLine: true } },
  { text: "  · 上座率超100%（7条）", options: { breakLine: true } },
], { x: 0.7, y: 1.85, w: 3.9, h: 1.5, fontSize: 12, fontFace: "Microsoft YaHei", color: C.dark, lineSpacingMultiple: 1.3, margin: 0 });

// 箭头
s4.addText("→", { x: 4.8, y: 2.0, w: 0.4, h: 0.5, fontSize: 30, color: C.green, align: "center", valign: "middle", margin: 0 });

// 清洗后
s4.addShape(pres.shapes.RECTANGLE, { x: 5.2, y: 1.3, w: 4.3, h: 2.2, fill: { color: C.white }, shadow: mkSh() });
s4.addText("清洗后", { x: 5.4, y: 1.4, w: 3.9, h: 0.35, fontSize: 15, fontFace: "Microsoft YaHei", bold: true, color: C.green, margin: 0 });
s4.addText([
  { text: "总记录：7,506 条（保留 99.8%）", options: { breakLine: true } },
  { text: "影院数：238 家", options: { breakLine: true } },
  { text: "移除异常值：14 条", options: { breakLine: true } },
  { text: "数据质量：全部通过逻辑校验", options: { breakLine: true } },
], { x: 5.4, y: 1.85, w: 3.9, h: 1.5, fontSize: 12, fontFace: "Microsoft YaHei", color: C.dark, lineSpacingMultiple: 1.3, margin: 0 });

// 要点总结
s4.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 3.8, w: 9.0, h: 1.5, fill: { color: "E8F5E9" } });
s4.addText("关键要点", { x: 0.7, y: 3.9, w: 8.6, h: 0.35, fontSize: 14, fontFace: "Microsoft YaHei", bold: true, color: C.green, margin: 0 });
s4.addText([
  { text: "1. 清洗比例很小（0.2%），说明原始数据质量还不错，只是有少量录入错误", options: { breakLine: true } },
  { text: "2. 清洗标准要基于「业务逻辑」：座位数不可能为负，上座率不可能超100%", options: { breakLine: true } },
  { text: "3. 清洗后要检查：是否影响了数据分布？移除的是否确实是错误而非特殊值？", options: {} },
], { x: 0.7, y: 4.3, w: 8.6, h: 0.9, fontSize: 11, fontFace: "Microsoft YaHei", color: C.dark, lineSpacingMultiple: 1.35, margin: 0 });

// ======================== S5 特征工程 - 聚合 ========================
let s5 = pres.addSlide();
s5.background = { color: C.cream };
s5.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.06, fill: { color: C.green } });
s5.addText("阶段二：特征工程 — 聚合", { x: 0.6, y: 0.25, w: 7, h: 0.55, fontSize: 26, fontFace: "Microsoft YaHei", bold: true, color: C.dark, margin: 0 });
s5.addText("为什么要把「场次数据」变成「影院画像」？", { x: 0.6, y: 0.78, w: 7, h: 0.35, fontSize: 12, fontFace: "Microsoft YaHei", color: C.gray, margin: 0 });

s5.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 1.25, w: 9.0, h: 1.6, fill: { color: C.white }, shadow: mkSh() });
s5.addText([
  { text: "原始数据是「影院 × 电影」维度的：", options: { bold: true, breakLine: true } },
  { text: "影院 #352 放映电影 A → 1 条记录\n影院 #352 放映电影 B → 1 条记录\n影院 #352 放映电影 C → 1 条记录", options: { fontFace: "Consolas", fontSize: 11, breakLine: true } },
  { text: "", options: { breakLine: true, fontSize: 4 } },
  { text: "但 K-means 需要每个「样本」是一个特征向量。我们想分析的是影院，不是某次放映。", options: { breakLine: true } },
  { text: "→ 必须按影院聚合：把同一个影院的所有放映记录合并为一条「影院画像」。", options: { bold: true, color: C.green } }
], { x: 0.7, y: 1.35, w: 8.6, h: 1.4, fontSize: 11.5, fontFace: "Microsoft YaHei", color: C.dark, lineSpacingMultiple: 1.3, margin: 0 });

// 聚合过程
s5.addText("聚合过程演示", { x: 0.6, y: 3.05, w: 4, h: 0.35, fontSize: 14, fontFace: "Microsoft YaHei", bold: true, color: C.dark, margin: 0 });

// 左: 聚合前
s5.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 3.5, w: 3.8, h: 1.7, fill: { color: "FFF3E0" } });
s5.addText("聚合前（多条记录）", { x: 0.65, y: 3.55, w: 3.5, h: 0.3, fontSize: 11, fontFace: "Microsoft YaHei", bold: true, color: C.orange, margin: 0 });
s5.addText([
  { text: "影院352 | 电影A | 票房1200万 | 上座率8%", options: { fontFace: "Consolas", fontSize: 9, breakLine: true } },
  { text: "影院352 | 电影B | 票房800万  | 上座率12%", options: { fontFace: "Consolas", fontSize: 9, breakLine: true } },
  { text: "影院352 | 电影C | 票房500万  | 上座率5%", options: { fontFace: "Consolas", fontSize: 9, breakLine: true } },
  { text: "... 共 15 条记录", options: { fontSize: 9, color: C.gray } }
], { x: 0.65, y: 3.9, w: 3.5, h: 1.2, fontSize: 9, fontFace: "Consolas", color: C.dark, lineSpacingMultiple: 1.4, margin: 0 });

s5.addText("→", { x: 4.3, y: 4.0, w: 0.4, h: 0.5, fontSize: 24, color: C.green, align: "center", valign: "middle", margin: 0 });

// 右: 聚合后
s5.addShape(pres.shapes.RECTANGLE, { x: 4.7, y: 3.5, w: 4.8, h: 1.7, fill: { color: "E8F5E9" } });
s5.addText("聚合后（一条画像）", { x: 4.85, y: 3.55, w: 4.5, h: 0.3, fontSize: 11, fontFace: "Microsoft YaHei", bold: true, color: C.green, margin: 0 });
s5.addText([
  { text: "影院352:", options: { bold: true, breakLine: true } },
  { text: "  总票房 = sum(所有电影) = 2500万", options: { fontFace: "Consolas", fontSize: 9.5, breakLine: true } },
  { text: "  平均上座率 = mean(所有电影) = 8.3%", options: { fontFace: "Consolas", fontSize: 9.5, breakLine: true } },
  { text: "  场次数 = count(电影种类) = 15", options: { fontFace: "Consolas", fontSize: 9.5, breakLine: true } },
  { text: "  ... + 其他特征", options: { fontSize: 9.5, color: C.gray } }
], { x: 4.85, y: 3.9, w: 4.5, h: 1.2, fontSize: 9.5, fontFace: "Microsoft YaHei", color: C.dark, lineSpacingMultiple: 1.4, margin: 0 });

// ======================== S6 特征工程 - 标准化 ========================
let s6 = pres.addSlide();
s6.background = { color: C.cream };
s6.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.06, fill: { color: C.green } });
s6.addText("阶段二：特征工程 — 标准化", { x: 0.6, y: 0.25, w: 7, h: 0.55, fontSize: 26, fontFace: "Microsoft YaHei", bold: true, color: C.dark, margin: 0 });
s6.addText("为什么量纲不同会影响聚类结果？", { x: 0.6, y: 0.78, w: 7, h: 0.35, fontSize: 12, fontFace: "Microsoft YaHei", color: C.gray, margin: 0 });

s6.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 1.25, w: 9.0, h: 1.5, fill: { color: C.white }, shadow: mkSh() });
s6.addText("问题：大数值特征会「淹没」小数值特征", { x: 0.7, y: 1.35, w: 8.6, h: 0.35, fontSize: 14, fontFace: "Microsoft YaHei", bold: true, color: C.red, margin: 0 });
s6.addText([
  { text: "K-means 使用欧氏距离：d = √[(x₁-y₁)² + (x₂-y₂)² + ...]", options: { fontFace: "Consolas", fontSize: 12, breakLine: true } },
  { text: "", options: { breakLine: true, fontSize: 4 } },
  { text: "假设影院 A 和 B：票房差 1 亿，上座率差 5%。", options: { breakLine: true } },
  { text: "票房差的平方 = (1亿)² = 10¹⁶    上座率差的平方 = (5)² = 25", options: { fontFace: "Consolas", fontSize: 11, breakLine: true } },
  { text: "→ 距离几乎完全由票房决定，上座率的影响被「淹没」了！", options: { bold: true, color: C.red } }
], { x: 0.7, y: 1.75, w: 8.6, h: 0.9, fontSize: 11.5, fontFace: "Microsoft YaHei", color: C.dark, lineSpacingMultiple: 1.3, margin: 0 });

// 解决方案
s6.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 2.95, w: 4.3, h: 2.2, fill: { color: C.white }, shadow: mkSh() });
s6.addText("解决方案：StandardScaler", { x: 0.7, y: 3.05, w: 3.9, h: 0.35, fontSize: 14, fontFace: "Microsoft YaHei", bold: true, color: C.green, margin: 0 });
s6.addText([
  { text: "公式：z = (x - μ) / σ", options: { fontFace: "Consolas", fontSize: 13, breakLine: true } },
  { text: "", options: { breakLine: true, fontSize: 4 } },
  { text: "μ = 均值，σ = 标准差", options: { breakLine: true } },
  { text: "", options: { breakLine: true, fontSize: 4 } },
  { text: "处理后：每个特征的均值=0，标准差=1", options: { breakLine: true } },
  { text: "所有特征处于同一量级，公平地参与距离计算。", options: { bold: true, color: C.green } }
], { x: 0.7, y: 3.45, w: 3.9, h: 1.5, fontSize: 11.5, fontFace: "Microsoft YaHei", color: C.dark, lineSpacingMultiple: 1.3, margin: 0 });

// 7个特征
s6.addShape(pres.shapes.RECTANGLE, { x: 5.2, y: 2.95, w: 4.3, h: 2.2, fill: { color: C.white }, shadow: mkSh() });
s6.addText("提取的 7 个特征", { x: 5.4, y: 3.05, w: 3.9, h: 0.35, fontSize: 14, fontFace: "Microsoft YaHei", bold: true, color: C.green, margin: 0 });
const featList2 = [
  { n: "total_sales", m: "总票房" }, { n: "tickets_sold", m: "总售票数" },
  { n: "avg_occu", m: "平均上座率" }, { n: "avg_price", m: "平均票价" },
  { n: "avg_capacity", m: "座位容量" }, { n: "show_count", m: "场次数" },
  { n: "film_count", m: "电影种类数" },
];
featList2.forEach((f, i) => {
  const fy = 3.5 + i * 0.23;
  s6.addShape(pres.shapes.RECTANGLE, { x: 5.4, y: fy + 0.02, w: 0.12, h: 0.12, fill: { color: C.green } });
  s6.addText(`${f.n}  →  ${f.m}`, { x: 5.6, y: fy - 0.02, w: 3.5, h: 0.25, fontSize: 10, fontFace: "Consolas", color: C.dark, margin: 0 });
});

// ======================== S7 K-means 原理 ========================
let s7 = pres.addSlide();
s7.background = { color: C.cream };
s7.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.06, fill: { color: C.green } });
s7.addText("阶段三：K-means 聚类 — 原理", { x: 0.6, y: 0.25, w: 8, h: 0.55, fontSize: 26, fontFace: "Microsoft YaHei", bold: true, color: C.dark, margin: 0 });
s7.addText("什么是聚类？为什么选 K-means？", { x: 0.6, y: 0.78, w: 8, h: 0.35, fontSize: 12, fontFace: "Microsoft YaHei", color: C.gray, margin: 0 });

s7.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 1.25, w: 9.0, h: 1.3, fill: { color: C.white }, shadow: mkSh() });
s7.addText([
  { text: "聚类（Clustering）= 无监督学习", options: { bold: true, breakLine: true } },
  { text: "没有标签，让算法自己发现数据中的「群组」。就像把一堆水果分成「苹果堆、香蕉堆、橙子堆」——你不用提前告诉算法水果的名字，它会根据颜色、形状、大小自动分。", options: { breakLine: true } },
  { text: "与分类的区别：分类是「有标签的学习」（已知答案），聚类是「无标签的探索」（不知道会分成什么）。", options: {} }
], { x: 0.7, y: 1.35, w: 8.6, h: 1.1, fontSize: 11.5, fontFace: "Microsoft YaHei", color: C.dark, lineSpacingMultiple: 1.3, margin: 0 });

// 为什么选K-means
s7.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 2.75, w: 4.3, h: 2.4, fill: { color: C.white }, shadow: mkSh() });
s7.addText("为什么选 K-means？", { x: 0.7, y: 2.85, w: 3.9, h: 0.35, fontSize: 14, fontFace: "Microsoft YaHei", bold: true, color: C.green, margin: 0 });
s7.addText([
  { text: "优点：", options: { bold: true, breakLine: true } },
  { text: "· 算法简单，容易理解和实现", options: { breakLine: true } },
  { text: "· 计算效率高，适合中等规模数据", options: { breakLine: true } },
  { text: "· 结果易于解释（每个点明确属于一个簇）", options: { breakLine: true } },
  { text: "· 行业应用广泛，便于业务沟通", options: { breakLine: true } },
  { text: "", options: { breakLine: true, fontSize: 4 } },
  { text: "为什么不用其他方法？", options: { bold: true, color: C.red, breakLine: true } },
  { text: "· DBSCAN：影院密度差异大，难选参数", options: { breakLine: true } },
  { text: "· 层次聚类：238家影院计算量偏大", options: { breakLine: true } },
  { text: "· 高斯混合：数据不一定符合正态分布", options: {} }
], { x: 0.7, y: 3.25, w: 3.9, h: 1.8, fontSize: 10.5, fontFace: "Microsoft YaHei", color: C.dark, lineSpacingMultiple: 1.25, margin: 0 });

// 核心公式
s7.addShape(pres.shapes.RECTANGLE, { x: 5.2, y: 2.75, w: 4.3, h: 2.4, fill: { color: C.white }, shadow: mkSh() });
s7.addText("核心公式", { x: 5.4, y: 2.85, w: 3.9, h: 0.35, fontSize: 14, fontFace: "Microsoft YaHei", bold: true, color: C.green, margin: 0 });
s7.addText([
  { text: "目标函数（惯性值 Inertia）：", options: { bold: true, breakLine: true } },
  { text: "Inertia = Σ min ||xᵢ - μₖ||²", options: { fontFace: "Consolas", fontSize: 14, breakLine: true } },
  { text: "", options: { breakLine: true, fontSize: 4 } },
  { text: "xᵢ = 第 i 个样本点", options: { breakLine: true } },
  { text: "μₖ = 第 k 个簇的中心（均值）", options: { breakLine: true } },
  { text: "||·|| = 欧氏距离", options: { breakLine: true } },
  { text: "", options: { breakLine: true, fontSize: 4 } },
  { text: "Inertia 越小 → 簇内越紧凑 → 聚类效果越好", options: { bold: true, color: C.green, breakLine: true } },
  { text: "但 K 越大 Inertia 越小，需要权衡。", options: {} }
], { x: 5.4, y: 3.25, w: 3.9, h: 1.8, fontSize: 11, fontFace: "Microsoft YaHei", color: C.dark, lineSpacingMultiple: 1.25, margin: 0 });

// ======================== S8 K-means 算法步骤 ========================
let s8 = pres.addSlide();
s8.background = { color: C.cream };
s8.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.06, fill: { color: C.green } });
s8.addText("K-means 算法执行步骤", { x: 0.6, y: 0.25, w: 7, h: 0.55, fontSize: 26, fontFace: "Microsoft YaHei", bold: true, color: C.dark, margin: 0 });
s8.addText("一步步看算法是怎么工作的", { x: 0.6, y: 0.78, w: 7, h: 0.35, fontSize: 12, fontFace: "Microsoft YaHei", color: C.gray, margin: 0 });

const algoSteps = [
  { num: "1", title: "初始化", desc: "随机选 K 个点作为初始聚类中心。\n\n初始点的选择会影响最终结果，所以通常会随机初始化多次，取最好的那次。" },
  { num: "2", title: "计算距离", desc: "对每个样本，计算它到 K 个中心的欧氏距离。\n\nd = √[(x₁-μ₁)² + (x₂-μ₂)² + ...]" },
  { num: "3", title: "分配簇", desc: "每个样本归入距离最近的那个簇。\n\n就像把学生分到最近的老师那里。" },
  { num: "4", title: "更新中心", desc: "每个簇的所有样本取均值，作为新的聚类中心。\n\n新中心 = 簇内所有点的平均位置。" },
  { num: "5", title: "迭代收敛", desc: "重复步骤 2-4，直到中心不再变化（或变化很小）。\n\n这时算法「收敛」了，得到最终结果。" },
];
algoSteps.forEach((st, i) => {
  const ax = 0.3 + i * 1.9;
  s8.addShape(pres.shapes.RECTANGLE, { x: ax, y: 1.3, w: 1.7, h: 3.8, fill: { color: C.white }, shadow: mkSh() });
  s8.addShape(pres.shapes.OVAL, { x: ax + 0.6, y: 1.45, w: 0.5, h: 0.5, fill: { color: C.green } });
  s8.addText(st.num, { x: ax + 0.6, y: 1.45, w: 0.5, h: 0.5, fontSize: 18, fontFace: "Microsoft YaHei", bold: true, color: C.white, align: "center", valign: "middle", margin: 0 });
  s8.addText(st.title, { x: ax + 0.05, y: 2.05, w: 1.6, h: 0.3, fontSize: 13, fontFace: "Microsoft YaHei", bold: true, color: C.dark, align: "center", margin: 0 });
  s8.addText(st.desc, { x: ax + 0.1, y: 2.4, w: 1.5, h: 2.5, fontSize: 9.5, fontFace: "Microsoft YaHei", color: C.gray, lineSpacingMultiple: 1.25, margin: 0 });
  if (i < 4) s8.addText("→", { x: ax + 1.7, y: 2.8, w: 0.2, h: 0.3, fontSize: 14, color: C.green, align: "center", valign: "middle", margin: 0 });
});

// ======================== S9 肘部法 ========================
let s9 = pres.addSlide();
s9.background = { color: C.cream };
s9.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.06, fill: { color: C.green } });
s9.addText("关键问题：K 取多少？", { x: 0.6, y: 0.25, w: 7, h: 0.55, fontSize: 26, fontFace: "Microsoft YaHei", bold: true, color: C.dark, margin: 0 });
s9.addText("肘部法（Elbow Method）原理", { x: 0.6, y: 0.78, w: 7, h: 0.35, fontSize: 12, fontFace: "Microsoft YaHei", color: C.gray, margin: 0 });

s9.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 1.25, w: 9.0, h: 1.3, fill: { color: C.white }, shadow: mkSh() });
s9.addText([
  { text: "K-means 的痛点：需要预先指定 K（聚类数）。", options: { bold: true, breakLine: true } },
  { text: "", options: { breakLine: true, fontSize: 4 } },
  { text: "K 太小 → 簇内差异大，分得不够细；K 太大 → 簇内太相似，分得太碎（极端情况：K=样本数时每个点自成一类）。", options: { breakLine: true } },
  { text: "", options: { breakLine: true, fontSize: 4 } },
  { text: "肘部法：让 K 从 2 变到 10，画出 Inertia 曲线。曲线从「陡」变「缓」的拐点就像人的手肘，那个位置就是最优 K。", options: { bold: true, color: C.green } }
], { x: 0.7, y: 1.35, w: 8.6, h: 1.1, fontSize: 11.5, fontFace: "Microsoft YaHei", color: C.dark, lineSpacingMultiple: 1.3, margin: 0 });

// 嵌入图
s9.addImage({ path: path.join(__dirname, "images/03_elbow.png"), x: 0.3, y: 2.75, w: 5.5, h: 2.6 });

// 右侧分析
s9.addShape(pres.shapes.RECTANGLE, { x: 6.1, y: 2.75, w: 3.5, h: 2.6, fill: { color: C.white }, shadow: mkSh() });
s9.addText("我们的分析", { x: 6.3, y: 2.85, w: 3.1, h: 0.3, fontSize: 13, fontFace: "Microsoft YaHei", bold: true, color: C.green, margin: 0 });
s9.addText([
  { text: "K=2 → 3：", options: { bold: true, breakLine: true } },
  { text: "Inertia 从 1047 降到 815，下降 22%", options: { breakLine: true } },
  { text: "", options: { breakLine: true, fontSize: 3 } },
  { text: "K=3 → 4：", options: { bold: true, breakLine: true } },
  { text: "从 815 降到 645，下降 21%，仍有明显改善", options: { breakLine: true } },
  { text: "", options: { breakLine: true, fontSize: 3 } },
  { text: "K=4 → 5：", options: { bold: true, breakLine: true } },
  { text: "从 645 降到 541，下降 16%，改善趋缓", options: { breakLine: true } },
  { text: "", options: { breakLine: true, fontSize: 3 } },
  { text: "结论：K=4 是拐点，且业务含义清晰", options: { bold: true, color: C.green } }
], { x: 6.3, y: 3.25, w: 3.1, h: 2.0, fontSize: 10.5, fontFace: "Microsoft YaHei", color: C.dark, lineSpacingMultiple: 1.25, margin: 0 });

// ======================== S10 聚类结果解读 ========================
let s10 = pres.addSlide();
s10.background = { color: C.cream };
s10.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.06, fill: { color: C.green } });
s10.addText("聚类结果：4 类影院画像", { x: 0.6, y: 0.25, w: 7, h: 0.55, fontSize: 26, fontFace: "Microsoft YaHei", bold: true, color: C.dark, margin: 0 });
s10.addText("每个类别有什么特征？为什么会分成这样？", { x: 0.6, y: 0.78, w: 7, h: 0.35, fontSize: 12, fontFace: "Microsoft YaHei", color: C.gray, margin: 0 });

// PCA 图
s10.addImage({ path: path.join(__dirname, "images/04_cluster_pca.png"), x: 0.3, y: 1.2, w: 4.8, h: 3.8 });

// 右侧详解
const clDetails = [
  { name: "顶级影院", count: "5家 (2.1%)", color: C.red, stats: "票房60亿 | 上座率38% | 票价11.9万", why: "少数巨头影院，票房和上座率都远超平均。场次多、覆盖电影广，是首映的首选。" },
  { name: "热门影院", count: "43家 (18%)", color: C.orange, stats: "票房9.8亿 | 上座率28% | 票价9.5万", why: "中坚力量，各项指标中上。运营效率好，适合作为备选或点映场。" },
  { name: "中等影院", count: "40家 (17%)", color: C.blue, stats: "票房2.2亿 | 上座率6.6% | 票价6.9万", why: "上座率偏低，场次少。可能是选址或经营策略问题，有提升空间。" },
  { name: "普通影院", count: "150家 (63%)", color: C.gray, stats: "票房0.9亿 | 上座率13% | 票价6.0万", why: "数量最多但单体贡献小。覆盖广泛的基础观众群体。" },
];
clDetails.forEach((cl, i) => {
  const cy = 1.2 + i * 1.0;
  s10.addShape(pres.shapes.RECTANGLE, { x: 5.3, y: cy, w: 4.3, h: 0.88, fill: { color: C.white }, shadow: mkSh() });
  s10.addShape(pres.shapes.RECTANGLE, { x: 5.3, y: cy, w: 0.08, h: 0.88, fill: { color: cl.color } });
  s10.addText(cl.name, { x: 5.55, y: cy + 0.05, w: 1.3, h: 0.22, fontSize: 12, fontFace: "Microsoft YaHei", bold: true, color: C.dark, margin: 0 });
  s10.addText(cl.count, { x: 5.55, y: cy + 0.27, w: 1.3, h: 0.18, fontSize: 9, fontFace: "Microsoft YaHei", color: C.gray, margin: 0 });
  s10.addText(cl.stats, { x: 5.55, y: cy + 0.48, w: 3.8, h: 0.18, fontSize: 8.5, fontFace: "Consolas", color: C.green, margin: 0 });
  s10.addText(cl.why, { x: 5.55, y: cy + 0.65, w: 3.8, h: 0.2, fontSize: 8.5, fontFace: "Microsoft YaHei", color: C.gray, margin: 0 });
});

// ======================== S11 特征对比图 ========================
let s11 = pres.addSlide();
s11.background = { color: C.cream };
s11.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.06, fill: { color: C.green } });
s11.addText("各簇特征对比", { x: 0.6, y: 0.25, w: 6, h: 0.55, fontSize: 26, fontFace: "Microsoft YaHei", bold: true, color: C.dark, margin: 0 });
s11.addText("用图表直观对比 4 类影院的差异", { x: 0.6, y: 0.78, w: 6, h: 0.35, fontSize: 12, fontFace: "Microsoft YaHei", color: C.gray, margin: 0 });
s11.addImage({ path: path.join(__dirname, "images/05_cluster_compare.png"), x: 0.3, y: 1.2, w: 9.4, h: 3.8 });
s11.addText("顶级影院在所有维度都遥遥领先，说明「强者恒强」——高票房的影院往往上座率也高、票价也高。", {
  x: 0.5, y: 5.1, w: 9.0, h: 0.4, fontSize: 11, fontFace: "Microsoft YaHei", color: C.gray, italic: true, margin: 0
});

// ======================== S12 综合评分 ========================
let s12 = pres.addSlide();
s12.background = { color: C.cream };
s12.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.06, fill: { color: C.green } });
s12.addText("阶段四：综合评分", { x: 0.6, y: 0.25, w: 7, h: 0.55, fontSize: 26, fontFace: "Microsoft YaHei", bold: true, color: C.dark, margin: 0 });
s12.addText("如何从聚类结果中选出最佳影院？", { x: 0.6, y: 0.78, w: 7, h: 0.35, fontSize: 12, fontFace: "Microsoft YaHei", color: C.gray, margin: 0 });

s12.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 1.25, w: 9.0, h: 1.2, fill: { color: C.white }, shadow: mkSh() });
s12.addText([
  { text: "聚类只告诉我们「影院属于哪一类」，但同一类里哪家更好？需要一个评分模型。", options: { breakLine: true } },
  { text: "", options: { breakLine: true, fontSize: 4 } },
  { text: "评分公式：", options: { bold: true, breakLine: true } },
  { text: "Score = MinMax(票房) × 0.3 + MinMax(上座率) × 0.3 + MinMax(场次) × 0.2 + MinMax(电影数) × 0.2", options: { fontFace: "Consolas", fontSize: 12, color: C.green } }
], { x: 0.7, y: 1.35, w: 8.6, h: 1.0, fontSize: 11.5, fontFace: "Microsoft YaHei", color: C.dark, lineSpacingMultiple: 1.3, margin: 0 });

// 权重解释
s12.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 2.65, w: 4.3, h: 1.5, fill: { color: "E8F5E9" } });
s12.addText("为什么用这个权重？", { x: 0.7, y: 2.75, w: 3.9, h: 0.3, fontSize: 13, fontFace: "Microsoft YaHei", bold: true, color: C.green, margin: 0 });
s12.addText([
  { text: "票房 30%：首映要「卖得多」，票房是硬指标", options: { breakLine: true } },
  { text: "上座率 30%：首映要「坐得满」，人气是关键", options: { breakLine: true } },
  { text: "场次 20%：排片密度反映影院的排片能力", options: { breakLine: true } },
  { text: "电影数 20%：内容丰富度反映影院的综合实力", options: {} }
], { x: 0.7, y: 3.1, w: 3.9, h: 0.95, fontSize: 10.5, fontFace: "Microsoft YaHei", color: C.dark, lineSpacingMultiple: 1.25, margin: 0 });

// 为什么用MinMax
s12.addShape(pres.shapes.RECTANGLE, { x: 5.2, y: 2.65, w: 4.3, h: 1.5, fill: { color: "FFF3E0" } });
s12.addText("为什么用 MinMax 而不是原始值？", { x: 5.4, y: 2.75, w: 3.9, h: 0.3, fontSize: 13, fontFace: "Microsoft YaHei", bold: true, color: C.orange, margin: 0 });
s12.addText([
  { text: "MinMax 归一化：x' = (x - min) / (max - min)", options: { fontFace: "Consolas", fontSize: 10.5, breakLine: true } },
  { text: "", options: { breakLine: true, fontSize: 3 } },
  { text: "处理后所有值在 [0, 1] 范围内。", options: { breakLine: true } },
  { text: "这样不同量纲的指标可以直接加权求和，", options: { breakLine: true } },
  { text: "不会因为某个指标数值大就主导总分。", options: {} }
], { x: 5.4, y: 3.1, w: 3.9, h: 0.95, fontSize: 10.5, fontFace: "Microsoft YaHei", color: C.dark, lineSpacingMultiple: 1.25, margin: 0 });

// TOP10 图（加大高度，确保10条柱状图清晰可见）
s12.addImage({ path: path.join(__dirname, "images/06_top10_recommend.png"), x: 0.3, y: 4.1, w: 5.5, h: 1.9 });

// 推荐卡片（同步加大高度）
s12.addShape(pres.shapes.RECTANGLE, { x: 6.0, y: 4.1, w: 3.6, h: 1.9, fill: { color: C.green }, shadow: mkSh() });
s12.addText([
  { text: "推荐：影院 #448", options: { bold: true, breakLine: true } },
  { text: "评分 0.847 | 票房 120.61亿 | 上座率 38.5%", options: { breakLine: true } },
  { text: "遥遥领先，是首映的最佳选择", options: {} }
], { x: 6.15, y: 4.5, w: 3.3, h: 1.2, fontSize: 11, fontFace: "Microsoft YaHei", color: C.white, lineSpacingMultiple: 1.3, margin: 0 });

// ======================== S13 可视化技术 ========================
let s13 = pres.addSlide();
s13.background = { color: C.cream };
s13.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.06, fill: { color: C.green } });
s13.addText("阶段五：数据可视化", { x: 0.6, y: 0.25, w: 7, h: 0.55, fontSize: 26, fontFace: "Microsoft YaHei", bold: true, color: C.dark, margin: 0 });
s13.addText("用图表让数据「说话」", { x: 0.6, y: 0.78, w: 7, h: 0.35, fontSize: 12, fontFace: "Microsoft YaHei", color: C.gray, margin: 0 });

// 6种图表说明
const chartTypes = [
  { name: "直方图", why: "看数据分布", example: "大部分影院票房在什么范围？" },
  { name: "散点图", why: "看变量关系", example: "上座率和票价有关系吗？" },
  { name: "肘部图", why: "选参数", example: "K 取多少最合适？" },
  { name: "PCA图", why: "看聚类效果", example: "4 类影院分得开吗？" },
  { name: "柱状图", why: "对比差异", example: "各类影院差距有多大？" },
  { name: "条形图", why: "排名展示", example: "TOP10 推荐是谁？" },
];
chartTypes.forEach((ch, i) => {
  const col = i % 3;
  const row = Math.floor(i / 3);
  const cx = 0.5 + col * 3.1;
  const cy = 1.3 + row * 1.5;
  s13.addShape(pres.shapes.RECTANGLE, { x: cx, y: cy, w: 2.85, h: 1.3, fill: { color: C.white }, shadow: mkSh() });
  s13.addShape(pres.shapes.RECTANGLE, { x: cx, y: cy, w: 0.08, h: 1.3, fill: { color: C.green } });
  s13.addText(ch.name, { x: cx + 0.2, y: cy + 0.1, w: 2.5, h: 0.3, fontSize: 14, fontFace: "Microsoft YaHei", bold: true, color: C.dark, margin: 0 });
  s13.addText(ch.why, { x: cx + 0.2, y: cy + 0.4, w: 2.5, h: 0.25, fontSize: 11, fontFace: "Microsoft YaHei", color: C.green, margin: 0 });
  s13.addText(ch.example, { x: cx + 0.2, y: cy + 0.7, w: 2.5, h: 0.45, fontSize: 10.5, fontFace: "Microsoft YaHei", color: C.gray, italic: true, margin: 0 });
});

s13.addShape(pres.shapes.RECTANGLE, { x: 0.5, y: 4.4, w: 9.0, h: 0.9, fill: { color: "E8F5E9" } });
s13.addText("本次分析共生成 6 张图表，覆盖从数据探索到结果展示的全流程。每张图都有明确的目的，不是为了「好看」而是为了「看懂」。", {
  x: 0.7, y: 4.5, w: 8.6, h: 0.7, fontSize: 12, fontFace: "Microsoft YaHei", color: C.dark, margin: 0
});

// ======================== S14 技术总结 ========================
let s14 = pres.addSlide();
s14.background = { color: C.green };
s14.addShape(pres.shapes.OVAL, { x: 8, y: -1, w: 3.5, h: 3.5, fill: { color: C.greenDark, transparency: 30 } });
s14.addShape(pres.shapes.OVAL, { x: -1, y: 4, w: 3, h: 3, fill: { color: C.greenDark, transparency: 30 } });
s14.addShape(pres.shapes.RECTANGLE, { x: 1.0, y: 0.5, w: 8.0, h: 4.6, fill: { color: C.white }, shadow: mkSh() });
s14.addText("技术总结", { x: 1.3, y: 0.7, w: 7.4, h: 0.5, fontSize: 26, fontFace: "Microsoft YaHei", bold: true, color: C.dark, margin: 0 });

const summaryCols = [
  { title: "数据处理", items: ["数据清洗：移除逻辑异常值", "特征聚合：从场次→影院维度", "标准化：消除量纲影响", "归一化：统一评分尺度"] },
  { title: "机器学习", items: ["K-means：基于距离的聚类", "肘部法：数据驱动选 K", "PCA：高维→低维可视化", "聚类中心：理解各群特征"] },
  { title: "业务洞察", items: ["影院分层：4类差异化画像", "评分模型：多维度加权决策", "推荐结果：数据驱动选址", "可复用：其他场景同样适用"] },
];
summaryCols.forEach((col, i) => {
  const mx = 1.3 + i * 2.5;
  s14.addShape(pres.shapes.RECTANGLE, { x: mx, y: 1.4, w: 2.2, h: 0.4, fill: { color: C.green } });
  s14.addText(col.title, { x: mx, y: 1.4, w: 2.2, h: 0.4, fontSize: 13, fontFace: "Microsoft YaHei", bold: true, color: C.white, align: "center", valign: "middle", margin: 0 });
  col.items.forEach((item, j) => {
    s14.addShape(pres.shapes.RECTANGLE, { x: mx, y: 2.0 + j * 0.55, w: 0.12, h: 0.12, fill: { color: C.green } });
    s14.addText(item, { x: mx + 0.22, y: 1.95 + j * 0.55, w: 1.9, h: 0.45, fontSize: 10.5, fontFace: "Microsoft YaHei", color: C.dark, lineSpacingMultiple: 1.2, margin: 0 });
  });
});
s14.addText("Python 大数据分析结课作业  ·  不如吃茶去", {
  x: 1.3, y: 4.6, w: 7.4, h: 0.35, fontSize: 12, fontFace: "Microsoft YaHei", color: C.gray, align: "center", margin: 0
});

// ======================== 保存 ========================
const outPath = path.join(__dirname, "实验分析流程与技术原理.pptx");
pres.writeFile({ fileName: outPath }).then(() => {
  console.log("PPT 已生成:", outPath);
  console.log("共 14 页幻灯片");
}).catch(err => {
  console.error("生成失败:", err);
});
