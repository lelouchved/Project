# Mirai Clubs Governance & Activities Tracking Platform
### College Challenge Submission — Problem Statement 3

A production-ready, mobile-first Web Application & PWA built for **Mirai School of Technology (MSOT)** across its **3 official campuses** (*HIET, RIT, and JU*). The platform digitizes the entire Saturday Club Day lifecycle from membership enrolment, activity planning, anti-proxy dynamic QR check-ins, assignment submissions, 3-part rubric evaluations, and budget approvals, to tamper-evident digital certificates, YouTube video integration, and social media showcase streams.

---

## 🌟 Key Highlights & Architectural Features

1. **Mirai Institutional Campus & Club Hierarchy:**
   - **Strictly 3 Campuses:**
     1. **HIET** (Hi Tech Institute of Engineering) — Main technology and activities campus.
     2. **RIT** (Rathinam Institute) — Research and inter-college symposium partner.
     3. **JU** (Jagannath University) — Entrepreneurship, incubation, and venture accelerator.
   - **HIET 4 Active Clubs:**
     1. **Nextcell Club** (Technical & AI)
     2. **Kaizen Club** (Continuous Innovation & Design)
     3. **Malhar Club** (Cultural & Arts)
     4. **Sports Club** (Athletics & Esports)
   - **Gated Access Policy:** Public/guest visitors view high-level summaries, public events, YouTube showcases, and social posts. Deep club operations (rosters, live QR attendance, submissions, budgets) require user sign-in or registration.

2. **Left Vertical Sidebar Navigation:**
   - Sleek, modern Left Sidebar layout with quick navigation, role indicator, theme switch, fast demo switcher, and responsive drawer on mobile devices.

3. **3D Cursor Animation & Three.js Background:**
   - Dual-element custom cursor with high-luminosity frost dot and fluid magnetic outer ring with inertia lag.
   - Real-time stardust particle emitter trailing mouse movement.
   - Interactive Three.js particle constellation and rotating celestial geometry responding to cursor parallax.

4. **Coolors Palette for Dark Mode & Mirror Effect Buttons:**
   - **Coolors Palette:** `#5465FF`, `#788BFF`, `#9BB1FF`, `#BFD7FF`, `#E2FDFF` blended over absolute black `#000000`.
   - **Mirror Effect Buttons (90% Transparency):** Glassmorphic styling with high backdrop blur, specular top reflection rim, and animated light streak sweep on hover.

5. **Mirai Media Stream (YouTube & Social Media):**
   - Embedded interactive YouTube video showcase of 24h Hackathons and Club Day auditions.
   - Social media feed cards from Google Campus Reviews (4.9★), Instagram (`@mirai.tech.clubs`), and GitHub developer repositories.

6. **Domain Expansion Passkey (Secret):**
   - The registration modal takes an optional "Domain Expansion Code" **silently without revealing the passkey to anyone**.
   - Inputting `"Yuzuru"` grants supreme domain authority to reassign club officer positions (President, VP, Finance, Media, Member), override attendance, and manage all campus clubs.

7. **OTP Delivery & Verification:**
   - 6-digit verification code sent/simulated to user's provided email or phone number for both registration and login.

8. **1-Click OAuth / Social Login:**
   - Direct buttons for **Continue with Google**, **Continue with Instagram**, and **Continue with GitHub**.

9. **Strict Institutional Enrolment & Capacity Rules:**
   - Enforces a hard institutional limit: **Students can join up to 2 clubs maximum**.
   - Club recruitment capacity: **50–70 members** with countdown banners.

10. **Anti-Proxy Dynamic QR Attendance (TOTP):**
    - Live projector screen generates a dynamic QR code that rotates every **20 seconds**. Screenshots expire immediately.
    - Manual overrides require a **mandatory written audit reason** logged in `AuditLog`.

11. **Standardized 3-Part Rubric Evaluation:**
    - Graded on a 30-point scale:
      - Content Quality & Technical Rigor (0–10)
      - Presentation & Communication (0–10)
      - Teamwork & Q&A Participation (0–10)

12. **100% Free & Zero Financial Investment ($0 Cost):**
    - Built entirely on Python 3.9, FastAPI, and local SQLite with WAL mode.
    - Zero paid cloud databases or third-party paid subscriptions.

---

## 🚀 One-Command Quickstart

To run the entire platform locally on your Mac:

```bash
# 1. Clone repository and navigate to folder
cd "most clubs"

# 2. Run the one-command launcher
./run.sh
```

The script will automatically:
- Create the local Python virtual environment (`venv`).
- Install all dependencies (`fastapi`, `uvicorn`, `sqlalchemy`, `pyotp`, `qrcode`, `reportlab`, `pytest`, `httpx`).
- Seed realistic data across the 3 campuses and HIET's 4 clubs.
- Launch the server at **`http://localhost:8000`**.

---

## 👥 Built-In Quick Persona Switcher

When opening `http://localhost:8000`, the Left Sidebar includes a fast demo switcher:
- **👑 Dr. Alok Verma (Admin / Authority)** — Oversees all 3 campuses, assigns club posts.
- **🏛️ Prof. Sunita Rao (Campus Manager)** — Approves scale-based budget proposals, exports academic CSV.
- **👨‍🏫 Dr. Rajiv Menon (Faculty Advisor)** — Nextcell Club Advisor, grades deliverables.
- **⭐ Aarav Sharma (Nextcell President)** — Projects dynamic rotating QR codes.
- **💰 Priya Patel (Nextcell Finance President)** — Submits budget requests.
- **🎨 Tanvi Mehta (Kaizen President)** — Manages Kaizen innovation sprints.
- **🎓 Student Candidate 1 (Club Member)** — Enrolled in Nextcell & Kaizen, downloads transcript.

---

## 🧪 Comprehensive Test Report (29 / 29 Passing — 100% Pass Rate)

> [!NOTE]
> For the complete itemized test execution evidence, audit logs, and load test benchmarks, see [TEST_REPORT.md](TEST_REPORT.md).

Run all automated tests:
```bash
PYTHONPATH=. ./venv/bin/pytest tests/ -v
```

| Test Suite | Purpose & Verification Focus | Test Cases | Result |
| :--- | :--- | :---: | :---: |
| **`test_bifurcation_flow.py`** | Multi-step role questionnaire, advisor governance & Kaizen 4 branches | 4 Tests | ✅ **PASSED** |
| **`test_calendar_authority.py`** | Public read, Domain Authority gating & push to personal calendars | 4 Tests | ✅ **PASSED** |
| **`test_lifecycle.py`** | 2-club limit, 20s dynamic QR TOTP, rubric grading & tamper-evident certificates | 8 Tests | ✅ **PASSED** |
| **`test_personal_work_history.py`**| Privacy isolation & category filters across personal student portfolios | 3 Tests | ✅ **PASSED** |
| **`test_analytics_and_championship.py`**| Inter-campus championship coalition & advisor hackathon audit gating | 3 Tests | ✅ **PASSED** |
| **`test_settings_and_permissions.py`** | Custom avatar photo uploads & presidential club logo updates | 3 Tests | ✅ **PASSED** |
| **`test_social_login.py`** | 1-click Google, Instagram & GitHub OAuth authentication | 4 Tests | ✅ **PASSED** |
| **Total** | **Complete Full-Platform Automated Regression Suite** | **29 Tests** | ✅ **100% PASSED** |

### 500 Concurrent Check-Ins Load Benchmark:
Run benchmark:
```bash
PYTHONPATH=. ./venv/bin/python tests/load_test_500.py
```
- **100 Concurrent:** p95 = `81.34 ms` (`0.00%` errors)
- **300 Concurrent:** p95 = `72.70 ms` (`0.00%` errors)
- **500 Concurrent:** p95 = `66.67 ms` (`0.00%` errors) — **Exceeds target of < 1,000 ms by 15x!**

---

## 🔀 Multi-Step Role Bifurcation ("Tick The Correct") Architecture

Upon registration or when selecting **Bifurcation Flow**, users complete a structured multi-step institutional questionnaire:
1. **Step 1: Affiliation**
   - **No, NOT part of Mirai:** Routed to **Public Guest Portal** (`home-non-mirai`) featuring admissions showcases, YouTube live streams, and application inquiries.
   - **Yes, I AM part of Mirai:** Proceeds to Step 2.
2. **Step 2: Institutional Standing**
   - **Teacher / Faculty (Case 1):** Proceeds to Teacher Bifurcation.
   - **Student / Scholar (Case 2):** Proceeds to Student Bifurcation.
3. **Step 3 (Case 1 — Teachers):**
   - **Club Advisor:** Routed to **Club Advisor Governance Console** (`home-advisor`) with student leadership appointment privileges (5 posts for standard clubs / 2 posts for Kaizen), vision report review desk, and 3-pillar audit console.
   - **Normal Teacher:** Routed to **Teacher Academic Workbench** (`home-teacher`) with lecture timetable, academic circulars, and student directory.
4. **Step 3 (Case 2 — Students):**
   - **Club Member:** Routed to **Club Member & Leadership Workbench** (`home-student-member`) with 20s dynamic QR check-in, 3-part rubric submissions, and verified PDF certificates.
   - **Non-Club Member:** Routed to **Non-Club Discovery Hub** (`home-student-non-member`) with recruitment countdowns, remaining capacities, and club applications.

---

## 🎨 Visual Engine: Absolute Matte Black & Foggy Mirror Optics

- **Absolute Matte Black (`#000000`):** Pure obsidian canvas without slate/gray tinting.
- **Foggy Mirror Panels:** Frosted glass panels styled with `backdrop-filter: blur(28px)`, linear glass diffusion gradients, and specular edge rim highlights.
- **Mirai Dynamic Ambience:** Ambient isometric grid matrix, dual breathing chromatic orbs (Royal Blue `#194cd1` & Electric Cyan `#069bad`), and an ethereal cursor spotlight beam with fluid RAF lerp damping.
- **Tactile Micro-Interactions:** Micro-elevation on hover, tactile spring press on active, and circular pointer shockwave ripples on click.

---

## 📂 Project Structure

```
Project/
├── TEST_REPORT.md               # Official Verification & Test Execution Report (29/29 Passing)
├── README.md                    # Institutional Documentation & Problem Statement Architecture
├── backend/
│   ├── database.py              # SQLite WAL mode & connection pooling
│   ├── models.py                # Campus, User, Club, Budget, Attendance, Rubric, Certs, Reports
│   ├── schemas.py               # Pydantic v2 schemas + Bifurcation & Social Login models
│   ├── auth.py                  # JWT authentication, bcrypt hashing, RBAC dependencies
│   ├── seed_data.py             # Seed data for RIT, HIET, JU, and HIET clubs & leadership
│   ├── main.py                  # FastAPI entry point & static file routing
│   └── routers/
│       ├── auth_routes.py       # OTP, register, login, bifurcation flow & social auth
│       ├── club_routes.py       # Club catalog, leadership appointments & advisor reviews
│       ├── event_routes.py      # Common calendar & push-to-personal calendar
│       ├── attendance_routes.py # 20s dynamic TOTP QR code & manual override audit trail
│       ├── assignment_routes.py # Project deliverables & 3-part rubric grading (/30)
│       ├── budget_routes.py     # Scale-based budget proposals & CM reviews
│       ├── certificate_routes.py# ReportLab PDF generator & SHA-256 verification
│       └── report_routes.py     # Analytics & exportable monthly academic CSV
├── frontend/
│   ├── index.html               # 5 dedicated homepages, bifurcation modal, foggy mirror theme
│   └── verify.html              # Standalone public certificate verification portal
├── tests/
│   ├── test_bifurcation_flow.py # Role bifurcation & advisor governance test suite
│   ├── test_calendar_authority.py# Common calendar & personal calendar push tests
│   ├── test_lifecycle.py        # Core Saturday activities & anti-spoofing tests
│   ├── test_personal_work_history.py# Student portfolio privacy & category filter tests
│   ├── test_analytics_and_championship.py# Inter-campus championship & performance tests
│   ├── test_settings_and_permissions.py# Custom avatars & club logo permission tests
│   ├── test_social_login.py     # Google, Instagram, GitHub OAuth tests
│   └── load_test_500.py         # 100, 300, 500 concurrent check-in benchmark
├── uploads/                     # Storage for deliverables, receipts, certificates
├── requirements.txt             # Locked Python dependencies
├── run.sh                       # One-command quickstart script
└── vercel.json                  # Serverless deployment configuration
```
