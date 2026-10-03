# Job Apply Bot 🤖

Automatically fill job application forms using Claude Code + Playwright.

Just paste a URL → Claude reads your profile → fills the entire form → you click Submit.

---

## How It Works

1. Claude reads your `profile.json` (personal info, education, work experience)
2. You paste a job application URL
3. Claude opens the browser, reads the form, and fills everything automatically
4. You review and click Submit

---

## Setup (One-time)

### 1. Prerequisites

- [Claude Code](https://claude.ai/code) installed and authenticated
- Node.js installed

### 2. Clone the repo

```bash
git clone https://github.com/YOUR_USERNAME/job-apply-bot.git
cd job-apply-bot
```

### 3. Add Playwright MCP

```bash
claude mcp add playwright npx @playwright/mcp@latest
```

Verify it's connected:
```bash
claude mcp list
```

### 4. Set up your profile

```bash
chmod +x setup.sh
./setup.sh
```

This copies `profile.template.json` → `profile.json` and opens it for editing.

Fill in your details:
- Personal info (name, email, phone, address)
- Education (undergraduate + postgraduate)
- Work experience
- Skills
- CV file path: `"cv_path": "/absolute/path/to/your/CV.pdf"`

> ⚠️ `profile.json` is in `.gitignore` — your personal data will never be pushed to GitHub.

---

## Usage

```bash
cd job-apply-bot
claude
```

Then just paste a job application URL:

```
https://company.com/apply/job-123
```

Claude will:
- Detect if it's a Graduate Programme or Internship
- Fill all fields from your profile
- Upload your CV
- Write open-text answers (motivation, skills, achievements) based on your experience
- Flag anything that needs your input (e.g. UK jobs if you only have Irish work rights)

When done, Claude shows a summary. **You** click Submit.

---

## Supported Form Types

- Pinpoint (Accenture, etc.)
- Greenhouse / Toast Careers
- Workable
- Most standard HTML forms

---

## Updating Your Profile

If a form asks something not in your profile, Claude will ask you. After you answer, it updates `profile.json` automatically — so you're never asked the same question twice.

---

## Tracking Applications

Claude automatically records every completed application in `applied_companies.json`:

```json
[
  {
    "company": "HPE",
    "role": "Software Engineer Intern",
    "location": "Galway, Ireland",
    "url": "https://...",
    "date_applied": "2026-10-03",
    "status": "submitted"
  }
]
```

- `applied_companies.json` is in `.gitignore` — stays on your machine only
- A blank template (`applied_companies.template.json`) is committed to the repo
- After filling a form, Claude records the application automatically unless you say "don't record this"
- If you give Claude a URL it has already applied to, it will warn you

---

## Privacy

- `profile.json` is gitignored — stays on your machine only
- Your CV is uploaded directly from your machine to the employer's server
- Claude (Anthropic) processes the text of your profile to fill forms

---

## Troubleshooting

**Playwright not connecting:**
```bash
claude mcp list  # should show playwright as Connected
claude mcp add playwright npx @playwright/mcp@latest  # re-add if needed
```

**Form not filling correctly:**
Run `claude` fresh in a new session for each application — don't reuse long sessions.
