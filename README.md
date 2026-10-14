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

## 🧪 Comprehensive Test Report (12 / 12 Passing)

Run tests:
```bash
PYTHONPATH=. ./venv/bin/pytest tests/ -v
```

| Test Case | Objective & Verification Evidence | Result |
| :--- | :--- | :---: |
| `test_01_institution_2_club_limit` | Confirms student can join up to 2 clubs; 3rd club request is rejected with HTTP 400. | ✅ PASSED |
| `test_02_dynamic_qr_checkin` | Verifies live TOTP code succeeds; expired/screenshot code fails anti-spoofing check. | ✅ PASSED |
| `test_03_attendance_manual_override` | Verifies coordinator override logs mandatory reason to immutable `AuditLog`. | ✅ PASSED |
| `test_04_deliverable_submission_rubric` | Verifies student upload and faculty evaluation across 3-part rubric (/30 points). | ✅ PASSED |
| `test_05_certificate_tamper_detection` | Generates 20 certificates; authentic hashes verify; tampered hashes fail validation. | ✅ PASSED |
| `test_06_finance_president_budget_workflow` | Submits budget proposal from Finance President and approves via Campus Manager. | ✅ PASSED |
| `test_07_monthly_academic_csv_export` | Verifies monthly CSV report matches student counts and headers. | ✅ PASSED |
| `test_08_registration_otp_and_passkey` | Tests OTP registration and elevates privileges when secret passkey 'Yuzuru' is used. | ✅ PASSED |
| `test_social_login_google` | Verifies 1-click Google OAuth simulation and token generation. | ✅ PASSED |
| `test_social_login_instagram` | Verifies 1-click Instagram authentication and token generation. | ✅ PASSED |
| `test_social_login_github` | Verifies 1-click GitHub authentication and token generation. | ✅ PASSED |
| `test_social_login_invalid_provider` | Rejects unsupported social providers with HTTP 400. | ✅ PASSED |

### 500 Concurrent Check-Ins Load Benchmark:
Run benchmark:
```bash
PYTHONPATH=. ./venv/bin/python tests/load_test_500.py
```
- **100 Concurrent:** p95 = 81.34 ms (0.00% errors)
- **300 Concurrent:** p95 = 72.70 ms (0.00% errors)
- **500 Concurrent:** p95 = 66.67 ms (0.00% errors) — **Exceeds target of < 1,000 ms by 15x!**

---

## 📂 Project Structure

```
most clubs/
├── backend/
│   ├── database.py              # SQLite WAL mode & timeout configuration
│   ├── models.py                # Campus, User, Club, Budget, Attendance, Rubric, Certs
│   ├── schemas.py               # Pydantic v2 schemas + SocialLoginRequest
│   ├── auth.py                  # JWT creation, bcrypt hashing, RBAC dependencies
│   ├── seed_data.py             # Seed data for RIT, HIET, JU and 4 HIET clubs
│   ├── main.py                  # FastAPI entry point & static file routing
│   └── routers/
│       ├── auth_routes.py       # OTP request, register, login, social-login
│       ├── club_routes.py       # Club catalog, join limits, post assignment
│       ├── event_routes.py      # Multi-tier calendar & recruitment dates
│       ├── attendance_routes.py # 20s dynamic TOTP QR code & manual overrides
│       ├── assignment_routes.py # Projects & 3-part rubric grading (/30)
│       ├── budget_routes.py     # Scale-based budget proposals & CM reviews
│       ├── certificate_routes.py# ReportLab PDF generator & SHA-256 verification
│       └── report_routes.py     # Analytics & exportable monthly academic CSV
├── frontend/
│   ├── index.html               # 3D canvas, left sidebar, mirror buttons, YouTube/social stream
│   └── verify.html              # Standalone public certificate verification portal
├── tests/
│   ├── test_lifecycle.py        # Automated test suite for all qualification areas
│   ├── test_social_login.py     # Tests for Google, Instagram, GitHub auth
│   └── load_test_500.py         # 100, 300, 500 concurrent check-in benchmark
├── uploads/                     # Storage for deliverables, receipts, certificates
├── requirements.txt             # Locked Python dependencies
├── run.sh                       # One-command quickstart script
└── README.md                    # Complete documentation & test report
```
