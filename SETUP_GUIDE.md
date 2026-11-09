# Job Apply Bot — 从零开始使用指南

> 把这份文档喂给你的 Claude Code，它就能帮你自动搜索职位、筛选评分、打开网页填表。
> 你只需要：**配好环境 → 填好个人资料 → 告诉 Claude 你要投什么 → 检查表单后自己点 Submit**。

---

## 目录

1. [这个项目能做什么](#1-这个项目能做什么)
2. [环境准备（约 15 分钟）](#2-环境准备约-15-分钟)
3. [配置你的个人资料](#3-配置你的个人资料)
4. [让 Claude 认识你的背景——修改 CLAUDE.md](#4-让-claude-认识你的背景修改-claudemd)
5. [定制搜索引擎——修改 discover.py](#5-定制搜索引擎修改-discoverpy)
6. [定制评分规则——修改 evaluate.py](#6-定制评分规则修改-evaluatepy)
7. [做一份你自己的公司清单（可选）](#7-做一份你自己的公司清单可选)
8. [邮箱验证码自动读取（可选）](#8-邮箱验证码自动读取可选)
9. [日常使用流程](#9-日常使用流程)
10. [常见问题 / 踩坑记录](#10-常见问题--踩坑记录)

---

## 1. 这个项目能做什么

```
你说 "搜索职位"
  → discover.py 自动抓 Indeed + LinkedIn 上的职位
  → evaluate.py 自动筛掉不相关的、打分排序
  → Claude 列出结果表，你选一个数字
  → Claude 用 Playwright 浏览器打开申请页面，自动填写所有字段
  → 你检查一遍，自己点 Submit
```

**核心原则：Claude 绝不会帮你点提交按钮。** 它只填表，最终提交由你自己完成。

### 项目文件一览

| 文件 | 作用 |
|------|------|
| `profile.json` | 你的个人信息（姓名、学历、经历、技能等），Claude 从这里读数据填表 |
| `CLAUDE.md` | Claude 的行为规则——怎么填表、怎么回答开放题、什么情况要问你 |
| `discover.py` | 职位搜索脚本——定义搜哪些关键词、搜哪个地区 |
| `evaluate.py` | 职位评分脚本——定义哪些关键词加分、哪些扣分、哪些直接过滤 |
| `company_list.md` | 目标公司清单（按 tier 分类），用于定向搜索 |
| `email_code.py` | Gmail 验证码自动读取（部分申请系统会发验证码到邮箱） |
| `applied_companies.json` | 已投递记录——防止重复投递 |

---

## 2. 环境准备（约 15 分钟）

### 2.1 安装前提

你需要以下工具，全部免费：

| 工具 | 用途 | 安装方式 |
|------|------|---------|
| **Python 3.12+** | 运行搜索/评分脚本 | `brew install python` (Mac) 或去 python.org 下载 |
| **uv** | Python 包管理器（比 pip 快） | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| **Claude Code** | CLI 版 Claude，能调用工具 | `npm install -g @anthropic-ai/claude-code` |
| **Node.js 18+** | Claude Code 和 Playwright 需要 | `brew install node` (Mac) 或去 nodejs.org |

### 2.2 获取项目代码

```bash
# 方式 A：从 GitHub clone（如果项目已上传）
git clone <repo-url> job-apply-bot
cd job-apply-bot

# 方式 B：直接拿到整个文件夹拷贝过来
cp -r /path/to/job-apply-bot ~/job-apply-bot
cd ~/job-apply-bot
```

### 2.3 安装 Python 依赖

```bash
uv sync
```

这会根据 `pyproject.toml` 安装 `python-jobspy`（职位抓取库）和 `tabulate`。

### 2.4 配置 Playwright MCP（让 Claude 能操控浏览器）

```bash
claude mcp add playwright -- npx @playwright/mcp@latest
```

这一步让 Claude 获得了打开浏览器、点击、填表的能力。

### 2.5 启动 Claude Code

```bash
cd ~/job-apply-bot
claude
```

首次启动时 Claude 会自动读取 `CLAUDE.md`，你会看到它加载了项目规则。

### 2.6 推荐设置（在 Claude Code 内输入）

```
/model opus          # 使用最强模型（表单填写更准确）
/permissions         # 选 bypassPermissions（免得每步都要确认）
```

---

## 3. 配置你的个人资料

这是**最重要的一步**。`profile.json` 是 Claude 填表时的数据源。

### 3.1 从模板开始

```bash
cp profile.template.json profile.json
```

然后用编辑器打开 `profile.json`，逐项填写。

### 3.2 完整字段说明

下面是每个字段的含义。**你不需要全部填完**，只填跟你相关的部分，Claude 遇到空字段会跳过或问你。

```jsonc
{
  // ═══════════════════════════════════════════
  // CV 路径——绝对路径，指向你的简历 PDF
  // ═══════════════════════════════════════════
  "cv_path": "/Users/你的用户名/Desktop/你的简历.pdf",

  // ═══════════════════════════════════════════
  // 个人信息
  // ═══════════════════════════════════════════
  "personal": {
    "first_name": "名",
    "last_name": "姓",
    "email": "你的邮箱@gmail.com",
    "phone_country_code": "+353",   // 爱尔兰 +353，中国 +86，英国 +44
    "phone_number": "870015190",    // 不含国家码
    "address_line1": "你的地址",
    "city": "Dublin",
    "postcode": "D04 P6P7",
    "country": "Ireland",
    "linkedin": "https://www.linkedin.com/in/你的ID/",
    "github": ""                    // 没有就留空
  },

  // ═══════════════════════════════════════════
  // 工作许可——根据你自己的签证类型填
  // ═══════════════════════════════════════════
  "work_permit": {
    "country": "Ireland",
    "document": "Stamp 1G",         // 改成你自己的：Stamp 1G / Stamp 2 / EU Citizen 等
    "notes": "2-year graduate work permission"
  },

  // ═══════════════════════════════════════════
  // 学历——按你的实际情况填
  // 如果没有研究生学历，整个 postgraduate 块可以删掉或留空
  // ═══════════════════════════════════════════
  "education": {
    "postgraduate": {
      "degree": "MSc Computer Science",  // 你的学位名称
      "university": "University College Dublin",
      "university_short": "UCD",
      "country": "Ireland",
      "start_day": 7, "start_month": "September", "start_year": 2026,
      "end_day": 1, "end_month": "January", "end_year": 2028,
      "expected_results": "2:1",
      "modules": "列出你的核心课程，逗号分隔"
    },
    "undergraduate": {
      "degree": "BComm International",   // ← 商科同学改成你的学位
      "degree_type": "BComm",            // 学位类型缩写
      "degree_subject": "Business",      // 学科领域
      "university": "你的本科大学全名",
      "country": "China",
      "field_of_study": "Business",
      "start_day": 1, "start_month": "September", "start_year": 2022,
      "end_day": 30, "end_month": "June", "end_year": 2026,
      "results": "2:1",
      "high_school_results": "Chinese Gaokao: 554/750",
      "leaving_cert_ireland": false      // 非爱尔兰高中 → false
    }
  },

  // ═══════════════════════════════════════════
  // 工作/实习经历——按时间倒序排列
  // 每段经历包含 title, company, start, end, highlights
  // highlights 是要点列表，Claude 填 Work Experience 时直接用
  // ═══════════════════════════════════════════
  "experience": [
    {
      "title": "Marketing Intern",
      "company": "某某公司",
      "start": "June 2025",
      "end": "August 2025",
      "highlights": [
        "Managed social media campaigns reaching 50K+ users across 3 platforms",
        "Analysed customer data with Excel and Tableau to identify purchasing trends",
        "Coordinated cross-functional team of 5 to deliver product launch event"
      ]
    },
    {
      "title": "Business Analyst Intern",
      "company": "另一个公司",
      "start": "January 2025",
      "end": "April 2025",
      "highlights": [
        "Created weekly performance dashboards using Power BI for 3 departments",
        "Conducted competitor analysis and presented findings to senior management"
      ]
    }
  ],

  // ═══════════════════════════════════════════
  // 技能——根据你的背景分类填写
  // 非技术专业也有很多可写的：Excel, SQL, Tableau, PowerBI, Python 等
  // ═══════════════════════════════════════════
  "skills": {
    "languages": ["English", "Mandarin"],      // 语言能力
    "tools": ["Excel", "PowerPoint", "Tableau", "Power BI", "SQL"],
    "frameworks": [],                           // 技术框架（没有就留空）
    "databases": [],
    "devops": [],
    "soft_skills": ["Communication", "Teamwork", "Problem-Solving", "Leadership"]
  },

  // ═══════════════════════════════════════════
  // 课外活动 & 兴趣
  // ═══════════════════════════════════════════
  "extras": {
    "activities": "Captain of the university debate team",
    "interests": "Travelling, Reading, Fitness"
  },

  // ═══════════════════════════════════════════
  // 可到岗时间——根据你的毕业时间调整
  // ═══════════════════════════════════════════
  "availability": {
    "grad_programme_start": "September 2027",
    "internship_start": "Immediate Availability",
    "summer_2027_internship": "Available Summer 2027 (June-August)",
    "postgrad_graduation": "January 2028"
  },

  // ═══════════════════════════════════════════
  // 常见问题标准答案——根据你的情况改
  // ═══════════════════════════════════════════
  "common_answers": {
    "age_18_plus": true,
    "second_undergraduate": false,
    "leaving_cert_ireland": false,
    "right_to_work_ireland": true,     // 有合法工作许可 → true
    "reasonable_adjustments": false,
    "gender": "Male",                  // 或 "Female" / "Non-binary" / "Prefer not to say"
    "pronouns": "He/Him"               // 或 "She/Her" / "They/Them"
  }
}
```

> **注意：** 上面的注释 (`//`) 仅作说明，实际 JSON 文件**不支持注释**。填完后把所有 `//` 注释行删掉。

### 3.3 可选：账号密码和 Gmail 配置

如果你希望 Claude 自动帮你注册 Workday 等平台账号、或自动读取邮箱验证码，可以加这些：

```json
{
  "gmail": {
    "email": "你的邮箱@gmail.com",
    "app_password": "xxxx xxxx xxxx xxxx"
  },
  "account_passwords": {
    "default": "你的常用密码",
    "workday": "你的Workday密码"
  }
}
```

Gmail App Password 获取方式：Google Account → Security → 2-Step Verification → App passwords → 生成一个。

> **安全提醒：** `profile.json` 已在 `.gitignore` 中，不会被提交到 Git。但请确保不要手动上传或分享这个文件。

---

## 4. 让 Claude 认识你的背景——修改 CLAUDE.md

`CLAUDE.md` 是 Claude 每次启动时自动读取的行为规则。你需要把里面**所有跟原作者相关的内容**改成你自己的。

### 4.1 必须修改的部分

打开 `CLAUDE.md`，找到并修改以下段落：

#### (A) Open-Text / Essay Questions（开放题模板）

原文中有针对软件工程背景的回答策略。**商科同学要整段替换：**

```markdown
### Open-Text / Essay Questions
Write answers automatically using the user's profile. Always:
- Reference specific internship experience (company names, tasks performed)
- Mention concrete skills (data analysis, client management, financial modelling, etc.)
- Reference current postgraduate studies if relevant
- Keep answers professional and specific, not generic

Common open-text questions and approach:
- "Why this role/company?" → Link their studies and internship experience to the company's industry and values
- "What are your key skills?" → List from experience: data analysis, stakeholder management, project coordination, client communication
- "Greatest achievement?" → Lead with a specific internship/university project result with quantified impact
- "Skills list" → Excel, SQL, Tableau, Power BI, Financial Modelling, Market Research, Project Management, Communication, Teamwork
```

#### (B) Work Experience（工作经历模板）

把两段经历改成你自己的：

```markdown
### Work Experience
When the form has a Work Experience / Employment History section, fill ALL entries from `experience` in profile.json:

**Entry 1 (most recent):**
- Job title: 你的最近职位
- Company: 你的公司名
- Start: 月 年 / End: 月 年
- Description: 用1-3句话描述你做了什么，尽量用数字量化结果

**Entry 2:**
- （同上格式填第二段经历）

If only one work experience slot is available, use Entry 1 (most recent).
```

#### (C) Skills list

找到所有技能列表的地方，替换成你的技能。全文搜索 `Java` 或 `Spring Boot` 即可找到所有相关位置。

#### (D) Pre-fill checks（填表前检查规则）

如果你的签证/工作许可跟原作者不同，修改这段：

```markdown
## Flags to Raise Before Filling

Always check and flag to user BEFORE filling:
1. **Outside Ireland**: 你的签证类型 only valid in Ireland — UK/other countries need confirmation
2. **Off-topic role**: 改成你不想投的行业 — confirm with user
3. **Availability conflict**: Graduate programme starts before 你的最早可到岗时间 — confirm with user
4. **Sponsorship required**: If the role requires visa sponsorship which user cannot provide
```

### 4.2 不需要改的部分

以下内容是通用逻辑，不用改：
- Step-by-Step Process（导航→快照→填表的流程）
- Personal Details（从 profile.json 读个人信息的规则）
- CV Upload（上传简历的方式）
- Gmail Verification Code（验证码读取）
- Multi-Tab Rule（多标签页规则）
- After Filling（填完后的汇报规则）
- Missing Information（缺失信息的处理）
- Recording Applications（记录已投递的逻辑）

---

## 5. 定制搜索引擎——修改 discover.py

`discover.py` 决定了搜什么职位。原版全是软件工程相关搜索词，**商科同学必须改**。

### 5.1 修改搜索关键词

打开 `discover.py`，找到 `SEARCHES` 列表（大约第 86 行），改成你的目标职位：

```python
SEARCHES = [
    # Graduate programmes
    {"query": "Business Graduate Programme",          "location": "Dublin, Ireland"},
    {"query": "Finance Graduate Programme",           "location": "Ireland"},
    {"query": "Marketing Graduate Programme",         "location": "Dublin, Ireland"},
    {"query": "Consulting Graduate Programme",        "location": "Ireland"},
    {"query": "Management Graduate Scheme",           "location": "Ireland"},
    {"query": "Commercial Graduate Programme",        "location": "Ireland"},
    {"query": "Operations Graduate",                  "location": "Ireland"},
    # Internships
    {"query": "Business Analyst Intern",              "location": "Dublin, Ireland"},
    {"query": "Marketing Intern",                     "location": "Dublin, Ireland"},
    {"query": "Finance Intern",                       "location": "Ireland"},
    {"query": "HR Intern",                            "location": "Dublin, Ireland"},
    {"query": "Supply Chain Intern",                  "location": "Ireland"},
    {"query": "Consulting Intern",                    "location": "Ireland"},
    {"query": "Project Management Intern",            "location": "Ireland"},
    {"query": "Data Analyst Intern",                  "location": "Dublin, Ireland"},
    # Broader
    {"query": "Graduate Trainee Business",            "location": "Ireland"},
    {"query": "Junior Business Analyst",              "location": "Ireland"},
    {"query": "Junior Account Executive",             "location": "Dublin, Ireland"},
    {"query": "Graduate Accountant",                  "location": "Ireland"},
]
```

### 5.2 修改评分关键词

在同一文件中找到 `KEYWORDS` 列表（大约第 107 行），改成你的：

```python
KEYWORDS = [
    "business", "finance", "marketing", "consulting", "analyst",
    "management", "operations", "strategy", "accounting", "commercial",
    "project management", "excel", "sql", "tableau", "power bi",
    "graduate", "intern", "entry level", "junior", "ireland", "dublin",
]
```

### 5.3 搜索参数调整

```python
HOURS   = 336   # 搜最近 14 天的职位（168=7天，336=14天，720=30天）
RESULTS = 25    # 每次搜索每个平台返回多少条（越大越慢但更全）
```

---

## 6. 定制评分规则——修改 evaluate.py

`evaluate.py` 决定了哪些职位被过滤掉、哪些得高分。

### 6.1 修改到岗时间限制

找到文件顶部（约第 14 行）：

```python
GRAD_MIN_YEAR  = 2027
GRAD_MIN_MONTH = 9   # September
```

改成你自己的最早可到岗时间。例如你 2027 年 6 月本科毕业：

```python
GRAD_MIN_YEAR  = 2027
GRAD_MIN_MONTH = 6   # June — 毕业后即可到岗
```

### 6.2 修改加分关键词

找到 `FIT_POSITIVE` 字典，改成你的目标领域：

```python
FIT_POSITIVE = {
    # 目标岗位类型
    "business analyst": 2, "data analyst": 2, "financial analyst": 2,
    "marketing": 1, "consulting": 1, "operations": 1,
    "project management": 1, "account executive": 1,
    # 你会的技能
    "excel": 1, "sql": 1, "tableau": 1, "power bi": 1, "python": 1,
    # 入门级标识
    "graduate": 2, "intern": 2, "entry level": 1, "junior": 1, "trainee": 1,
    # 地点偏好
    "dublin": 2, "cork": 1, "remote": 1, "hybrid": 1, "ireland": 1,
}
```

### 6.3 修改减分关键词

```python
FIT_NEGATIVE = {
    "senior": -2, "lead": -2, "manager": -2, "director": -2,
    "5 years": -2, "5+ years": -2, "7 years": -2, "10 years": -2,
    "minimum 3 years": -1, "3+ years": -1,
}
```

### 6.4 修改 "Off-topic" 过滤词

原版过滤了 finance、marketing 等（因为原作者是软件工程）。**商科同学要反过来！** 把软件/工程类改成 off-topic：

```python
OFF_TOPIC_TITLE_KEYWORDS = [
    # 跟商科无关的工程岗
    "software engineer", "backend developer", "frontend developer",
    "devops engineer", "site reliability", "embedded engineer",
    "mechanical engineer", "electrical engineer", "civil engineer",
    "structural engineer", "geotechnical",
    # 医疗/护理
    "nurse", "nursing", "clinical", "pharmacy", "pharmacist",
    "physiotherap", "occupational therap",
    # 其他明确不相关的
    "chef", "driver", "warehouse operative", "security guard",
    "cleaner", "barista", "retail assistant",
]
```

> **原则：** 只过滤你**绝对不会投**的岗位。宁可放过一些不太相关的，也不要误杀可能感兴趣的。

### 6.5 修改 UK 过滤

如果你有英国工作权利（比如 UK Graduate Visa），可以把 `is_uk` 函数改成 `return False`，这样英国的职位也会保留：

```python
def is_uk(location: str, description: str) -> bool:
    return False  # 如果你可以在英国工作
```

---

## 7. 做一份你自己的公司清单（可选）

`company_list.md` 让你可以按公司定向搜索。格式很简单：

```markdown
# 目标公司清单

## S+ 大厂
Google · Microsoft · Amazon · Meta · Apple

## A 级 — 四大/咨询
Accenture · Deloitte · PwC · EY · KPMG · McKinsey · BCG

## B 级 — 金融
JPMorgan · Goldman Sachs · Citi · Bank of Ireland · AIB

## C 级 — FMCG / Consumer
Unilever · P&G · L'Oreal · Diageo · Kerry Group · Musgrave
```

使用方式：
```
# 在 Claude Code 中
搜大厂          → 搜索所有未投递的公司
搜 S+ tier      → 只搜 S+ 级别
check tier list → 同上，英文版
```

---

## 8. 邮箱验证码自动读取（可选）

一些申请系统（Oracle、Workday）会发验证码到你邮箱。如果你配置了 Gmail App Password，Claude 会自动读取。

**配置方法：**

1. 在 `profile.json` 中添加 `gmail` 字段（见 3.3 节）
2. 确保 Gmail 开启了 IMAP：Gmail Settings → See all settings → Forwarding and POP/IMAP → Enable IMAP
3. Claude 会自动运行 `uv run python email_code.py --wait` 来获取验证码

不配置也完全可以用——遇到验证码时 Claude 会让你手动输入。

---

## 9. 日常使用流程

### 9.1 搜索+投递完整流程

```
你：搜索职位
Claude：（运行 discover.py + evaluate.py，显示结果表）

✅  15 jobs ready to apply:

#   Fit  Type   Title                                Company              Location
───────────────────────────────────────────────────────────────────────────────
1   8    GRAD   Business Graduate Programme           Accenture            Dublin, Ireland
2   7    INTERN Marketing Intern - Summer 2027        Deloitte             Dublin, Ireland
3   6    GRAD   Finance Graduate Scheme               AIB                  Dublin, Ireland
...

你：1
Claude：（打开浏览器，自动填写 Accenture 的申请表）
Claude：请检查表单，确认无误后点击 Submit。
你：（检查后自己点 Submit）
```

### 9.2 直接给 URL

```
你：https://careers.deloitte.com/job/12345
Claude：（打开网页，自动填表，汇报结果）
```

### 9.3 批量投递

```
你：全部投递 1 2 3 5 8
Claude：（用 subagent 并行填写多个表单，每个在新标签页）
```

### 9.4 定向搜公司

```
你：搜大厂
你：搜 A 级
```

---

## 10. 常见问题 / 踩坑记录

### Q: 运行 discover.py 报错 "No module named 'jobspy'"
```bash
uv sync   # 重新安装依赖
```

### Q: Claude 说 "Playwright MCP not found"
```bash
claude mcp add playwright -- npx @playwright/mcp@latest
# 然后重启 Claude Code
```

### Q: 浏览器打不开 / 超时
确保 Node.js 已安装且版本 >= 18：
```bash
node --version
npx @playwright/mcp@latest   # 首次运行会自动安装浏览器
```

### Q: CV 上传失败
确保 `cv_path` 是**绝对路径**（以 `/` 开头），文件确实存在：
```bash
ls -la "/Users/你的用户名/Desktop/你的简历.pdf"
```

### Q: 搜到的职位太少 / 太多不相关
- 太少 → 增大 `HOURS`（比如 720 = 30天），增大 `RESULTS`，增加 `SEARCHES` 关键词
- 太多不相关 → 在 `OFF_TOPIC_TITLE_KEYWORDS` 中加入你不想看到的职位关键词
- 评分不准 → 调整 `FIT_POSITIVE` 和 `FIT_NEGATIVE` 的关键词和权重

### Q: Claude 填错了某个字段怎么办
表单还没提交之前，你可以：
1. 直接在浏览器里手动修改
2. 告诉 Claude 哪里错了，它会帮你改

### Q: 我不是在爱尔兰，怎么改
1. `profile.json` → 改 `personal.country`、`work_permit`
2. `discover.py` → 改所有 `location` 字段，以及 `country_indeed` 参数
3. `evaluate.py` → 修改/删除 `is_uk` 函数和 `UK_LOCATIONS` 列表
4. `CLAUDE.md` → 修改 "Flags to Raise" 中的地区规则

### Q: profile.json 里的密码安全吗
`profile.json` 在 `.gitignore` 中，不会被 Git 追踪。但请注意：
- 不要手动把它上传到任何地方
- 如果 fork 了这个项目，确保 `.gitignore` 包含 `profile.json`
- Gmail App Password 可以随时在 Google Account 中撤销

---

## 快速上手 Checklist

- [ ] 安装 Python 3.12+, uv, Node.js, Claude Code
- [ ] `uv sync` 安装依赖
- [ ] `claude mcp add playwright -- npx @playwright/mcp@latest`
- [ ] `cp profile.template.json profile.json` 并填写你的信息
- [ ] 修改 `CLAUDE.md` 中的开放题模板、工作经历、技能列表
- [ ] 修改 `discover.py` 中的搜索关键词（`SEARCHES` + `KEYWORDS`）
- [ ] 修改 `evaluate.py` 中的评分规则（`FIT_POSITIVE` + `FIT_NEGATIVE` + `OFF_TOPIC_TITLE_KEYWORDS`）
- [ ] （可选）编辑 `company_list.md`
- [ ] （可选）配置 Gmail App Password
- [ ] `cd ~/job-apply-bot && claude` 开始使用！
