const pptxgen = require("pptxgenjs");

const pres = new pptxgen();
pres.layout = "LAYOUT_16x9";
pres.author = "Hinata";
pres.title = "PyCharm 团队协作开发项目流程";

// ============================================================
// COLOR PALETTE — 鹤顶红 × 女贞黄
// ============================================================
const C = {
  navy:      "C0392B",   // 鹤顶红深 - 标题
  blue:      "D44636",   // 鹤顶红 - 主强调
  teal:      "D44636",   // 鹤顶红 - 统一主色
  gold:      "E8A838",   // 暖金 - 辅助点缀
  dark:      "3D3229",   // 深褐 - 正文
  mid:       "8C7E6A",   // 暖灰 - 副文本
  light:     "F5EDDA",   // 暖白 - 分隔线/浅色
  white:     "FFFFFF",
  bg:        "FBEEAF",   // 女贞黄 - 页面背景
  cardBg:    "FFFFFF",
  red:       "C0392B",   // 深红 - 痛点
  green:     "6B8E4E",   // 苔绿 - 解决方案
  orange:    "D44636",   // 鹤顶红 - 复用
  purple:    "8E5A3A",   // 赭石 - 复用
};

// Fresh shadow factory — never reuse objects
const mkShadow = () => ({
  type: "outer", blur: 6, offset: 2, angle: 135, color: "000000", opacity: 0.10,
});

// ============================================================
// SLIDE 1: TITLE
// ============================================================
const s1 = pres.addSlide();
s1.background = { color: C.navy };

// Decorative accent — top-right block
s1.addShape(pres.shapes.RECTANGLE, {
  x: 7.2, y: 0, w: 2.8, h: 2.0,
  fill: { color: C.blue, transparency: 70 },
});

// Decorative accent — bottom-left block
s1.addShape(pres.shapes.RECTANGLE, {
  x: 0, y: 3.8, w: 2.5, h: 1.825,
  fill: { color: C.teal, transparency: 75 },
});

// Accent bar
s1.addShape(pres.shapes.RECTANGLE, {
  x: 0.8, y: 1.6, w: 0.8, h: 0.06,
  fill: { color: C.teal },
});

// Main title
s1.addText("PyCharm", {
  x: 0.8, y: 1.8, w: 8.4, h: 1.0,
  fontSize: 48, fontFace: "Trebuchet MS", color: C.white,
  bold: true, margin: 0,
});

s1.addText("团队协作开发项目流程", {
  x: 0.8, y: 2.7, w: 8.4, h: 0.9,
  fontSize: 36, fontFace: "Trebuchet MS", color: C.white,
  bold: true, margin: 0,
});

// Subtitle
s1.addText("从项目初始化到持续交付的完整协作指南", {
  x: 0.8, y: 3.7, w: 8.4, h: 0.5,
  fontSize: 16, fontFace: "Calibri", color: C.mid,
  margin: 0,
});

// Bottom bar
s1.addShape(pres.shapes.RECTANGLE, {
  x: 0, y: 4.9, w: 10, h: 0.725,
  fill: { color: "8B2E1E" },
});
s1.addText("高效协作  |  规范开发  |  持续交付  |  质量保障", {
  x: 0.8, y: 4.95, w: 8.4, h: 0.6,
  fontSize: 14, fontFace: "Calibri", color: C.light,
  margin: 0,
});

// ============================================================
// SLIDE 2: 目录
// ============================================================
const s2 = pres.addSlide();
s2.background = { color: C.bg };

s2.addShape(pres.shapes.RECTANGLE, {
  x: 0, y: 0, w: 10, h: 0.06,
  fill: { color: C.blue },
});

s2.addText("目  录", {
  x: 0.5, y: 0.3, w: 3, h: 0.7,
  fontSize: 30, fontFace: "Trebuchet MS", color: C.navy,
  bold: true, margin: 0,
});
s2.addText("AGENDA", {
  x: 0.5, y: 0.85, w: 3, h: 0.4,
  fontSize: 12, fontFace: "Calibri", color: C.mid,
  margin: 0,
});

s2.addShape(pres.shapes.RECTANGLE, {
  x: 0.5, y: 1.35, w: 9.0, h: 0.02,
  fill: { color: C.light },
});

const agendaItems = [
  { num: "01", title: "团队协作概述", desc: "为什么需要规范化协作流程" },
  { num: "02", title: "项目初始化", desc: "PyCharm 创建项目与环境配置" },
  { num: "03", title: "Git 版本控制", desc: "PyCharm 内置 Git 操作详解" },
  { num: "04", title: "分支策略", desc: "Git Flow 工作流与分支管理" },
  { num: "05", title: "开发流程", desc: "编码 - 提交 - 审查 - 合并" },
  { num: "06", title: "代码审查", desc: "Code Review 工具与最佳实践" },
  { num: "07", title: "调试与测试", desc: "调试器、pytest 与 CI 集成" },
  { num: "08", title: "远程协作", desc: "Code With Me 与远程开发" },
  { num: "09", title: "最佳实践", desc: "团队规范与约定" },
  { num: "10", title: "总结与 Q&A", desc: "关键要点回顾" },
];

agendaItems.forEach((item, i) => {
  const col = i < 5 ? 0 : 1;
  const row = i < 5 ? i : i - 5;
  const ax = 0.5 + col * 4.7;
  const ay = 1.6 + row * 0.82;

  s2.addShape(pres.shapes.OVAL, {
    x: ax, y: ay + 0.1, w: 0.45, h: 0.45,
    fill: { color: C.blue },
  });
  s2.addText(item.num, {
    x: ax, y: ay + 0.1, w: 0.45, h: 0.45,
    fontSize: 13, fontFace: "Trebuchet MS", color: C.white,
    bold: true, align: "center", valign: "middle", margin: 0,
  });
  s2.addText(item.title, {
    x: ax + 0.6, y: ay + 0.05, w: 3.5, h: 0.35,
    fontSize: 14, fontFace: "Trebuchet MS", color: C.navy,
    bold: true, valign: "middle", margin: 0,
  });
  s2.addText(item.desc, {
    x: ax + 0.6, y: ay + 0.38, w: 3.5, h: 0.3,
    fontSize: 10.5, fontFace: "Calibri", color: C.mid,
    valign: "top", margin: 0,
  });
});

// ============================================================
// SLIDE 3: 团队协作概述
// ============================================================
const s3 = pres.addSlide();
s3.background = { color: C.bg };

s3.addShape(pres.shapes.RECTANGLE, {
  x: 0, y: 0, w: 10, h: 0.06,
  fill: { color: C.blue },
});
s3.addText("01", {
  x: 0.5, y: 0.3, w: 0.6, h: 0.55,
  fontSize: 22, fontFace: "Trebuchet MS", color: C.blue,
  bold: true, align: "center", valign: "middle", margin: 0,
});
s3.addText("团队协作概述", {
  x: 1.15, y: 0.3, w: 8.0, h: 0.55,
  fontSize: 26, fontFace: "Trebuchet MS", color: C.navy,
  bold: true, valign: "middle", margin: 0,
});
s3.addShape(pres.shapes.RECTANGLE, {
  x: 0.5, y: 0.95, w: 9.0, h: 0.02,
  fill: { color: C.light },
});

// Left: pain points
s3.addShape(pres.shapes.RECTANGLE, {
  x: 0.5, y: 1.2, w: 4.3, h: 3.8,
  fill: { color: C.white },
  shadow: mkShadow(),
});
s3.addShape(pres.shapes.RECTANGLE, {
  x: 0.5, y: 1.2, w: 4.3, h: 0.5,
  fill: { color: C.red },
});
s3.addText("痛点与挑战", {
  x: 0.7, y: 1.2, w: 3.9, h: 0.5,
  fontSize: 15, fontFace: "Trebuchet MS", color: C.white,
  bold: true, valign: "middle", margin: 0,
});

const painPoints = [
  "代码冲突频发，合并困难",
  "缺乏统一编码规范",
  "分支管理混乱",
  "Code Review 流于形式",
  "调试环境不一致",
];

painPoints.forEach((p, i) => {
  s3.addText("✕  " + p, {
    x: 0.8, y: 1.85 + i * 0.55, w: 3.8, h: 0.45,
    fontSize: 12.5, fontFace: "Calibri", color: C.dark,
    valign: "middle", margin: 0,
  });
});

// Right: solutions
s3.addShape(pres.shapes.RECTANGLE, {
  x: 5.2, y: 1.2, w: 4.3, h: 3.8,
  fill: { color: C.white },
  shadow: mkShadow(),
});
s3.addShape(pres.shapes.RECTANGLE, {
  x: 5.2, y: 1.2, w: 4.3, h: 0.5,
  fill: { color: C.green },
});
s3.addText("PyCharm 解决方案", {
  x: 5.4, y: 1.2, w: 3.9, h: 0.5,
  fontSize: 15, fontFace: "Trebuchet MS", color: C.white,
  bold: true, valign: "middle", margin: 0,
});

const solutions = [
  "内置 Git 可视化操作",
  "代码风格统一配置 + 一键格式化",
  "图形化分支管理与合并",
  "内置 Code Review 工具",
  "远程解释器 + Docker 集成",
];

solutions.forEach((s, i) => {
  s3.addText("✓  " + s, {
    x: 5.5, y: 1.85 + i * 0.55, w: 3.8, h: 0.45,
    fontSize: 12.5, fontFace: "Calibri", color: C.dark,
    valign: "middle", margin: 0,
  });
});

// ============================================================
// SLIDE 4: 项目初始化
// ============================================================
const s4 = pres.addSlide();
s4.background = { color: C.bg };

s4.addShape(pres.shapes.RECTANGLE, {
  x: 0, y: 0, w: 10, h: 0.06,
  fill: { color: C.blue },
});
s4.addText("02", {
  x: 0.5, y: 0.3, w: 0.6, h: 0.55,
  fontSize: 22, fontFace: "Trebuchet MS", color: C.blue,
  bold: true, align: "center", valign: "middle", margin: 0,
});
s4.addText("项目初始化", {
  x: 1.15, y: 0.3, w: 8.0, h: 0.55,
  fontSize: 26, fontFace: "Trebuchet MS", color: C.navy,
  bold: true, valign: "middle", margin: 0,
});
s4.addShape(pres.shapes.RECTANGLE, {
  x: 0.5, y: 0.95, w: 9.0, h: 0.02,
  fill: { color: C.light },
});

const initSteps = [
  { num: "01", title: "创建项目", desc: "File > New Project\n选择解释器类型\nVirtualenv / Conda / Docker", color: C.blue },
  { num: "02", title: "配置解释器", desc: "Settings > Project\n安装项目依赖\nrequirements.txt", color: C.teal },
  { num: "03", title: "启用 Git", desc: "VCS > Enable VCS\n初始化仓库\n.gitignore 配置", color: C.green },
  { num: "04", title: "连接远程", desc: "Git > Remotes\nSSH Key 认证\n首次 Push", color: C.gold },
];

const cardW = 2.05, cardH = 2.8, cardGap = 0.25;
const startX = (10 - (cardW * 4 + cardGap * 3)) / 2;

initSteps.forEach((step, i) => {
  const cx = startX + i * (cardW + cardGap);
  const cy = 1.3;

  // Card
  s4.addShape(pres.shapes.RECTANGLE, {
    x: cx, y: cy, w: cardW, h: cardH,
    fill: { color: C.white },
    shadow: mkShadow(),
  });

  // Accent bar on top
  s4.addShape(pres.shapes.RECTANGLE, {
    x: cx, y: cy, w: cardW, h: 0.05,
    fill: { color: step.color },
  });

  // Number circle
  s4.addShape(pres.shapes.OVAL, {
    x: cx + (cardW - 0.6) / 2, y: cy + 0.3, w: 0.6, h: 0.6,
    fill: { color: step.color },
  });
  s4.addText(step.num, {
    x: cx + (cardW - 0.6) / 2, y: cy + 0.3, w: 0.6, h: 0.6,
    fontSize: 18, fontFace: "Trebuchet MS", color: C.white,
    bold: true, align: "center", valign: "middle", margin: 0,
  });

  // Title
  s4.addText(step.title, {
    x: cx + 0.1, y: cy + 1.05, w: cardW - 0.2, h: 0.4,
    fontSize: 15, fontFace: "Trebuchet MS", color: C.navy,
    bold: true, align: "center", valign: "middle", margin: 0,
  });

  // Description
  s4.addText(step.desc, {
    x: cx + 0.15, y: cy + 1.5, w: cardW - 0.3, h: 1.1,
    fontSize: 11, fontFace: "Calibri", color: C.mid,
    align: "center", valign: "top", margin: 0,
    lineSpacingMultiple: 1.3,
  });
});

// Arrow connectors
for (let i = 0; i < 3; i++) {
  const ax = startX + (i + 1) * cardW + i * cardGap + cardGap * 0.3;
  s4.addText("→", {
    x: ax, y: 2.4, w: cardGap, h: 0.5,
    fontSize: 20, fontFace: "Arial", color: C.mid,
    align: "center", valign: "middle", margin: 0,
  });
}

// Tip
s4.addShape(pres.shapes.RECTANGLE, {
  x: 0.5, y: 4.4, w: 9.0, h: 0.55,
  fill: { color: "FFF8E7" },
});
s4.addText("Pro Tip: 使用 SSH Key 认证避免每次输入密码；推荐使用 Virtualenv 隔离项目依赖", {
  x: 0.7, y: 4.4, w: 8.6, h: 0.55,
  fontSize: 12, fontFace: "Calibri", color: C.dark,
  valign: "middle", margin: 0,
});

// ============================================================
// SLIDE 5: Git 版本控制
// ============================================================
const s5 = pres.addSlide();
s5.background = { color: C.bg };

s5.addShape(pres.shapes.RECTANGLE, {
  x: 0, y: 0, w: 10, h: 0.06,
  fill: { color: C.blue },
});
s5.addText("03", {
  x: 0.5, y: 0.3, w: 0.6, h: 0.55,
  fontSize: 22, fontFace: "Trebuchet MS", color: C.blue,
  bold: true, align: "center", valign: "middle", margin: 0,
});
s5.addText("Git 版本控制集成", {
  x: 1.15, y: 0.3, w: 8.0, h: 0.55,
  fontSize: 26, fontFace: "Trebuchet MS", color: C.navy,
  bold: true, valign: "middle", margin: 0,
});
s5.addShape(pres.shapes.RECTANGLE, {
  x: 0.5, y: 0.95, w: 9.0, h: 0.02,
  fill: { color: C.light },
});

// Left: Git features
s5.addShape(pres.shapes.RECTANGLE, {
  x: 0.5, y: 1.2, w: 5.5, h: 3.8,
  fill: { color: C.white },
  shadow: mkShadow(),
});
s5.addText("PyCharm Git 功能", {
  x: 0.7, y: 1.35, w: 5.1, h: 0.45,
  fontSize: 16, fontFace: "Trebuchet MS", color: C.navy,
  bold: true, margin: 0,
});

const gitFeatures = [
  { title: "可视化 Diff", desc: "逐行对比代码变更，支持合并冲突解决" },
  { title: "Local History", desc: "自动记录文件变更，随时回退到任意版本" },
  { title: "Interactive Rebase", desc: "图形化整理提交历史，保持分支整洁" },
  { title: "Cherry-Pick", desc: "精确选择提交，跨分支应用变更" },
  { title: "Blame 查看", desc: "追溯每行代码的修改人与时间" },
];

gitFeatures.forEach((f, i) => {
  const fy = 1.95 + i * 0.6;
  s5.addShape(pres.shapes.OVAL, {
    x: 0.8, y: fy + 0.08, w: 0.22, h: 0.22,
    fill: { color: C.blue },
  });
  s5.addText(f.title, {
    x: 1.15, y: fy, w: 2.0, h: 0.35,
    fontSize: 12.5, fontFace: "Trebuchet MS", color: C.navy,
    bold: true, valign: "middle", margin: 0,
  });
  s5.addText(f.desc, {
    x: 3.15, y: fy, w: 2.7, h: 0.35,
    fontSize: 11, fontFace: "Calibri", color: C.mid,
    valign: "middle", margin: 0,
  });
});

// Right: commands
s5.addShape(pres.shapes.RECTANGLE, {
  x: 6.3, y: 1.2, w: 3.2, h: 3.8,
  fill: { color: C.white },
  shadow: mkShadow(),
});
s5.addShape(pres.shapes.RECTANGLE, {
  x: 6.3, y: 1.2, w: 3.2, h: 0.45,
  fill: { color: C.navy },
});
s5.addText("常用 Git 操作", {
  x: 6.5, y: 1.2, w: 2.8, h: 0.45,
  fontSize: 13, fontFace: "Trebuchet MS", color: C.white,
  bold: true, valign: "middle", margin: 0,
});

const gitCmds = [
  "Commit (Ctrl+K)",
  "Push (Ctrl+Shift+K)",
  "Update Project (Ctrl+T)",
  "Show History",
  "Branches (Ctrl+`)",
  "Merge / Rebase",
  "Stash Changes",
];

gitCmds.forEach((cmd, i) => {
  s5.addText(cmd, {
    x: 6.5, y: 1.8 + i * 0.4, w: 2.8, h: 0.35,
    fontSize: 11, fontFace: "Consolas", color: C.dark,
    valign: "middle", margin: 0,
  });
});

// ============================================================
// SLIDE 6: 分支策略
// ============================================================
const s6 = pres.addSlide();
s6.background = { color: C.bg };

s6.addShape(pres.shapes.RECTANGLE, {
  x: 0, y: 0, w: 10, h: 0.06,
  fill: { color: C.blue },
});
s6.addText("04", {
  x: 0.5, y: 0.3, w: 0.6, h: 0.55,
  fontSize: 22, fontFace: "Trebuchet MS", color: C.blue,
  bold: true, align: "center", valign: "middle", margin: 0,
});
s6.addText("分支策略 — Git Flow", {
  x: 1.15, y: 0.3, w: 8.0, h: 0.55,
  fontSize: 26, fontFace: "Trebuchet MS", color: C.navy,
  bold: true, valign: "middle", margin: 0,
});
s6.addShape(pres.shapes.RECTANGLE, {
  x: 0.5, y: 0.95, w: 9.0, h: 0.02,
  fill: { color: C.light },
});

// Branch diagram
const bx = 0.8, by = 1.3;

// main branch
s6.addShape(pres.shapes.RECTANGLE, {
  x: bx, y: by + 1.4, w: 8.4, h: 0.05,
  fill: { color: C.navy },
});
s6.addText("main", {
  x: bx - 0.05, y: by + 1.05, w: 1.0, h: 0.35,
  fontSize: 13, fontFace: "Consolas", color: C.navy, bold: true, margin: 0,
});

// develop branch
s6.addShape(pres.shapes.RECTANGLE, {
  x: bx, y: by + 2.6, w: 8.4, h: 0.05,
  fill: { color: C.blue },
});
s6.addText("develop", {
  x: bx - 0.05, y: by + 2.25, w: 1.2, h: 0.35,
  fontSize: 13, fontFace: "Consolas", color: C.blue, bold: true, margin: 0,
});

// feature branches
const featureBranches = [
  { label: "feature/login", x: 1.5, color: C.green },
  { label: "feature/search", x: 3.8, color: C.orange },
  { label: "feature/payment", x: 6.1, color: C.purple },
];

featureBranches.forEach((f) => {
  s6.addShape(pres.shapes.RECTANGLE, {
    x: f.x, y: by + 2.6, w: 0.03, h: 0.4,
    fill: { color: f.color },
  });
  s6.addShape(pres.shapes.RECTANGLE, {
    x: f.x, y: by + 3.0, w: 1.6, h: 0.03,
    fill: { color: f.color },
  });
  s6.addShape(pres.shapes.RECTANGLE, {
    x: f.x + 1.6, y: by + 2.6, w: 0.03, h: 0.4,
    fill: { color: f.color },
  });
  s6.addText(f.label, {
    x: f.x + 0.1, y: by + 3.1, w: 1.6, h: 0.3,
    fontSize: 10, fontFace: "Consolas", color: f.color, bold: true, margin: 0,
  });
});

// hotfix branch
s6.addShape(pres.shapes.RECTANGLE, {
  x: 7.2, y: by + 0.8, w: 0.03, h: 0.6,
  fill: { color: C.red },
});
s6.addShape(pres.shapes.RECTANGLE, {
  x: 7.2, y: by + 0.8, w: 1.2, h: 0.03,
  fill: { color: C.red },
});
s6.addShape(pres.shapes.RECTANGLE, {
  x: 8.4, y: by + 0.8, w: 0.03, h: 0.6,
  fill: { color: C.red },
});
s6.addText("hotfix/v1.0.1", {
  x: 7.3, y: by + 0.5, w: 1.5, h: 0.3,
  fontSize: 10, fontFace: "Consolas", color: C.red, bold: true, margin: 0,
});

// release branch
s6.addShape(pres.shapes.RECTANGLE, {
  x: 5.2, y: by + 0.9, w: 0.03, h: 0.5,
  fill: { color: C.gold },
});
s6.addShape(pres.shapes.RECTANGLE, {
  x: 5.2, y: by + 0.9, w: 1.0, h: 0.03,
  fill: { color: C.gold },
});
s6.addShape(pres.shapes.RECTANGLE, {
  x: 6.2, y: by + 0.9, w: 0.03, h: 0.5,
  fill: { color: C.gold },
});
s6.addText("release/v1.0", {
  x: 5.3, y: by + 0.6, w: 1.3, h: 0.3,
  fontSize: 10, fontFace: "Consolas", color: C.gold, bold: true, margin: 0,
});

// Commit dots
[2.0, 4.2, 6.4, 8.4].forEach((dx) => {
  s6.addShape(pres.shapes.OVAL, {
    x: bx + dx - 0.08, y: by + 1.34, w: 0.18, h: 0.18,
    fill: { color: C.navy },
  });
});
[1.5, 3.0, 4.5, 6.0, 7.5, 8.8].forEach((dx) => {
  s6.addShape(pres.shapes.OVAL, {
    x: bx + dx - 0.08, y: by + 2.54, w: 0.18, h: 0.18,
    fill: { color: C.blue },
  });
});

// Legend
const legendItems = [
  { color: C.navy, label: "main — 生产环境" },
  { color: C.blue, label: "develop — 开发主干" },
  { color: C.green, label: "feature/* — 功能开发" },
  { color: C.gold, label: "release/* — 发布准备" },
  { color: C.red, label: "hotfix/* — 紧急修复" },
];

legendItems.forEach((item, i) => {
  const ly = 3.7 + i * 0.3;
  s6.addShape(pres.shapes.RECTANGLE, {
    x: 0.8, y: ly + 0.1, w: 0.25, h: 0.04,
    fill: { color: item.color },
  });
  s6.addText(item.label, {
    x: 1.15, y: ly - 0.02, w: 2.5, h: 0.3,
    fontSize: 10.5, fontFace: "Calibri", color: C.dark, margin: 0,
  });
});

// Branch naming
s6.addShape(pres.shapes.RECTANGLE, {
  x: 4.0, y: 3.65, w: 5.5, h: 1.2,
  fill: { color: C.white },
  shadow: mkShadow(),
});
s6.addText("分支命名规范", {
  x: 4.2, y: 3.75, w: 5.1, h: 0.35,
  fontSize: 13, fontFace: "Trebuchet MS", color: C.navy, bold: true, margin: 0,
});
s6.addText("feature/TASK-123-login  |  bugfix/TASK-456-fix", {
  x: 4.2, y: 4.15, w: 5.1, h: 0.55,
  fontSize: 11, fontFace: "Consolas", color: C.dark,
  valign: "middle", margin: 0,
});

// ============================================================
// SLIDE 7: 开发流程
// ============================================================
const s7 = pres.addSlide();
s7.background = { color: C.bg };

s7.addShape(pres.shapes.RECTANGLE, {
  x: 0, y: 0, w: 10, h: 0.06,
  fill: { color: C.blue },
});
s7.addText("05", {
  x: 0.5, y: 0.3, w: 0.6, h: 0.55,
  fontSize: 22, fontFace: "Trebuchet MS", color: C.blue,
  bold: true, align: "center", valign: "middle", margin: 0,
});
s7.addText("开发流程", {
  x: 1.15, y: 0.3, w: 8.0, h: 0.55,
  fontSize: 26, fontFace: "Trebuchet MS", color: C.navy,
  bold: true, valign: "middle", margin: 0,
});
s7.addShape(pres.shapes.RECTANGLE, {
  x: 0.5, y: 0.95, w: 9.0, h: 0.02,
  fill: { color: C.light },
});

// Flow diagram
const flowSteps = [
  { label: "需求分析", sub: "Issue/Ticket", color: C.navy },
  { label: "创建分支", sub: "feature/*", color: C.blue },
  { label: "编码开发", sub: "PyCharm IDE", color: C.teal },
  { label: "本地测试", sub: "pytest", color: C.green },
  { label: "提交代码", sub: "Commit+Push", color: C.gold },
  { label: "代码审查", sub: "Pull Request", color: C.orange },
  { label: "合并部署", sub: "Merge+CI/CD", color: C.purple },
];

const fBoxW = 1.15, fBoxH = 1.2, fGap = 0.18;
const fTotalW = flowSteps.length * fBoxW + (flowSteps.length - 1) * fGap;
const fStartX = (10 - fTotalW) / 2;
const fY = 1.3;

flowSteps.forEach((step, i) => {
  const fx = fStartX + i * (fBoxW + fGap);

  s7.addShape(pres.shapes.RECTANGLE, {
    x: fx, y: fY, w: fBoxW, h: fBoxH,
    fill: { color: step.color },
    shadow: mkShadow(),
  });
  s7.addText(String(i + 1), {
    x: fx, y: fY + 0.08, w: fBoxW, h: 0.3,
    fontSize: 14, fontFace: "Trebuchet MS", color: C.white,
    bold: true, align: "center", valign: "middle", margin: 0,
  });
  s7.addText(step.label, {
    x: fx, y: fY + 0.38, w: fBoxW, h: 0.35,
    fontSize: 12, fontFace: "Trebuchet MS", color: C.white,
    bold: true, align: "center", valign: "middle", margin: 0,
  });
  s7.addText(step.sub, {
    x: fx, y: fY + 0.72, w: fBoxW, h: 0.35,
    fontSize: 9.5, fontFace: "Calibri", color: C.white,
    align: "center", valign: "top", margin: 0,
  });

  if (i < flowSteps.length - 1) {
    s7.addText("→", {
      x: fx + fBoxW, y: fY, w: fGap, h: fBoxH,
      fontSize: 16, fontFace: "Arial", color: C.mid,
      align: "center", valign: "middle", margin: 0,
    });
  }
});

// Commit convention
s7.addShape(pres.shapes.RECTANGLE, {
  x: 0.5, y: 2.8, w: 9.0, h: 2.2,
  fill: { color: C.white },
  shadow: mkShadow(),
});
s7.addText("Commit Message 规范 (Conventional Commits)", {
  x: 0.7, y: 2.9, w: 8.6, h: 0.4,
  fontSize: 14, fontFace: "Trebuchet MS", color: C.navy, bold: true, margin: 0,
});

const commitTypes = [
  { type: "feat:", desc: "新功能", color: C.green },
  { type: "fix:", desc: "修复 Bug", color: C.red },
  { type: "docs:", desc: "文档更新", color: C.blue },
  { type: "refactor:", desc: "代码重构", color: C.purple },
  { type: "test:", desc: "测试相关", color: C.teal },
  { type: "chore:", desc: "构建/工具", color: C.mid },
];

commitTypes.forEach((ct, i) => {
  const col = i % 3;
  const row = Math.floor(i / 3);
  const cx = 0.7 + col * 2.95;
  const cy = 3.45 + row * 0.7;

  s7.addText(ct.type + "  " + ct.desc, {
    x: cx, y: cy, w: 2.8, h: 0.3,
    fontSize: 11, fontFace: "Consolas", color: ct.color,
    bold: true, valign: "middle", margin: 0,
  });
});

// ============================================================
// SLIDE 8: 代码审查
// ============================================================
const s8 = pres.addSlide();
s8.background = { color: C.bg };

s8.addShape(pres.shapes.RECTANGLE, {
  x: 0, y: 0, w: 10, h: 0.06,
  fill: { color: C.blue },
});
s8.addText("06", {
  x: 0.5, y: 0.3, w: 0.6, h: 0.55,
  fontSize: 22, fontFace: "Trebuchet MS", color: C.blue,
  bold: true, align: "center", valign: "middle", margin: 0,
});
s8.addText("代码审查 (Code Review)", {
  x: 1.15, y: 0.3, w: 8.0, h: 0.55,
  fontSize: 26, fontFace: "Trebuchet MS", color: C.navy,
  bold: true, valign: "middle", margin: 0,
});
s8.addShape(pres.shapes.RECTANGLE, {
  x: 0.5, y: 0.95, w: 9.0, h: 0.02,
  fill: { color: C.light },
});

// Left panel
s8.addShape(pres.shapes.RECTANGLE, {
  x: 0.5, y: 1.2, w: 4.3, h: 3.8,
  fill: { color: C.white },
  shadow: mkShadow(),
});
s8.addShape(pres.shapes.RECTANGLE, {
  x: 0.5, y: 1.2, w: 4.3, h: 0.5,
  fill: { color: C.blue },
});
s8.addText("PyCharm 审查工具", {
  x: 0.7, y: 1.2, w: 3.9, h: 0.5,
  fontSize: 15, fontFace: "Trebuchet MS", color: C.white,
  bold: true, valign: "middle", margin: 0,
});

const reviewTools = [
  "Diff 对比 — 逐行对比分支差异",
  "Annotations — 查看代码修改历史",
  "TODO 视图 — 追踪待办事项",
  "Code Inspection — 静态代码分析",
  "Quality Profiles — 自定义代码质量规则",
];

reviewTools.forEach((t, i) => {
  s8.addText("•  " + t, {
    x: 0.8, y: 1.85 + i * 0.55, w: 3.8, h: 0.45,
    fontSize: 12, fontFace: "Calibri", color: C.dark,
    valign: "middle", margin: 0,
  });
});

// Right panel
s8.addShape(pres.shapes.RECTANGLE, {
  x: 5.2, y: 1.2, w: 4.3, h: 3.8,
  fill: { color: C.white },
  shadow: mkShadow(),
});
s8.addShape(pres.shapes.RECTANGLE, {
  x: 5.2, y: 1.2, w: 4.3, h: 0.5,
  fill: { color: C.teal },
});
s8.addText("Review 检查清单", {
  x: 5.4, y: 1.2, w: 3.9, h: 0.5,
  fontSize: 15, fontFace: "Trebuchet MS", color: C.white,
  bold: true, valign: "middle", margin: 0,
});

const reviewChecklist = [
  "功能实现是否符合需求",
  "代码逻辑是否清晰可读",
  "是否有潜在的 Bug 或安全问题",
  "是否遵循团队编码规范",
  "是否有充分的测试覆盖",
  "性能是否有可优化空间",
  "文档/注释是否充分",
];

reviewChecklist.forEach((item, i) => {
  s8.addText("☐  " + item, {
    x: 5.5, y: 1.85 + i * 0.42, w: 3.8, h: 0.35,
    fontSize: 12, fontFace: "Calibri", color: C.dark,
    valign: "middle", margin: 0,
  });
});

// ============================================================
// SLIDE 9: 调试与测试
// ============================================================
const s9 = pres.addSlide();
s9.background = { color: C.bg };

s9.addShape(pres.shapes.RECTANGLE, {
  x: 0, y: 0, w: 10, h: 0.06,
  fill: { color: C.blue },
});
s9.addText("07", {
  x: 0.5, y: 0.3, w: 0.6, h: 0.55,
  fontSize: 22, fontFace: "Trebuchet MS", color: C.blue,
  bold: true, align: "center", valign: "middle", margin: 0,
});
s9.addText("调试与测试", {
  x: 1.15, y: 0.3, w: 8.0, h: 0.55,
  fontSize: 26, fontFace: "Trebuchet MS", color: C.navy,
  bold: true, valign: "middle", margin: 0,
});
s9.addShape(pres.shapes.RECTANGLE, {
  x: 0.5, y: 0.95, w: 9.0, h: 0.02,
  fill: { color: C.light },
});

// Debug panel
s9.addShape(pres.shapes.RECTANGLE, {
  x: 0.5, y: 1.2, w: 4.3, h: 2.0,
  fill: { color: C.white },
  shadow: mkShadow(),
});
s9.addShape(pres.shapes.RECTANGLE, {
  x: 0.5, y: 1.2, w: 4.3, h: 0.45,
  fill: { color: C.blue },
});
s9.addText("Debug 调试", {
  x: 0.7, y: 1.2, w: 3.9, h: 0.45,
  fontSize: 14, fontFace: "Trebuchet MS", color: C.white,
  bold: true, valign: "middle", margin: 0,
});

const debugItems = [
  "断点调试 — 行号处点击设断点",
  "条件断点 — 右键设置触发条件",
  "Evaluate — 运行时修改变量值",
  "Remote Debug — 调试远程服务器",
];

debugItems.forEach((item, i) => {
  s9.addText("•  " + item, {
    x: 0.8, y: 1.78 + i * 0.33, w: 3.8, h: 0.3,
    fontSize: 11, fontFace: "Calibri", color: C.dark,
    valign: "middle", margin: 0,
  });
});

// Test panel
s9.addShape(pres.shapes.RECTANGLE, {
  x: 5.2, y: 1.2, w: 4.3, h: 2.0,
  fill: { color: C.white },
  shadow: mkShadow(),
});
s9.addShape(pres.shapes.RECTANGLE, {
  x: 5.2, y: 1.2, w: 4.3, h: 0.45,
  fill: { color: C.green },
});
s9.addText("Test 测试", {
  x: 5.4, y: 1.2, w: 3.9, h: 0.45,
  fontSize: 14, fontFace: "Trebuchet MS", color: C.white,
  bold: true, valign: "middle", margin: 0,
});

const testItems = [
  "pytest — 单元测试框架",
  "Coverage — 代码覆盖率检查",
  "Mock — 模拟外部依赖",
  "CI 集成 — 提交自动运行测试",
];

testItems.forEach((item, i) => {
  s9.addText("•  " + item, {
    x: 5.5, y: 1.78 + i * 0.33, w: 3.8, h: 0.3,
    fontSize: 11, fontFace: "Calibri", color: C.dark,
    valign: "middle", margin: 0,
  });
});

// CI/CD Pipeline
s9.addShape(pres.shapes.RECTANGLE, {
  x: 0.5, y: 3.4, w: 9.0, h: 1.6,
  fill: { color: C.white },
  shadow: mkShadow(),
});
s9.addShape(pres.shapes.RECTANGLE, {
  x: 0.5, y: 3.4, w: 9.0, h: 0.45,
  fill: { color: C.navy },
});
s9.addText("CI/CD 流水线", {
  x: 0.7, y: 3.4, w: 8.6, h: 0.45,
  fontSize: 14, fontFace: "Trebuchet MS", color: C.white,
  bold: true, valign: "middle", margin: 0,
});

const pipeSteps = [
  { label: "Push", color: C.blue },
  { label: "Lint", color: C.teal },
  { label: "Test", color: C.green },
  { label: "Build", color: C.gold },
  { label: "Deploy", color: C.purple },
];

const pBoxW = 1.3, pBoxH = 0.55, pGap = 0.35;
const pTotalW = pipeSteps.length * pBoxW + (pipeSteps.length - 1) * pGap;
const pStartX = (10 - pTotalW) / 2;

pipeSteps.forEach((ps, i) => {
  const px = pStartX + i * (pBoxW + pGap);
  const py = 4.05;

  s9.addShape(pres.shapes.RECTANGLE, {
    x: px, y: py, w: pBoxW, h: pBoxH,
    fill: { color: ps.color },
  });
  s9.addText(ps.label, {
    x: px, y: py, w: pBoxW, h: pBoxH,
    fontSize: 13, fontFace: "Trebuchet MS", color: C.white,
    bold: true, align: "center", valign: "middle", margin: 0,
  });

  if (i < pipeSteps.length - 1) {
    s9.addText("→", {
      x: px + pBoxW, y: py, w: pGap, h: pBoxH,
      fontSize: 18, fontFace: "Arial", color: C.mid,
      align: "center", valign: "middle", margin: 0,
    });
  }
});

// ============================================================
// SLIDE 10: 远程协作
// ============================================================
const s10 = pres.addSlide();
s10.background = { color: C.bg };

s10.addShape(pres.shapes.RECTANGLE, {
  x: 0, y: 0, w: 10, h: 0.06,
  fill: { color: C.blue },
});
s10.addText("08", {
  x: 0.5, y: 0.3, w: 0.6, h: 0.55,
  fontSize: 22, fontFace: "Trebuchet MS", color: C.blue,
  bold: true, align: "center", valign: "middle", margin: 0,
});
s10.addText("远程协作", {
  x: 1.15, y: 0.3, w: 8.0, h: 0.55,
  fontSize: 26, fontFace: "Trebuchet MS", color: C.navy,
  bold: true, valign: "middle", margin: 0,
});
s10.addShape(pres.shapes.RECTANGLE, {
  x: 0.5, y: 0.95, w: 9.0, h: 0.02,
  fill: { color: C.light },
});

// Code With Me
s10.addShape(pres.shapes.RECTANGLE, {
  x: 0.5, y: 1.2, w: 4.3, h: 3.8,
  fill: { color: C.white },
  shadow: mkShadow(),
});
s10.addShape(pres.shapes.RECTANGLE, {
  x: 0.5, y: 1.2, w: 4.3, h: 0.5,
  fill: { color: C.blue },
});
s10.addText("Code With Me", {
  x: 0.7, y: 1.2, w: 3.9, h: 0.5,
  fontSize: 15, fontFace: "Trebuchet MS", color: C.white,
  bold: true, valign: "middle", margin: 0,
});

const cwmFeatures = [
  "实时多人协同编码",
  "共享编辑器与终端",
  "语音通话集成",
  "权限控制 (只读/完全控制)",
  "会话录制与回放",
  "支持 JetBrains 全系列 IDE",
];

cwmFeatures.forEach((f, i) => {
  s10.addText("▸  " + f, {
    x: 0.8, y: 1.85 + i * 0.45, w: 3.8, h: 0.4,
    fontSize: 12, fontFace: "Calibri", color: C.dark,
    valign: "middle", margin: 0,
  });
});

// Remote Development
s10.addShape(pres.shapes.RECTANGLE, {
  x: 5.2, y: 1.2, w: 4.3, h: 3.8,
  fill: { color: C.white },
  shadow: mkShadow(),
});
s10.addShape(pres.shapes.RECTANGLE, {
  x: 5.2, y: 1.2, w: 4.3, h: 0.5,
  fill: { color: C.teal },
});
s10.addText("远程开发", {
  x: 5.4, y: 1.2, w: 3.9, h: 0.5,
  fontSize: 15, fontFace: "Trebuchet MS", color: C.white,
  bold: true, valign: "middle", margin: 0,
});

const remoteFeatures = [
  "SSH Remote — 远程服务器开发",
  "Docker — 容器化开发环境",
  "WSL — Windows 子系统支持",
  "Gateway — 远程 IDE 托管",
  "Remote Interpreter — 远程解释器",
  "端口转发 — 调试远程服务",
];

remoteFeatures.forEach((f, i) => {
  s10.addText("▸  " + f, {
    x: 5.5, y: 1.85 + i * 0.45, w: 3.8, h: 0.4,
    fontSize: 12, fontFace: "Calibri", color: C.dark,
    valign: "middle", margin: 0,
  });
});

// ============================================================
// SLIDE 11: 最佳实践
// ============================================================
const s11 = pres.addSlide();
s11.background = { color: C.bg };

s11.addShape(pres.shapes.RECTANGLE, {
  x: 0, y: 0, w: 10, h: 0.06,
  fill: { color: C.blue },
});
s11.addText("09", {
  x: 0.5, y: 0.3, w: 0.6, h: 0.55,
  fontSize: 22, fontFace: "Trebuchet MS", color: C.blue,
  bold: true, align: "center", valign: "middle", margin: 0,
});
s11.addText("最佳实践", {
  x: 1.15, y: 0.3, w: 8.0, h: 0.55,
  fontSize: 26, fontFace: "Trebuchet MS", color: C.navy,
  bold: true, valign: "middle", margin: 0,
});
s11.addShape(pres.shapes.RECTANGLE, {
  x: 0.5, y: 0.95, w: 9.0, h: 0.02,
  fill: { color: C.light },
});

const practices = [
  {
    title: "统一代码风格",
    items: ["使用 .editorconfig 统一缩进", "PyCharm Code Style 共享配置", "提交前自动格式化 (Black/isort)"],
    color: C.blue,
  },
  {
    title: "分支管理规范",
    items: ["一个功能一个分支", "分支命名包含任务编号", "及时删除已合并分支"],
    color: C.teal,
  },
  {
    title: "提交信息规范",
    items: ["遵循 Conventional Commits", "一个提交只做一件事", "中文描述清晰明了"],
    color: C.green,
  },
  {
    title: "Code Review 文化",
    items: ["至少一人 Approve", "建设性反馈，对事不对人", "48 小时内完成审查"],
    color: C.gold,
  },
  {
    title: "测试驱动开发",
    items: ["核心逻辑必须有测试", "CI 自动运行测试套件", "覆盖率不低于 80%"],
    color: C.orange,
  },
  {
    title: "文档即代码",
    items: ["README 说明项目概览", "API 文档自动生成", "变更日志跟随版本"],
    color: C.purple,
  },
];

const pCardW = 2.85, pCardH = 2.0, pCardGap = 0.2;
const pCols = 3;
const pCardTotalW = pCols * pCardW + (pCols - 1) * pCardGap;
const pCardStartX = (10 - pCardTotalW) / 2;

practices.forEach((p, i) => {
  const col = i % pCols;
  const row = Math.floor(i / pCols);
  const px = pCardStartX + col * (pCardW + pCardGap);
  const py = 1.2 + row * (pCardH + 0.2);

  s11.addShape(pres.shapes.RECTANGLE, {
    x: px, y: py, w: pCardW, h: pCardH,
    fill: { color: C.white },
    shadow: mkShadow(),
  });
  // Accent bar
  s11.addShape(pres.shapes.RECTANGLE, {
    x: px, y: py, w: pCardW, h: 0.05,
    fill: { color: p.color },
  });

  s11.addText(p.title, {
    x: px + 0.2, y: py + 0.2, w: pCardW - 0.4, h: 0.35,
    fontSize: 14, fontFace: "Trebuchet MS", color: C.navy,
    bold: true, margin: 0,
  });

  p.items.forEach((item, j) => {
    s11.addText("•  " + item, {
      x: px + 0.25, y: py + 0.65 + j * 0.4, w: pCardW - 0.5, h: 0.35,
      fontSize: 10.5, fontFace: "Calibri", color: C.dark,
      valign: "middle", margin: 0,
    });
  });
});

// ============================================================
// SLIDE 12: 总结
// ============================================================
const s12 = pres.addSlide();
s12.background = { color: C.bg };

s12.addShape(pres.shapes.RECTANGLE, {
  x: 0, y: 0, w: 10, h: 0.06,
  fill: { color: C.blue },
});
s12.addText("10", {
  x: 0.5, y: 0.3, w: 0.6, h: 0.55,
  fontSize: 22, fontFace: "Trebuchet MS", color: C.blue,
  bold: true, align: "center", valign: "middle", margin: 0,
});
s12.addText("总结", {
  x: 1.15, y: 0.3, w: 8.0, h: 0.55,
  fontSize: 26, fontFace: "Trebuchet MS", color: C.navy,
  bold: true, valign: "middle", margin: 0,
});
s12.addShape(pres.shapes.RECTANGLE, {
  x: 0.5, y: 0.95, w: 9.0, h: 0.02,
  fill: { color: C.light },
});

// Key takeaways
s12.addShape(pres.shapes.RECTANGLE, {
  x: 0.5, y: 1.2, w: 9.0, h: 2.0,
  fill: { color: C.white },
  shadow: mkShadow(),
});

const takeaways = [
  { num: "1", text: "PyCharm 提供一站式团队协作工具链，从编码到部署全流程覆盖", color: C.blue },
  { num: "2", text: "Git 分支策略 + Code Review 是团队协作的基石", color: C.teal },
  { num: "3", text: "CI/CD 自动化流水线保障代码质量与交付效率", color: C.green },
  { num: "4", text: "Code With Me 实现远程实时协作，打破地理限制", color: C.gold },
];

takeaways.forEach((t, i) => {
  const ty = 1.4 + i * 0.45;
  s12.addShape(pres.shapes.OVAL, {
    x: 0.8, y: ty + 0.05, w: 0.3, h: 0.3,
    fill: { color: t.color },
  });
  s12.addText(t.num, {
    x: 0.8, y: ty + 0.05, w: 0.3, h: 0.3,
    fontSize: 12, fontFace: "Trebuchet MS", color: C.white,
    bold: true, align: "center", valign: "middle", margin: 0,
  });
  s12.addText(t.text, {
    x: 1.25, y: ty, w: 8.0, h: 0.4,
    fontSize: 13, fontFace: "Calibri", color: C.dark,
    valign: "middle", margin: 0,
  });
});

// Action items
s12.addShape(pres.shapes.RECTANGLE, {
  x: 0.5, y: 3.5, w: 9.0, h: 1.5,
  fill: { color: C.white },
  shadow: mkShadow(),
});
s12.addText("下一步行动", {
  x: 0.7, y: 3.6, w: 8.6, h: 0.4,
  fontSize: 15, fontFace: "Trebuchet MS", color: C.navy,
  bold: true, margin: 0,
});

const actions = [
  { text: "配置统一的 .editorconfig 和 Code Style", color: C.blue },
  { text: "制定团队分支策略与 Commit 规范", color: C.teal },
  { text: "搭建 CI/CD 流水线", color: C.green },
  { text: "组织 Code Review 培训", color: C.gold },
];

actions.forEach((a, i) => {
  const col = i % 2;
  const row = Math.floor(i / 2);
  const ax = 0.7 + col * 4.5;
  const ay = 4.1 + row * 0.4;

  s12.addShape(pres.shapes.RECTANGLE, {
    x: ax, y: ay + 0.08, w: 0.15, h: 0.15,
    fill: { color: a.color },
  });
  s12.addText(a.text, {
    x: ax + 0.3, y: ay, w: 4.0, h: 0.35,
    fontSize: 12, fontFace: "Calibri", color: C.dark,
    valign: "middle", margin: 0,
  });
});

// ============================================================
// SLIDE 13: Q&A
// ============================================================
const s13 = pres.addSlide();
s13.background = { color: C.navy };

// Decorative
s13.addShape(pres.shapes.RECTANGLE, {
  x: 7.2, y: 0, w: 2.8, h: 2.0,
  fill: { color: C.blue, transparency: 70 },
});
s13.addShape(pres.shapes.RECTANGLE, {
  x: 0, y: 3.8, w: 2.5, h: 1.825,
  fill: { color: C.teal, transparency: 75 },
});

// Accent line
s13.addShape(pres.shapes.RECTANGLE, {
  x: 4.0, y: 1.5, w: 2.0, h: 0.06,
  fill: { color: C.teal },
});

s13.addText("Thank You", {
  x: 0.5, y: 1.7, w: 9.0, h: 1.2,
  fontSize: 52, fontFace: "Trebuchet MS", color: C.white,
  bold: true, align: "center", valign: "middle", margin: 0,
});

s13.addText("Q & A", {
  x: 0.5, y: 2.8, w: 9.0, h: 0.8,
  fontSize: 32, fontFace: "Trebuchet MS", color: C.teal,
  bold: true, align: "center", valign: "middle", margin: 0,
});

s13.addText("感谢聆听  |  期待交流", {
  x: 0.5, y: 3.7, w: 9.0, h: 0.5,
  fontSize: 16, fontFace: "Calibri", color: C.mid,
  align: "center", valign: "middle", margin: 0,
});

// Bottom bar
s13.addShape(pres.shapes.RECTANGLE, {
  x: 0, y: 4.9, w: 10, h: 0.725,
  fill: { color: "8B2E1E" },
});
s13.addText("PyCharm 团队协作开发项目流程  |  Presentation by Hinata", {
  x: 0.5, y: 4.95, w: 9.0, h: 0.6,
  fontSize: 12, fontFace: "Calibri", color: C.light,
  align: "center", valign: "middle", margin: 0,
});

// ============================================================
// SAVE
// ============================================================
pres.writeFile({ fileName: "D:/pycharm/Person-Practice/PPT/PyCharm团队协作开发流程.pptx" })
  .then(() => console.log("Done! Saved to PPT/PyCharm团队协作开发流程.pptx"))
  .catch(err => console.error(err));
