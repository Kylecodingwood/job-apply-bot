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
10. [实战踩坑经验 & 进阶技巧](#10-实战踩坑经验--进阶技巧)

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

## 10. 实战踩坑经验 & 进阶技巧

> 以下是投递 50+ 个职位后积累的血泪教训。每一条背后都是真实的翻车经历。

---

### 10.1 多标签页填写：必须用 Subagent

**问题：** Claude Code 有上下文窗口限制。如果你说「一起投 5 个职位」，Claude 在主线程依次填写，到第 2-3 个表单时上下文就爆了——之前填的内容被压缩遗忘，后面的表单开始出错或丢字段。

**解决方案：** 在 `CLAUDE.md` 中写明批量投递时使用 Agent tool（subagent）。每个 subagent 独立处理一个标签页，有自己的上下文窗口，互不干扰。

```
# 你这样说：
全部投递 1 3 5 7

# Claude 应该这样做：
- 为每个职位启动一个 subagent
- 每个 subagent 在新标签页独立填表
- 主线程只负责协调和汇报结果
```

**如果你发现 Claude 在主线程逐个填（没用 subagent），直接告诉它：** 「用 subagent，每个 tab 开一个 agent 去填」。

---

### 10.2 CV 上传的正确姿势

**问题：** Playwright 的 `browser_file_upload` 有时无法触发文件选择器（特别是 Workday 和 Oracle 的隐藏 input）。

**正确做法（写进 CLAUDE.md）：**

1. **先复制 CV 到项目目录**（Playwright 沙箱可能访问不到桌面路径）：
   ```bash
   cp "/Users/你/Desktop/你的简历.pdf" "/Users/你/job-apply-bot/你的简历.pdf"
   ```

2. **优先用 `browser_file_upload`**——这是标准方式。

3. **如果 upload 按钮点击后没弹出文件选择器**，用 fallback：
   ```javascript
   // Claude 会用 browser_run_code_unsafe 执行这个
   await page.locator('input[type="file"]').first().setInputFiles('/Users/你/job-apply-bot/你的简历.pdf')
   ```

4. **如果页面有多个 file input**（比如 CV + Cover Letter 分开上传），需要指定具体的 locator，不能用 `.first()`。

---

### 10.3 Workday 表单的特殊处理

Workday 是最常见的申请系统，也是坑最多的。

#### 学校下拉框搜不到

Workday 的学校列表不是标准的 `<select>`，而是 ReactVirtualized 虚拟滚动列表。你的大学可能搜不到。

**策略（写进 CLAUDE.md 或 MEMORY.md）：**
- 先搜大学全名 → 搜不到就搜缩写 → 还搜不到选 **"Other - School Not Found in List"**
- 选 "Other" 后通常会出现一个文本框让你手动输入校名

#### 虚拟滚动下拉框操作

Workday 的下拉选项用了 ReactVirtualized，普通的 click 可能点不到不在视口内的选项。

```javascript
// 1. 先滚动虚拟列表到目标位置
Array.from(document.querySelectorAll('div'))
  .find(el => el.className?.includes('ReactVirtualized__List'))
  .scrollTop = 500  // 调整数字直到目标出现

// 2. 然后点击 radio input（不是选项文字）
target.querySelector('input[type="radio"]')?.click()
```

#### 多步骤表单的「最后一步陷阱」

Workday 的申请通常是 5-6 步：My Information → My Experience → Application Questions → Voluntary Disclosures → Review。

**危险点：** Review 页面的 "Submit" 按钮会直接提交申请。Claude 绝不应该点这个按钮。但有些表单最后一步的 "Save & Continue" 其实就是提交。

**防御策略：** 在 CLAUDE.md 里写明——「如果当前步骤看起来是最后一步（下一步是 Review 或 Submit），先告诉我，等我确认后再继续。」

---

### 10.4 Oracle HCM (Taleo/IRC) 表单的特殊处理

Oracle 系统（DP World、Oracle 自家等用）也很常见。

#### 邮箱验证流程
Oracle HCM 通常需要邮箱验证才能开始申请。Claude 应该：
1. 填入邮箱 → 点击发送验证码
2. 自动运行 `uv run python email_code.py --wait --sender oracle`
3. 读到验证码后自动填入

#### Resume Import 会覆盖已填字段
Oracle 的 "Import Resume" 功能会解析你的 CV 并预填某些字段——但解析结果经常是错的（比如把 LinkedIn URL 填成 `https://LinkedIn`，把地址弄丢）。

**最佳实践：** 先上传 CV，再逐一检查和覆盖被错误填入的字段。

#### Preferred Location 等 Combobox
Oracle 的 location 选择器不是标准 `<select>`，用 `fill_form` 会报错。正确做法是用 `browser_type` 输入关键词（如 "Dublin"），等下拉选项出现后用 `browser_click` 点击。

---

### 10.5 Cover Letter 自动生成

有些申请需要 Cover Letter。让 Claude 自动生成 Word 文档：

**写进 CLAUDE.md 的规则：**
```
当表单要求上传 Cover Letter 时：
1. 用 python-docx 生成一份 .docx 文件
2. 保存到项目目录：/Users/你/job-apply-bot/CoverLetter_公司名_职位.docx
3. 上传到表单
```

Claude 会这样执行：
```python
python3 -c "
from docx import Document
doc = Document()
doc.add_paragraph('Dear Hiring Manager,')
doc.add_paragraph('正文...')
doc.add_paragraph('Yours sincerely,')
doc.add_paragraph('你的名字')
doc.save('/Users/你/job-apply-bot/CoverLetter_Accenture_GradProgramme.docx')
"
```

需要先安装：`uv add python-docx`

---

### 10.6 上下文管理——Claude 最大的瓶颈

Claude Code 的上下文窗口是有限的。每次 `browser_snapshot` 会消耗大量 token。一个复杂的 Workday 6 步表单很容易用完整个窗口。

**实用策略：**

| 场景 | 做法 |
|------|------|
| 填单个简单表单 | 主线程直接填，不需要 subagent |
| 填单个复杂表单（Workday 6 步） | 主线程填，但 Claude 可能在第 4-5 步开始「忘记」之前的信息。如果出现重复填写或遗漏，提醒 Claude 看 profile.json |
| 批量填 2+ 个表单 | **必须用 subagent**，每个表单一个 agent |
| Claude 明显开始「糊涂」了 | 说「读一下 profile.json 刷新记忆」，或者开一个新对话 |

**写进 CLAUDE.md：**
```
当你感觉上下文快满了（比如 snapshot 返回的内容开始被截断），主动告诉用户，
建议开新对话继续剩余的表单。
```

---

### 10.7 MEMORY.md——Claude 的跨对话记忆

Claude Code 有一个 auto-memory 目录（`~/.claude/projects/<project>/memory/`），里面的 `MEMORY.md` 每次对话都会自动加载前 200 行。

**这意味着什么：**
- 你在 MEMORY.md 里写的踩坑经验，Claude 下次对话时还能看到
- 如果你发现某个申请系统有特殊操作（比如 Workday 学校搜索策略），告诉 Claude「记住这个」，它会写入 MEMORY.md
- 你也可以直接编辑这个文件

**推荐写入 MEMORY.md 的内容：**
- 特定申请系统的操作技巧（Workday、Oracle、Greenhouse、Lever 等）
- 你的学校在各系统下拉框中的准确名称
- 每次填表后发现的新问题和解决方法
- 投递统计数据（多少个投了、多少个回复了）

---

### 10.8 LinkedIn 浏览器补充抓取

JobSpy 通过 API 抓取 LinkedIn，经常被反爬限制，漏掉大量职位。项目内置了一个**双通道策略**：

1. **discover.py（JobSpy）** — 批量抓取，覆盖 Indeed + LinkedIn，速度快但可能漏
2. **Playwright 浏览器直接刷 LinkedIn** — 用真实浏览器打开 LinkedIn Jobs 页面，像你手动浏览一样读取职位列表

**工作原理：**
- discover.py 跑完后，Claude 会自动打开 LinkedIn Jobs 搜索页
- 按你配置的关键词搜索，筛选「最近 24 小时」+「Entry level / Internship」
- 滚动 1-2 页，提取每条职位的标题、公司、地点、链接
- 跟 jobs.json 去重后追加新发现的职位
- 重新跑 evaluate.py 更新评分

**前提条件：**
- 你需要在 Playwright 浏览器中**至少手动登录一次 LinkedIn**（Claude 打开 LinkedIn 后你登录，session 会保留）
- 之后每次抓取都会复用这个 session，不需要重新登录

**手动触发：**
```
你：刷LinkedIn
你：scrape LinkedIn
你：补充抓取
```

**自定义搜索词：** 在 `CLAUDE.md` 的 "LinkedIn Browser Scraping" 章节中修改搜索关键词和 URL 模板。

---

### 10.9 常见报错 & 修复

#### Q: 运行 discover.py 报错 "No module named 'jobspy'"
```bash
uv sync   # 重新安装依赖
```

#### Q: Claude 说 "Playwright MCP not found"
```bash
claude mcp add playwright -- npx @playwright/mcp@latest
# 然后重启 Claude Code
```

#### Q: 浏览器打不开 / 超时
确保 Node.js 已安装且版本 >= 18：
```bash
node --version
npx @playwright/mcp@latest   # 首次运行会自动安装浏览器
```

#### Q: CV 上传失败
确保 `cv_path` 是**绝对路径**（以 `/` 开头），文件确实存在：
```bash
ls -la "/Users/你的用户名/Desktop/你的简历.pdf"
```

#### Q: 搜到的职位太少 / 太多不相关
- 太少 → 增大 `HOURS`（比如 720 = 30天），增大 `RESULTS`，增加 `SEARCHES` 关键词
- 太多不相关 → 在 `OFF_TOPIC_TITLE_KEYWORDS` 中加入你不想看到的职位关键词
- 评分不准 → 调整 `FIT_POSITIVE` 和 `FIT_NEGATIVE` 的关键词和权重

#### Q: Claude 填错了某个字段怎么办
表单还没提交之前，你可以：
1. 直接在浏览器里手动修改
2. 告诉 Claude 哪里错了，它会帮你改

#### Q: 我不是在爱尔兰，怎么改
1. `profile.json` → 改 `personal.country`、`work_permit`
2. `discover.py` → 改所有 `location` 字段，以及 `country_indeed` 参数
3. `evaluate.py` → 修改/删除 `is_uk` 函数和 `UK_LOCATIONS` 列表
4. `CLAUDE.md` → 修改 "Flags to Raise" 中的地区规则

#### Q: profile.json 里的密码安全吗
`profile.json` 在 `.gitignore` 中，不会被 Git 追踪。但请注意：
- 不要手动把它上传到任何地方
- 如果 fork 了这个项目，确保 `.gitignore` 包含 `profile.json`
- Gmail App Password 可以随时在 Google Account 中撤销

---

### 10.10 推荐的 Claude Code 设置

在 Claude Code 里输入以下命令获得最佳体验：

```
/model opus              # 用最强模型——填表准确率明显更高
/permissions             # 选 bypassPermissions——免得每个操作都要确认
```

也可以在 `~/.claude/settings.json` 中直接配置：
```json
{
  "permissions": {
    "defaultMode": "bypassPermissions"
  },
  "model": "opus",
  "skipDangerousModePermissionPrompt": true
}
```

---

### 10.11 投递效率最大化——工作流建议

根据 50+ 次投递的经验，最高效的工作流是：

1. **每天/每周跑一次 discover + evaluate**
   ```
   你：搜索职位
   ```

2. **从评分最高的开始投**——高分意味着匹配度高，值得优先投

3. **一次选 3-5 个批量投递**
   ```
   你：全部投递 1 2 3 4 5
   ```

4. **填完后逐一检查再 Submit**——Claude 填的 95% 是对的，但偶尔会有小错误（日期格式、电话号码多了国家码等）

5. **常见的 Claude 小错误（你检查时注意）：**
   - 电话号码：可能把 country code 和号码连在一起（如 `+353870015190` 应该分开填）
   - 日期格式：有些系统要 DD/MM/YYYY，有些要 MM/DD/YYYY，Claude 偶尔会搞混
   - 下拉框：如果选项列表很长，Claude 可能选了一个相近但不完全正确的选项
   - 自动导入的字段：Resume Import 后某些字段可能被覆盖成错误值

6. **定期更新 company_list.md**——打勾已投的公司，添加新发现的公司

7. **跟踪回复率**——如果投了 30+ 个还没有回复，可能需要：
   - 改进 CV（让有经验的人看看）
   - 扩大搜索范围（更多关键词、更多地区）
   - 针对性写 Cover Letter（而不是通用的）

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
