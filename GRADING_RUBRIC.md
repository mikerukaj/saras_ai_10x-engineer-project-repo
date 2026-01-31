# PromptLab: Grading Rubric

## Total Score: 100 Points

| Week | Focus | Weight |
|------|-------|--------|
| 1 | Backend Foundation | 25% |
| 2 | Documentation & Specs | 25% |
| 3 | Testing & DevOps | 25% |
| 4 | Full-Stack Integration | 25% |

### Grading Scheme

| Grade | Requirement |
|-------|-------------|
| **Satisfactory (S)** | Total score ≥ 70% |
| **Unsatisfactory (U)** | Total score < 70% |

---

## Week 1: Backend Foundation (25 Points)

### Deliverables
- [ ] All 4 bugs fixed and working
- [ ] PATCH endpoint implemented for partial updates
- [ ] All provided tests pass
- [ ] Code committed with meaningful commit messages

### Criteria

| Criterion | Points | Description |
|-----------|--------|-------------|
| **Bug Fixes** | 14 | All bugs fixed (GET 404, PUT timestamp, Sorting, Deletion) |
| **New Feature** | 8 | PATCH endpoint implemented correctly with partial updates |
| **Code Quality** | 3 | Tests pass and clean commit history |

---

## Week 2: Documentation & Specifications (25 Points)

### Deliverables
- [ ] Comprehensive `README.md` with project overview, setup, and usage
- [ ] Google-style docstrings on all functions in `models.py`, `api.py`, `storage.py`, `utils.py`
- [ ] `docs/API_REFERENCE.md` with full endpoint documentation
- [ ] `.github/copilot-instructions.md` or `.continuerules` for custom AI agent
- [ ] `specs/prompt-versions.md` feature specification
- [ ] `specs/tagging-system.md` feature specification

### Criteria

| Criterion | Points | Description |
|-----------|--------|-------------|
| **Docstrings & API Docs** | 12 | Comprehensive documentation for code and API |
| **README.md** | 5 | Professional, clear setup and usage guide |
| **Feature Specifications** | 5 | Detailed specs for 2 new features |
| **Custom AI Agent** | 3 | Instructions file created for AI coding standards |

---

## Week 3: Testing & DevOps (25 Points)

### Deliverables
- [ ] Comprehensive test suite with ≥80% code coverage
- [ ] One new feature implemented (Prompt Versions OR Tagging System) using TDD
- [ ] `.github/workflows/ci.yml` GitHub Actions pipeline
- [ ] `backend/Dockerfile` for containerization
- [ ] `docker-compose.yml` for local development
- [ ] Code refactored for quality improvements

### Criteria

| Criterion | Points | Description |
|-----------|--------|-------------|
| **Test Suite** | 10 | Coverage ≥ 80%, meaningful tests, edge cases |
| **Feature Implementation** | 8 | Feature works and used TDD approach |
| **DevOps Setup** | 7 | CI/CD pipeline and Docker configuration working |

---

## Week 4: Full-Stack Integration (25 Points)

### Deliverables
- [ ] React frontend scaffolded with Vite
- [ ] Prompt list/grid displaying all prompts
- [ ] Create, edit, delete prompt functionality
- [ ] Collections management UI
- [ ] Frontend connected to backend API
- [ ] Loading states, error handling, and empty states
- [ ] Responsive design that works on mobile

### Criteria

| Criterion | Points | Description |
|-----------|--------|-------------|
| **Core Components** | 10 | List, Form, and Collections UI implemented |
| **API Integration** | 8 | Full CRUD operations connected to backend |
| **UX Polish** | 5 | Loading states, error handling, responsiveness |
| **Setup & Structure** | 2 | Clean project structure and correct setup |

---

## Grading Scale

| Grade | Score | Description |
|-------|-------|-------------|
| **Satisfactory (S)** | ≥ 70 | Meets requirements, demonstrates competency |
| **Unsatisfactory (U)** | < 70 | Does not meet minimum requirements |

> **Note:** You need at least 70 points (70%) to pass the project.

---

## Automatic Deductions

| Issue | Deduction |
|-------|-----------|
| Tests don't pass | -5 points |
| Application doesn't run | -10 points |
| Missing week deliverable | -25 points (full week) |
| Plagiarism detected | -100 points |
| Late submission (per day) | -5 points |

---

## Bonus Points (Up to 10 extra)

| Bonus | Points | Description |
|-------|--------|-------------|
| Exceptional UI design | +3 | Goes beyond basic functionality |
| Extra features | +3 | Implemented both specs in Week 3 |
| 95%+ test coverage | +2 | Exceptional testing |
| Deployment | +2 | Actually deployed and accessible |

---

## Submission Requirements

Each week, submit:
1. GitHub repository link
2. Brief summary of what you completed
3. Any notes or known issues

**Repository must include:**
- All source code
- Working README with setup instructions
- Passing tests (where applicable)

---

## Questions?

Reach out to your instructor or post in the course forum.

Good luck! 🚀
