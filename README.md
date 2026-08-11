# PromptLab

**Your AI Prompt Engineering Platform**

---

### What is PromptLab?

PromptLab is an internal tool for AI engineers to **store, organize, and manage their prompts**. Think of it as a "Postman for Prompts" — a professional workspace where teams can:

- 📝 Store prompt templates with variables (`{{input}}`, `{{context}}`)
- 📁 Organize prompts into collections
- 🏷️ Tag and search prompts
- 📜 Track version history
- 🧪 Test prompts with sample inputs

### The Current Situation

The previous developer left us with a *partially working* backend. The core structure is there, but:

- The **documentation is a work in progress**
- There are **no tests** worth mentioning
- **No CI/CD pipeline** exists
- **No frontend** has been built yet
---

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+ (for Week 4)
- Git

### Run Locally

```bash
# Clone the repo
git clone <your-repo-url>
cd <repo-name>

# Set up backend
cd backend
python3 -m venv .testenv
source .testenv/bin/activate
pip install -r requirements.txt
python main.py
```

API runs at: http://localhost:8000

API docs at: http://localhost:8000/docs

### Run Tests

```bash
cd backend
pytest tests/ -v
```

---


