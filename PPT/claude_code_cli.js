const pptxgen = require("pptxgenjs");

let pres = new pptxgen();
pres.layout = "LAYOUT_16x9";
pres.author = "Hinata";
pres.title = "Claude Code CLI 使用指南";

// ========== Color Palette (Van Dyke Brown + Light Khaki) ==========
const C = {
  darkBg: "4B2C23",      // 凡戴克棕（深）
  medBg: "3D231B",       // 更深棕（卡片背景，增加边界感）
  primary: "4B2C23",     // 凡戴克棕
  accent: "D6C3B2",      // 浅卡其色
  highlight: "C9A882",   // 暖金色（辅助强调）
  white: "FFFFFF",
  light: "FFFFFF",       // 纯白（正文提亮）
  muted: "D6C3B2",       // 浅卡其（柔和文字）
  codeBg: "2E1A12",      // 更深棕代码块
  green: "6AAF6C",       // 提亮暖绿
  red: "E06050",         // 提亮暖红
};

const mkShadow = () => ({ type: "outer", color: "000000", blur: 8, offset: 3, angle: 135, opacity: 0.2 });

// ========== Helper: slide footer ==========
function addFooter(slide, pageNum, total) {
  slide.addShape(pres.shapes.RECTANGLE, { x: 0, y: 5.2, w: 10, h: 0.425, fill: { color: C.darkBg } });
  slide.addText("Claude Code CLI 使用指南", { x: 0.5, y: 5.22, w: 5, h: 0.4, fontSize: 9, color: C.muted, fontFace: "Arial" });
  slide.addText(`${pageNum} / ${total}`, { x: 8, y: 5.22, w: 1.5, h: 0.4, fontSize: 9, color: C.muted, fontFace: "Arial", align: "right" });
}

function addSectionBar(slide, title) {
  slide.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 0.9, fill: { color: C.primary } });
  slide.addText(title, { x: 0.6, y: 0.15, w: 9, h: 0.6, fontSize: 24, color: C.white, fontFace: "Arial", bold: true, margin: 0 });
}

function addCodeBlock(slide, code, x, y, w, h) {
  slide.addShape(pres.shapes.RECTANGLE, { x, y, w, h, fill: { color: C.codeBg }, shadow: mkShadow() });
  slide.addText(code, { x: x + 0.15, y: y + 0.1, w: w - 0.3, h: h - 0.2, fontSize: 11, color: "E6EDF3", fontFace: "Consolas", valign: "top" });
}

function addCard(slide, title, desc, x, y, w, h, accentColor) {
  slide.addShape(pres.shapes.RECTANGLE, { x, y, w, h, fill: { color: C.medBg }, shadow: mkShadow() });
  slide.addShape(pres.shapes.RECTANGLE, { x, y, w: 0.06, h, fill: { color: accentColor || C.accent } });
  slide.addText(title, { x: x + 0.2, y: y + 0.08, w: w - 0.35, h: 0.35, fontSize: 13, color: accentColor || C.accent, fontFace: "Arial", bold: true, margin: 0 });
  slide.addText(desc, { x: x + 0.2, y: y + 0.4, w: w - 0.35, h: h - 0.5, fontSize: 10.5, color: C.light, fontFace: "Arial", valign: "top", margin: 0 });
}

const TOTAL = 12;

// ========================================================
// SLIDE 1: Title (FIXED: balanced layout with right decoration)
// ========================================================
let s1 = pres.addSlide();
s1.background = { color: C.darkBg };
s1.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 5.625, fill: { color: C.primary, transparency: 30 } });
// Right decorative block
s1.addShape(pres.shapes.RECTANGLE, { x: 6.5, y: 1.2, w: 3.2, h: 3.2, fill: { color: C.accent, transparency: 70 } });
s1.addShape(pres.shapes.RECTANGLE, { x: 7.0, y: 1.7, w: 2.5, h: 2.5, fill: { color: C.highlight, transparency: 60 } });
// Left accent bar
s1.addShape(pres.shapes.RECTANGLE, { x: 0.8, y: 1.8, w: 0.08, h: 1.8, fill: { color: C.highlight } });
// Title
s1.addText("Claude Code CLI", { x: 1.1, y: 1.8, w: 5, h: 1.0, fontSize: 42, color: C.white, fontFace: "Arial", bold: true, margin: 0 });
s1.addText("使用指南", { x: 1.1, y: 2.7, w: 5, h: 0.7, fontSize: 30, color: C.accent, fontFace: "Arial", margin: 0 });
s1.addText("从安装到精通的完整教程", { x: 1.1, y: 3.4, w: 5, h: 0.5, fontSize: 15, color: C.muted, fontFace: "Arial", margin: 0 });
// Bottom bar
s1.addShape(pres.shapes.RECTANGLE, { x: 0, y: 4.8, w: 10, h: 0.825, fill: { color: C.darkBg } });
s1.addText("Anthropic 出品  |  终端中的 AI 编程助手", { x: 0.8, y: 4.9, w: 8, h: 0.4, fontSize: 12, color: C.light, fontFace: "Arial" });

// ========================================================
// SLIDE 2: What is Claude Code CLI (FIXED: cards moved up)
// ========================================================
let s2 = pres.addSlide();
s2.background = { color: C.darkBg };
addSectionBar(s2, "什么是 Claude Code CLI");
addFooter(s2, 2, TOTAL);

s2.addText("Claude Code 是 Anthropic 推出的命令行 AI 编程助手，直接在终端中运行，能够理解整个代码库并执行实际操作。", {
  x: 0.6, y: 1.1, w: 8.8, h: 0.5, fontSize: 13, color: C.light, fontFace: "Arial", margin: 0
});

// 4 cards - moved up, closer together
addCard(s2, "智能代码编辑", "读取、编写、修改文件\n理解项目上下文与架构", 0.6, 1.8, 4.1, 1.3, C.accent);
addCard(s2, "Shell 命令执行", "运行构建、测试、Git 命令\n自动诊断并修复错误", 5.3, 1.8, 4.1, 1.3, C.highlight);
addCard(s2, "多轮对话", "交互式 REPL 会话\n保持上下文连续性", 0.6, 3.3, 4.1, 1.3, C.green);
addCard(s2, "MCP 扩展", "支持 Model Context Protocol\n连接外部工具和数据源", 5.3, 3.3, 4.1, 1.3, "A23B72");

// ========================================================
// SLIDE 3: Installation (FIXED: better vertical balance)
// ========================================================
let s3 = pres.addSlide();
s3.background = { color: C.darkBg };
addSectionBar(s3, "安装与环境配置");
addFooter(s3, 3, TOTAL);

// Left column - extend content downward
s3.addText("前置要求", { x: 0.6, y: 1.1, w: 3, h: 0.35, fontSize: 15, color: C.highlight, fontFace: "Arial", bold: true, margin: 0 });
s3.addText([
  { text: "Node.js 18+", options: { bullet: true, breakLine: true } },
  { text: "npm 或 yarn", options: { bullet: true, breakLine: true } },
  { text: "Anthropic API Key 或 Claude Max/Pro 订阅", options: { bullet: true } },
], { x: 0.6, y: 1.45, w: 4, h: 1.0, fontSize: 12, color: C.light, fontFace: "Arial" });

s3.addText("安装命令", { x: 0.6, y: 2.6, w: 3, h: 0.35, fontSize: 15, color: C.highlight, fontFace: "Arial", bold: true, margin: 0 });
addCodeBlock(s3, "# 全局安装\nnpm install -g @anthropic-ai/claude-code\n\n# 或直接运行（无需安装）\nnpx @anthropic-ai/claude-code", 0.6, 3.0, 4.2, 1.5);

// Right column - moved up slightly
s3.addText("认证方式", { x: 5.2, y: 1.1, w: 4, h: 0.35, fontSize: 15, color: C.highlight, fontFace: "Arial", bold: true, margin: 0 });
addCard(s3, "API Key 认证", "设置环境变量:\nANTHROPIC_API_KEY=sk-ant-...", 5.2, 1.5, 4.2, 0.95, C.accent);
addCard(s3, "OAuth 登录", "运行 /login 命令\n使用 Claude Max/Pro 账号登录", 5.2, 2.65, 4.2, 0.95, C.green);
addCard(s3, "健康检查", "运行 /doctor 命令\n诊断安装和配置问题", 5.2, 3.8, 4.2, 0.95, "A23B72");

// ========================================================
// SLIDE 4: Interactive Mode (FIXED: no overlap, wider description area)
// ========================================================
let s4 = pres.addSlide();
s4.background = { color: C.darkBg };
addSectionBar(s4, "基础用法：交互式模式");
addFooter(s4, 4, TOTAL);

// Left side - code example only
s4.addText("启动交互式会话", { x: 0.6, y: 1.1, w: 4, h: 0.35, fontSize: 15, color: C.highlight, fontFace: "Arial", bold: true, margin: 0 });
addCodeBlock(s4, "$ claude\n\n> _", 0.6, 1.5, 4.2, 0.85);

// Right side - example session
s4.addText("示例会话", { x: 5.4, y: 1.1, w: 4, h: 0.35, fontSize: 15, color: C.highlight, fontFace: "Arial", bold: true, margin: 0 });
addCodeBlock(s4, '$ claude\n> 帮我看看这个函数有什么问题\n\nClaude: 我来分析 processOrder()\n函数...\n\n✓ 已修复: 边界条件处理\n✓ 已添加: 错误日志记录\n\n> 帮我写个单元测试', 5.4, 1.5, 4.0, 2.5);

// Bottom section - numbered list (FULL WIDTH, no overlap)
s4.addText("在 REPL 中你可以：", { x: 0.6, y: 3.3, w: 8, h: 0.35, fontSize: 14, color: C.light, fontFace: "Arial", bold: true, margin: 0 });

let replItems = [
  { text: "直接输入问题或指令", desc: "Claude 会理解你的代码库并执行操作" },
  { text: "Shift+Tab 切换自动接受", desc: "自动批准工具调用，无需逐个确认" },
  { text: "Esc 中断当前生成", desc: "随时停止 Claude 的回复" },
  { text: "# 开头添加记忆", desc: "保存上下文信息供后续使用" },
];
replItems.forEach((item, i) => {
  let col = i % 2;
  let row = Math.floor(i / 2);
  let xPos = 0.6 + col * 4.7;
  let yPos = 3.75 + row * 0.55;
  s4.addShape(pres.shapes.RECTANGLE, { x: xPos, y: yPos, w: 0.3, h: 0.3, fill: { color: C.accent } });
  s4.addText(String(i + 1), { x: xPos, y: yPos, w: 0.3, h: 0.3, fontSize: 11, color: C.white, fontFace: "Arial", bold: true, align: "center", valign: "middle", margin: 0 });
  s4.addText(item.text + " — " + item.desc, { x: xPos + 0.4, y: yPos, w: 4.1, h: 0.3, fontSize: 11, color: C.light, fontFace: "Arial", valign: "middle", margin: 0 });
});

// ========================================================
// SLIDE 5: One-shot & Pipe Mode (FIXED: code blocks shorter)
// ========================================================
let s5 = pres.addSlide();
s5.background = { color: C.darkBg };
addSectionBar(s5, "基础用法：单次执行与管道模式");
addFooter(s5, 5, TOTAL);

// One-shot mode
s5.addText("单次执行模式 (-p)", { x: 0.6, y: 1.1, w: 5, h: 0.35, fontSize: 15, color: C.highlight, fontFace: "Arial", bold: true, margin: 0 });
s5.addText("适合脚本和 CI/CD 集成，执行后自动退出", { x: 0.6, y: 1.45, w: 8, h: 0.25, fontSize: 11, color: C.muted, fontFace: "Arial", margin: 0 });
addCodeBlock(s5, '# 非交互式执行\nclaude -p "分析这个项目的代码结构"\n\n# 结合其他命令\nclaude -p "为这个函数写文档" > doc.txt', 0.6, 1.75, 4.2, 1.3);

// Pipe mode - shorter
s5.addText("管道模式", { x: 0.6, y: 3.2, w: 5, h: 0.35, fontSize: 15, color: C.highlight, fontFace: "Arial", bold: true, margin: 0 });
addCodeBlock(s5, '# 将文件内容传递给 Claude\ncat app.py | claude "找出其中的 bug"\n\n# 结合 git diff\ngit diff | claude "总结这些变更"', 0.6, 3.55, 4.2, 1.1);

// Right side
s5.addText("适用场景", { x: 5.2, y: 1.1, w: 4, h: 0.35, fontSize: 15, color: C.highlight, fontFace: "Arial", bold: true, margin: 0 });
addCard(s5, "CI/CD 集成", "在自动化流水线中使用\n代码审查、生成测试", 5.2, 1.55, 4.2, 0.9, C.accent);
addCard(s5, "批量处理", "脚本化处理多个文件\n自动化重复任务", 5.2, 2.6, 4.2, 0.9, C.green);
addCard(s5, "快速查询", "一行命令获取答案\n无需启动完整会话", 5.2, 3.65, 4.2, 0.9, C.highlight);

// ========================================================
// SLIDE 6: Slash Commands
// ========================================================
let s6 = pres.addSlide();
s6.background = { color: C.darkBg };
addSectionBar(s6, "斜杠命令一览");
addFooter(s6, 6, TOTAL);

s6.addText("输入 / 后自动补全，或使用以下常用命令", { x: 0.6, y: 1.05, w: 8.8, h: 0.35, fontSize: 12, color: C.muted, fontFace: "Arial", margin: 0 });

const cmds = [
  ["/help", "查看所有可用命令"],
  ["/clear", "清除对话历史"],
  ["/compact", "压缩对话以节省上下文窗口"],
  ["/cost", "查看 Token 使用量和费用"],
  ["/config", "管理配置设置"],
  ["/memory", "编辑 CLAUDE.md 记忆文件"],
  ["/permissions", "查看和管理工具权限"],
  ["/doctor", "诊断安装和配置问题"],
  ["/login /logout", "登录/登出账号"],
  ["/vim", "切换 Vim 编辑模式"],
  ["/init", "初始化项目 CLAUDE.md 文件"],
];

let tableData = [
  [
    { text: "命令", options: { fill: { color: C.codeBg }, color: C.accent, bold: true, fontSize: 12, fontFace: "Arial", align: "center" } },
    { text: "说明", options: { fill: { color: C.codeBg }, color: C.accent, bold: true, fontSize: 12, fontFace: "Arial", align: "center" } },
  ],
];
cmds.forEach((cmd, i) => {
  tableData.push([
    { text: cmd[0], options: { fill: { color: i % 2 === 0 ? C.medBg : C.darkBg }, color: C.highlight, fontSize: 11, fontFace: "Consolas", bold: true } },
    { text: cmd[1], options: { fill: { color: i % 2 === 0 ? C.medBg : C.darkBg }, color: C.light, fontSize: 11, fontFace: "Arial" } },
  ]);
});
s6.addTable(tableData, { x: 0.6, y: 1.45, w: 8.8, colW: [2.5, 6.3], border: { pt: 0.5, color: "5D3830" } });

// ========================================================
// SLIDE 7: CLAUDE.md (FIXED: code block shorter)
// ========================================================
let s7 = pres.addSlide();
s7.background = { color: C.darkBg };
addSectionBar(s7, "CLAUDE.md 项目指令文件");
addFooter(s7, 7, TOTAL);

s7.addText("CLAUDE.md 是 Claude Code 的持久化记忆系统，让 Claude 在每次会话中都了解你的项目", {
  x: 0.6, y: 1.05, w: 8.8, h: 0.45, fontSize: 12, color: C.light, fontFace: "Arial", margin: 0
});

// Left column - 3 cards same height
s7.addText("文件位置", { x: 0.6, y: 1.6, w: 4, h: 0.35, fontSize: 14, color: C.highlight, fontFace: "Arial", bold: true, margin: 0 });
addCard(s7, "项目根目录", "CLAUDE.md — 项目级指令\n所有会话生效", 0.6, 2.0, 4.1, 0.9, C.accent);
addCard(s7, "子目录", "子目录/CLAUDE.md\n特定文件夹的专属指令", 0.6, 3.05, 4.1, 0.9, C.green);
addCard(s7, "用户全局", "~/.claude/CLAUDE.md\n跨项目的个人偏好", 0.6, 4.1, 4.1, 0.9, "A23B72");

// Right column - shorter code block
s7.addText("示例内容", { x: 5.2, y: 1.6, w: 4, h: 0.35, fontSize: 14, color: C.highlight, fontFace: "Arial", bold: true, margin: 0 });
addCodeBlock(s7, '# CLAUDE.md\n\n## 项目信息\nReact + TypeScript 项目\n\n## 构建命令\n- npm install\n- npm test\n- npm run build\n\n## 代码规范\nESLint + Prettier', 5.2, 2.0, 4.2, 2.8);

// ========================================================
// SLIDE 8: Permission Modes (FIXED: balanced 2x2 grid)
// ========================================================
let s8 = pres.addSlide();
s8.background = { color: C.darkBg };
addSectionBar(s8, "权限管理与安全控制");
addFooter(s8, 8, TOTAL);

s8.addText("Claude Code 默认在使用工具前请求用户确认，确保安全可控", {
  x: 0.6, y: 1.05, w: 8.8, h: 0.45, fontSize: 12, color: C.light, fontFace: "Arial", margin: 0
});

// 2x2 grid - all same height
addCard(s8, "默认模式", "执行文件写入、Shell 命令等\n操作前需用户确认", 0.6, 1.65, 4.1, 1.0, C.accent);
addCard(s8, "自动接受模式", "Shift+Tab 开启\n自动批准所有工具调用", 5.3, 1.65, 4.1, 1.0, C.green);
addCard(s8, "CI/CD 模式", "跳过所有权限检查\n仅限沙盒/CI 环境", 0.6, 2.85, 4.1, 1.0, C.red);
addCard(s8, "工具级控制", "--allowedTools 精细控制\n按需分配工具权限", 5.3, 2.85, 4.1, 1.0, "A23B72");

// Code example below
addCodeBlock(s8, '# 允许特定工具\nclaude --allowedTools=Bash,Write,Edit\n\n# 查看当前权限\n> /permissions', 0.6, 4.05, 8.8, 1.0);

// ========================================================
// SLIDE 9: MCP Support (FIXED: shorter code block)
// ========================================================
let s9 = pres.addSlide();
s9.background = { color: C.darkBg };
addSectionBar(s9, "MCP 服务器扩展");
addFooter(s9, 9, TOTAL);

s9.addText("Model Context Protocol (MCP) 让 Claude Code 连接外部工具和数据源", {
  x: 0.6, y: 1.05, w: 8.8, h: 0.45, fontSize: 12, color: C.light, fontFace: "Arial", margin: 0
});

// Left - What is MCP
s9.addText("什么是 MCP？", { x: 0.6, y: 1.6, w: 4, h: 0.35, fontSize: 14, color: C.highlight, fontFace: "Arial", bold: true, margin: 0 });
s9.addText([
  { text: "开放协议，扩展 Claude 能力边界", options: { bullet: true, breakLine: true } },
  { text: "连接数据库、API、文件系统等资源", options: { bullet: true, breakLine: true } },
  { text: "权限与内置工具统一管理", options: { bullet: true } },
], { x: 0.6, y: 2.0, w: 4.2, h: 1.0, fontSize: 11, color: C.light, fontFace: "Arial" });

// Left - Config (shorter code)
s9.addText("配置方式", { x: 0.6, y: 3.1, w: 4, h: 0.35, fontSize: 14, color: C.highlight, fontFace: "Arial", bold: true, margin: 0 });
addCodeBlock(s9, '// .mcp.json\n{\n  "mcpServers": {\n    "my-server": {\n      "command": "npx",\n      "args": ["my-mcp-server"]\n    }\n  }\n}', 0.6, 3.5, 4.2, 1.5);

// Right - use cases
s9.addText("典型场景", { x: 5.2, y: 1.6, w: 4, h: 0.35, fontSize: 14, color: C.highlight, fontFace: "Arial", bold: true, margin: 0 });
addCard(s9, "数据库查询", "连接 PostgreSQL/MySQL\n直接查询和分析数据", 5.2, 2.0, 4.2, 0.95, C.accent);
addCard(s9, "API 集成", "调用内部 REST API\n获取实时数据", 5.2, 3.1, 4.2, 0.95, C.green);
addCard(s9, "自定义工具", "创建专属 MCP 服务器\n满足特定业务需求", 5.2, 4.2, 4.2, 0.95, "A23B72");

// ========================================================
// SLIDE 10: Advanced Features (added subtitle)
// ========================================================
let s10 = pres.addSlide();
s10.background = { color: C.darkBg };
addSectionBar(s10, "高级功能");
addFooter(s10, 10, TOTAL);

s10.addText("更多进阶能力，让你的开发工作流更高效", {
  x: 0.6, y: 1.05, w: 8.8, h: 0.45, fontSize: 12, color: C.light, fontFace: "Arial", margin: 0
});

const features = [
  { title: "会话管理", desc: "恢复、继续和压缩历史会话\n支持多会话并行", color: C.accent },
  { title: "扩展思考", desc: "--thinking 参数启用深度推理\n适合复杂架构决策", color: C.highlight },
  { title: "模型选择", desc: "--model 指定不同模型\n按任务复杂度灵活切换", color: C.green },
  { title: "上下文压缩", desc: "/compact 压缩长对话\n突破上下文窗口限制", color: "A23B72" },
  { title: "Token 追踪", desc: "/cost 实时查看使用量\n监控 API 费用", color: C.accent },
  { title: "Git 集成", desc: "自动识别分支和 diff\n智能提交信息生成", color: C.highlight },
];

features.forEach((f, i) => {
  let col = i % 2;
  let row = Math.floor(i / 2);
  let xPos = 0.6 + col * 4.7;
  let yPos = 1.6 + row * 1.15;
  addCard(s10, f.title, f.desc, xPos, yPos, 4.1, 1.0, f.color);
});

// ========================================================
// SLIDE 11: Best Practices (FIXED: added card backgrounds)
// ========================================================
let s11 = pres.addSlide();
s11.background = { color: C.darkBg };
addSectionBar(s11, "最佳实践与使用技巧");
addFooter(s11, 11, TOTAL);

// 4 quadrants with card backgrounds
// Top-left
s11.addShape(pres.shapes.RECTANGLE, { x: 0.6, y: 1.1, w: 4.1, h: 1.85, fill: { color: C.medBg }, shadow: mkShadow() });
s11.addText("项目配置", { x: 0.8, y: 1.15, w: 3.7, h: 0.35, fontSize: 14, color: C.accent, fontFace: "Arial", bold: true, margin: 0 });
s11.addText([
  { text: "编写详细的 CLAUDE.md", options: { bullet: true, breakLine: true } },
  { text: "包含构建、测试、部署命令", options: { bullet: true, breakLine: true } },
  { text: "说明代码规范和架构约定", options: { bullet: true, breakLine: true } },
  { text: "使用 /init 快速初始化", options: { bullet: true } },
], { x: 0.8, y: 1.5, w: 3.7, h: 1.3, fontSize: 11, color: C.light, fontFace: "Arial" });

// Top-right
s11.addShape(pres.shapes.RECTANGLE, { x: 5.3, y: 1.1, w: 4.1, h: 1.85, fill: { color: C.medBg }, shadow: mkShadow() });
s11.addText("安全建议", { x: 5.5, y: 1.15, w: 3.7, h: 0.35, fontSize: 14, color: C.red, fontFace: "Arial", bold: true, margin: 0 });
s11.addText([
  { text: "避免在生产环境跳过权限", options: { bullet: true, breakLine: true } },
  { text: "使用 --allowedTools 精细控制", options: { bullet: true, breakLine: true } },
  { text: "敏感操作前让 Claude 解释计划", options: { bullet: true, breakLine: true } },
  { text: "定期检查 /permissions 配置", options: { bullet: true } },
], { x: 5.5, y: 1.5, w: 3.7, h: 1.3, fontSize: 11, color: C.light, fontFace: "Arial" });

// Bottom-left
s11.addShape(pres.shapes.RECTANGLE, { x: 0.6, y: 3.15, w: 4.1, h: 1.85, fill: { color: C.medBg }, shadow: mkShadow() });
s11.addText("效率提升", { x: 0.8, y: 3.2, w: 3.7, h: 0.35, fontSize: 14, color: C.green, fontFace: "Arial", bold: true, margin: 0 });
s11.addText([
  { text: "善用 /compact 管理上下文", options: { bullet: true, breakLine: true } },
  { text: "Shift+Tab 批量操作时开启", options: { bullet: true, breakLine: true } },
  { text: "用 -p 模式集成到脚本", options: { bullet: true, breakLine: true } },
  { text: "# 添加会话内记忆", options: { bullet: true } },
], { x: 0.8, y: 3.55, w: 3.7, h: 1.3, fontSize: 11, color: C.light, fontFace: "Arial" });

// Bottom-right
s11.addShape(pres.shapes.RECTANGLE, { x: 5.3, y: 3.15, w: 4.1, h: 1.85, fill: { color: C.medBg }, shadow: mkShadow() });
s11.addText("常见场景", { x: 5.5, y: 3.2, w: 3.7, h: 0.35, fontSize: 14, color: C.highlight, fontFace: "Arial", bold: true, margin: 0 });
s11.addText([
  { text: "代码审查: git diff | claude", options: { bullet: true, breakLine: true } },
  { text: "Bug 定位: 描述问题让 Claude 分析", options: { bullet: true, breakLine: true } },
  { text: "重构: 说明目标，Claude 规划步骤", options: { bullet: true, breakLine: true } },
  { text: "文档生成: 自动创建 README/注释", options: { bullet: true } },
], { x: 5.5, y: 3.55, w: 3.7, h: 1.3, fontSize: 11, color: C.light, fontFace: "Arial" });

// ========================================================
// SLIDE 12: Thank You (FIXED: balanced layout)
// ========================================================
let s12 = pres.addSlide();
s12.background = { color: C.darkBg };
s12.addShape(pres.shapes.RECTANGLE, { x: 0, y: 0, w: 10, h: 5.625, fill: { color: C.primary, transparency: 30 } });
// Right decorative block
s12.addShape(pres.shapes.RECTANGLE, { x: 6.5, y: 1.2, w: 3.2, h: 3.2, fill: { color: C.accent, transparency: 70 } });
s12.addShape(pres.shapes.RECTANGLE, { x: 7.0, y: 1.7, w: 2.5, h: 2.5, fill: { color: C.highlight, transparency: 60 } });
// Left accent bar
s12.addShape(pres.shapes.RECTANGLE, { x: 0.8, y: 1.8, w: 0.08, h: 1.8, fill: { color: C.highlight } });
s12.addText("Thank You", { x: 1.1, y: 1.8, w: 5, h: 1.0, fontSize: 42, color: C.white, fontFace: "Arial", bold: true, margin: 0 });
s12.addText("开始你的 Claude Code 之旅", { x: 1.1, y: 2.7, w: 5, h: 0.6, fontSize: 22, color: C.accent, fontFace: "Arial", margin: 0 });

s12.addText([
  { text: "官方文档: ", options: { bold: true, color: C.muted } },
  { text: "docs.anthropic.com/en/docs/claude-code", options: { color: C.accent } },
], { x: 1.1, y: 3.5, w: 5, h: 0.35, fontSize: 12, fontFace: "Arial", margin: 0 });
s12.addText([
  { text: "GitHub: ", options: { bold: true, color: C.muted } },
  { text: "github.com/anthropics/claude-code", options: { color: C.accent } },
], { x: 1.1, y: 3.85, w: 5, h: 0.35, fontSize: 12, fontFace: "Arial", margin: 0 });

// Bottom bar
s12.addShape(pres.shapes.RECTANGLE, { x: 0, y: 4.8, w: 10, h: 0.825, fill: { color: C.darkBg } });
s12.addText("npm install -g @anthropic-ai/claude-code", { x: 0.8, y: 4.9, w: 8, h: 0.4, fontSize: 12, color: C.light, fontFace: "Consolas" });

// ========== Write File ==========
pres.writeFile({ fileName: "D:/pycharm/Person-Practice/PPT/Claude_Code_CLI_使用指南.pptx" })
  .then(() => console.log("PPT created successfully!"))
  .catch(err => console.error("Error:", err));
