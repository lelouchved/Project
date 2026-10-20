import os
import datetime
import uuid
from backend.database import engine, Base, SessionLocal
from backend.models import (
    Campus, User, Club, ClubMembership, ClubBudget, Event,
    AttendanceSession, AttendanceRecord, AssignmentProject, Submission, Evaluation, Certificate, AuditLog,
    ClubPresidentReport
)
from backend.auth import hash_password
from backend.routers.certificate_routes import generate_verification_hash, create_certificate_pdf

def seed_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # Check if already seeded
    if db.query(Campus).count() > 0:
        print("Database already seeded. Skipping.")
        db.close()
        return

    print("Seeding Mirai Clubs Governance & Activities Tracker database...")

    # 1. Mirai Campuses (Strictly 3 Campuses: HIET, RIT, JU)
    c_hiet = Campus(name="Hi Tech Institute of Engineering", code="HIET")
    c_rit = Campus(name="Rathinam Institute", code="RIT")
    c_ju = Campus(name="Jagannath University", code="JU")
    db.add_all([c_hiet, c_rit, c_ju])
    db.commit()

    # 2. Staff & Faculty Users
    pwd = hash_password("password123")

    admin = User(username="admin_alok", phone="+91 98000 00001", name="Dr. Alok Verma", email="admin@msot.org", role="ADMIN", is_domain_authorized=True, campus_id=c_hiet.id, password_hash=pwd)
    cm_hiet = User(username="cm_sunita", phone="+91 98000 00002", name="Prof. Sunita Rao", email="cm.hiet@msot.org", role="CAMPUS_MANAGER", is_domain_authorized=True, campus_id=c_hiet.id, password_hash=pwd)
    
    advisor_tech = User(username="advisor_menon", phone="+91 98000 00003", name="Dr. Rajiv Menon", email="advisor.tech@msot.org", role="FACULTY_ADVISOR", is_domain_authorized=True, campus_id=c_hiet.id, password_hash=pwd)
    advisor_design = User(username="advisor_sen", phone="+91 98000 00004", name="Prof. Ananya Sen", email="advisor.design@msot.org", role="FACULTY_ADVISOR", is_domain_authorized=True, campus_id=c_hiet.id, password_hash=pwd)
    advisor_lit = User(username="advisor_joshi", phone="+91 98000 00005", name="Dr. Vikram Joshi", email="advisor.lit@msot.org", role="FACULTY_ADVISOR", is_domain_authorized=True, campus_id=c_hiet.id, password_hash=pwd)
    advisor_sports = User(username="advisor_pillai", phone="+91 98000 00006", name="Coach Rajesh Pillai", email="advisor.sports@msot.org", role="FACULTY_ADVISOR", is_domain_authorized=True, campus_id=c_hiet.id, password_hash=pwd)
    
    db.add_all([admin, cm_hiet, advisor_tech, advisor_design, advisor_lit, advisor_sports])
    db.commit()

    # 3. Student Leaders & General Students
    aarav_pres = User(username="aarav_lead", phone="+91 98111 22331", name="Aarav Sharma", email="aarav.pres@msot.org", roll_no="MSOT24CS01", role="STUDENT", is_domain_authorized=True, campus_id=c_hiet.id, password_hash=pwd)
    rohan_vp = User(username="rohan_vp", phone="+91 98111 22332", name="Rohan Gupta", email="rohan.vp@msot.org", roll_no="MSOT24CS02", role="STUDENT", is_domain_authorized=False, campus_id=c_hiet.id, password_hash=pwd)
    priya_fin = User(username="priya_fin", phone="+91 98111 22333", name="Priya Patel", email="priya.fin@msot.org", roll_no="MSOT24CS03", role="STUDENT", is_domain_authorized=False, campus_id=c_hiet.id, password_hash=pwd)
    neha_media = User(username="neha_media", phone="+91 98111 22334", name="Neha Singh", email="neha.media@msot.org", roll_no="MSOT24CS04", role="STUDENT", is_domain_authorized=False, campus_id=c_hiet.id, password_hash=pwd)

    tanvi_pres = User(username="tanvi_lead", phone="+91 98111 22335", name="Tanvi Mehta", email="tanvi.pres@msot.org", roll_no="MSOT24DS01", role="STUDENT", is_domain_authorized=True, campus_id=c_hiet.id, password_hash=pwd)
    karan_fin = User(username="karan_fin", phone="+91 98111 22336", name="Karan Verma", email="karan.fin@msot.org", roll_no="MSOT24DS02", role="STUDENT", is_domain_authorized=False, campus_id=c_hiet.id, password_hash=pwd)

    aditi_pres = User(username="aditi_lead", phone="+91 98111 22337", name="Aditi Roy", email="aditi.pres@msot.org", roll_no="MSOT24IT01", role="STUDENT", is_domain_authorized=True, campus_id=c_hiet.id, password_hash=pwd)
    kabir_pres = User(username="kabir_lead", phone="+91 98111 22338", name="Kabir Khan", email="kabir.pres@msot.org", roll_no="MSOT24SP01", role="STUDENT", is_domain_authorized=True, campus_id=c_hiet.id, password_hash=pwd)

    # General Students
    gen_students = []
    for i in range(1, 11):
        s = User(
            username=f"student_{i}",
            phone=f"+91 98222 100{i:02d}",
            name=f"Student Candidate {i}",
            email=f"student{i}@msot.org",
            roll_no=f"MSOT24UG{10+i:02d}",
            role="STUDENT",
            is_domain_authorized=False,
            campus_id=c_hiet.id,
            password_hash=pwd
        )
        gen_students.append(s)

    db.add_all([aarav_pres, rohan_vp, priya_fin, neha_media, tanvi_pres, karan_fin, aditi_pres, kabir_pres] + gen_students)
    db.commit()

    # 4. Create Clubs - Strictly 4 Clubs in HIET (Nextcell, Kaizen, Malhar, Sports Club)
    club_nextcell = Club(
        name="Nextcell Club",
        category="Entrepreneurship & E-Cell",
        description="The flagship student entrepreneurship cell (E-Cell) and startup incubation society of Mirai HIET. Empowering student founders to build commercial MVPs, pitch to angel investors, secure seed venture capital, and scale innovative tech startups.",
        campus_id=c_hiet.id,
        faculty_advisor_id=advisor_tech.id,
        capacity=65,
        is_recruiting=True,
        recruitment_deadline=datetime.datetime.utcnow() + datetime.timedelta(days=7),
        meeting_rules="Every Saturday 10:00 AM - 1:00 PM, Venture & Incubation Lab"
    )

    club_kaizen = Club(
        name="Kaizen Club",
        category="Continuous Innovation & Design",
        description="Creating intuitive product interfaces, design systems, rapid prototyping, and engineering continuous improvement.",
        campus_id=c_hiet.id,
        faculty_advisor_id=advisor_design.id,
        capacity=55,
        is_recruiting=True,
        recruitment_deadline=datetime.datetime.utcnow() + datetime.timedelta(days=10),
        meeting_rules="Every Saturday 11:00 AM - 1:30 PM, Media Studio 2"
    )

    club_malhar = Club(
        name="Malhar Club",
        category="Cultural & Arts",
        description="Fostering expressive music, dance, theater, student publications, and creative arts reflecting Mirai vibrant spirit.",
        campus_id=c_hiet.id,
        faculty_advisor_id=advisor_lit.id,
        capacity=50,
        is_recruiting=False, # Recruitment closed to demonstrate countdown/status badge
        recruitment_deadline=datetime.datetime.utcnow() - datetime.timedelta(days=2),
        meeting_rules="Every Saturday 2:00 PM - 4:00 PM, Seminar Hall A"
    )

    club_sports = Club(
        name="Sports Club",
        category="Athletics & Esports",
        description="Organizing inter-college athletics, competitive gaming leagues, physical fitness bootcamps, and tournament cups.",
        campus_id=c_hiet.id,
        faculty_advisor_id=advisor_sports.id,
        capacity=60,
        is_recruiting=True,
        recruitment_deadline=datetime.datetime.utcnow() + datetime.timedelta(days=12),
        meeting_rules="Every Saturday 4:00 PM - 6:00 PM, Sports Complex & Arena"
    )

    db.add_all([club_nextcell, club_kaizen, club_malhar, club_sports])
    db.commit()

    # 5. Memberships (Stock Web State - All posts vacant until appointed by Domain Keyholder)
    m_nextcell = [
        ClubMembership(user_id=aarav_pres.id, club_id=club_nextcell.id, post="MEMBER", status="ACTIVE"),
        ClubMembership(user_id=rohan_vp.id, club_id=club_nextcell.id, post="MEMBER", status="ACTIVE"),
        ClubMembership(user_id=priya_fin.id, club_id=club_nextcell.id, post="MEMBER", status="ACTIVE"),
        ClubMembership(user_id=neha_media.id, club_id=club_nextcell.id, post="MEMBER", status="ACTIVE"),
        ClubMembership(user_id=gen_students[0].id, club_id=club_nextcell.id, post="MEMBER", status="ACTIVE"),
        ClubMembership(user_id=gen_students[1].id, club_id=club_nextcell.id, post="MEMBER", status="ACTIVE"),
        ClubMembership(user_id=gen_students[2].id, club_id=club_nextcell.id, post="MEMBER", status="ACTIVE"),
    ]

    m_kaizen = [
        ClubMembership(user_id=tanvi_pres.id, club_id=club_kaizen.id, post="MEMBER", status="ACTIVE"),
        ClubMembership(user_id=karan_fin.id, club_id=club_kaizen.id, post="MEMBER", status="ACTIVE"),
        ClubMembership(user_id=gen_students[0].id, club_id=club_kaizen.id, post="MEMBER", status="ACTIVE"),
        ClubMembership(user_id=gen_students[3].id, club_id=club_kaizen.id, post="MEMBER", status="ACTIVE"),
    ]

    m_malhar = [
        ClubMembership(user_id=aditi_pres.id, club_id=club_malhar.id, post="MEMBER", status="ACTIVE"),
        ClubMembership(user_id=gen_students[1].id, club_id=club_malhar.id, post="MEMBER", status="ACTIVE"),
    ]

    m_sports = [
        ClubMembership(user_id=kabir_pres.id, club_id=club_sports.id, post="MEMBER", status="ACTIVE"),
        ClubMembership(user_id=gen_students[4].id, club_id=club_sports.id, post="MEMBER", status="ACTIVE"),
    ]

    db.add_all(m_nextcell + m_kaizen + m_malhar + m_sports)
    db.commit()

    # 6. Budget Proposals from Finance Presidents
    b1 = ClubBudget(
        club_id=club_nextcell.id,
        requested_by_id=priya_fin.id,
        title="AWS & GPU Cloud Credits for Annual Mirai Hackathon",
        amount=18500.0,
        category="Event & Cloud Infrastructure",
        purpose="Hosting 50 student participant model inference servers and cloud databases for the 24h hackathon.",
        scale="Flagship Event",
        status="APPROVED",
        approved_by_id=cm_hiet.id,
        admin_notes="Approved by Campus Manager. Ensure usage invoices are submitted."
    )

    b2 = ClubBudget(
        club_id=club_kaizen.id,
        requested_by_id=karan_fin.id,
        title="Prototyping Materials & Figma Organization Licenses",
        amount=9400.0,
        category="Design Tools & Supplies",
        purpose="Educational UI kit access and physical prototyping boards for Club Day workshop.",
        scale="Medium",
        status="PENDING",
        approved_by_id=None,
        admin_notes=None
    )

    b3 = ClubBudget(
        club_id=club_sports.id,
        requested_by_id=kabir_pres.id,
        title="Inter-Campus Football & Cricket Tournament Equipment",
        amount=12000.0,
        category="Equipment & Logistics",
        purpose="Procurement of official match balls, protective gear, and scoreboard electronics.",
        scale="Medium",
        status="PENDING",
        approved_by_id=None,
        admin_notes=None
    )

    db.add_all([b1, b2, b3])
    db.commit()

    # 7. Events (3-Tier Visibility)
    now = datetime.datetime.utcnow()
    # Tier 1: Public Event (Seen by Non-Club members and Guests)
    e_public = Event(
        club_id=None,
        title="Mirai Annual Inter-College Innovation Summit & Tech Expo",
        description="Public showcase of top student hardware, AI models, and entrepreneurial projects across all Mirai campuses.",
        event_type="FLAGSHIP_EVENT",
        visibility="PUBLIC",
        date=now + datetime.timedelta(days=14),
        venue="HIET Central Convention Center",
        deliverable_info="Working prototype and 5-minute poster presentation"
    )

    # Tier 2: College Student Important Date & Recruiting
    e_college_dates = Event(
        club_id=None,
        title="Fall Semester Club Auditions & Recruitment Closes",
        description="Mandatory deadline for Mirai students to confirm primary and secondary club affiliations.",
        event_type="IMPORTANT_DATE",
        visibility="CAMPUS_STUDENTS",
        date=now + datetime.timedelta(days=5),
        venue="Mirai Club Portal Online"
    )

    # Tier 3: Internal Club Day Event (Nextcell)
    e_coding_session = Event(
        club_id=club_nextcell.id,
        title="Club Day #4: AI Startup Pitch Deck & MVP Commercialization Sprint",
        description="Hands-on venture pitch validation, business model canvas, and customer discovery metrics for student startup teams.",
        event_type="CLUB_DAY",
        visibility="CLUB_ONLY",
        date=now - datetime.timedelta(hours=2),
        venue="Venture & Incubation Lab, Room 301",
        deliverable_info="Pitch Deck PDF + MVP Demo URL",
        status="IN_PROGRESS"
    )

    # Internal Workshop (Kaizen)
    e_kaizen_session = Event(
        club_id=club_kaizen.id,
        title="Design Sprint #2: Zero-to-One Product Flow & Prototyping",
        description="Hands-on Figma component library and interactive interaction design workshop.",
        event_type="WORKSHOP",
        visibility="CAMPUS_STUDENTS",
        date=now + datetime.timedelta(days=3),
        venue="Innovation Studio 2",
        deliverable_info="Figma Prototype URL"
    )

    db.add_all([e_public, e_college_dates, e_coding_session, e_kaizen_session])
    db.commit()

    # 8. Dynamic Attendance Session for Nextcell Session
    att_session = AttendanceSession(
        event_id=e_coding_session.id,
        club_id=club_nextcell.id,
        totp_secret="JBSWY3DPEHPK3PXP", # standard base32
        opens_at=now - datetime.timedelta(hours=2),
        closes_at=now + datetime.timedelta(hours=2),
        is_active=True
    )
    db.add(att_session)
    db.commit()

    # Attendance Records (Aarav, Rohan, Student 1)
    rec1 = AttendanceRecord(session_id=att_session.id, user_id=aarav_pres.id, status="PRESENT")
    rec2 = AttendanceRecord(session_id=att_session.id, user_id=rohan_vp.id, status="PRESENT")
    rec3 = AttendanceRecord(
        session_id=att_session.id, user_id=gen_students[0].id,
        status="MANUAL_OVERRIDE",
        override_reason="Phone camera lens cracked, coordinator visually confirmed presentation attendance.",
        override_by_id=aarav_pres.id
    )
    db.add_all([rec1, rec2, rec3])
    db.commit()

    # 9. Assignment & Project
    assign1 = AssignmentProject(
        club_id=club_nextcell.id,
        event_id=e_coding_session.id,
        title="High-Throughput Rate Limiter Implementation in Python",
        description="Implement token-bucket algorithm using Redis and write automated concurrency tests.",
        assignment_type="PROJECT",
        due_date=now + datetime.timedelta(days=2),
        max_score=30.0,
        created_by_id=aarav_pres.id
    )
    db.add(assign1)
    db.commit()

    # Student 1 Submission & Rubric Evaluation
    sub1 = Submission(
        assignment_id=assign1.id,
        student_id=gen_students[0].id,
        external_link="https://github.com/msot-student/rate-limiter-service",
        notes="Implemented sliding window counter with unit tests covering 500 req/sec.",
        status="EVALUATED"
    )
    db.add(sub1)
    db.commit()

    eval1 = Evaluation(
        submission_id=sub1.id,
        evaluated_by_id=advisor_tech.id,
        content_score=9.5,
        presentation_score=9.0,
        participation_score=9.0,
        total_score=27.5,
        feedback_comments="Exceptional benchmark analysis and clear concurrency handling. Recommended for publication in club newsletter.",
        evaluated_at=now
    )
    db.add(eval1)
    db.commit()

    # 10. Sample Certificates for Student 1
    cert_id = str(uuid.uuid4())
    cert_hash = generate_verification_hash(cert_id, gen_students[0].id, "Excellence in Systems Programming", now.strftime("%Y-%m-%d"))
    cert1 = Certificate(
        id=cert_id,
        certificate_number=f"MSOT-2026-CLB-{uuid.uuid4().hex[:6].upper()}",
        user_id=gen_students[0].id,
        club_id=club_nextcell.id,
        event_id=e_coding_session.id,
        cert_type="ACHIEVEMENT",
        title="Excellence in Systems Programming",
        issue_date=now,
        verification_hash=cert_hash
    )
    db.add(cert1)
    db.commit()

    # Generate physical PDF for verification testing
    try:
        pdf_path = create_certificate_pdf(
            cert=cert1,
            student_name=gen_students[0].name,
            roll_no=gen_students[0].roll_no,
            club_name=club_nextcell.name,
            campus_name=c_hiet.name
        )
        cert1.pdf_url = pdf_path
        db.commit()
    except Exception as e:
        print(f"Notice: PDF generation warning: {e}")

    ensure_bifurcation_seed_data(db)
    print("Database seeding completed successfully!")
    db.close()

def ensure_bifurcation_seed_data(db):
    """Guarantees that all 5 user bifurcation personas, 5 leadership posts, Kaizen branches, and President reports are populated."""
    pwd = hash_password("password123")
    hiet = db.query(Campus).filter(Campus.code == "HIET").first()
    campus_id = hiet.id if hiet else 1

    # 1. Non-Mirai Guest user
    guest = db.query(User).filter(User.email == "guest@visitor.com").first()
    if not guest:
        guest = User(
            username="guest_visitor",
            phone="+91 99999 00000",
            name="Pooja Sharma (Guest)",
            email="guest@visitor.com",
            role="GUEST",
            user_category="NON_MIRAI",
            is_mirai_entity=False,
            is_domain_authorized=False,
            campus_id=campus_id,
            password_hash=pwd
        )
        db.add(guest)

    # 2. Normal Teacher
    teacher_vikram = db.query(User).filter(User.email == "teacher.vikram@msot.org").first()
    if not teacher_vikram:
        teacher_vikram = User(
            username="teacher_vikram",
            phone="+91 98000 00010",
            name="Prof. Vikram Seth",
            email="teacher.vikram@msot.org",
            role="TEACHER",
            user_category="TEACHER",
            is_mirai_entity=True,
            teacher_type="NORMAL",
            is_domain_authorized=False,
            campus_id=campus_id,
            password_hash=pwd
        )
        db.add(teacher_vikram)

    # 3. Club Advisor
    advisor_tech = db.query(User).filter(User.email == "advisor.tech@msot.org").first()
    if advisor_tech:
        advisor_tech.role = "FACULTY_ADVISOR"
        advisor_tech.user_category = "FACULTY_ADVISOR"
        advisor_tech.is_mirai_entity = True
        advisor_tech.teacher_type = "ADVISOR"

    # 4. Non-Club Member Student
    student_rahul = db.query(User).filter(User.email == "student.rahul@msot.org").first()
    if not student_rahul:
        student_rahul = User(
            username="student_rahul",
            phone="+91 98111 00099",
            name="Rahul Verma",
            email="student.rahul@msot.org",
            roll_no="MSOT24NON01",
            role="STUDENT",
            user_category="STUDENT_NON_MEMBER",
            is_mirai_entity=True,
            student_type="NON_CLUB_MEMBER",
            is_domain_authorized=False,
            campus_id=campus_id,
            password_hash=pwd
        )
        db.add(student_rahul)

    # 5. General Secretary for Nextcell Club
    kavita_sec = db.query(User).filter(User.email == "kavita.sec@msot.org").first()
    if not kavita_sec:
        kavita_sec = User(
            username="kavita_sec",
            phone="+91 98111 22339",
            name="Kavita Deshmukh",
            email="kavita.sec@msot.org",
            roll_no="MSOT24CS05",
            role="STUDENT",
            user_category="STUDENT_MEMBER",
            is_mirai_entity=True,
            student_type="CLUB_MEMBER",
            is_domain_authorized=False,
            campus_id=campus_id,
            password_hash=pwd
        )
        db.add(kavita_sec)

    db.commit()

    # Assign 5 leaders to Nextcell Club
    club_nextcell = db.query(Club).filter(Club.name == "Nextcell Club").first()
    if club_nextcell:
        leaders = [
            ("aarav.pres@msot.org", "PRESIDENT"),
            ("rohan.vp@msot.org", "VICE_PRESIDENT"),
            ("priya.fin@msot.org", "FINANCE_PRESIDENT"),
            ("neha.media@msot.org", "MEDIA_PRESIDENT"),
            ("kavita.sec@msot.org", "GENERAL_SECRETARY")
        ]
        for email, post in leaders:
            u = db.query(User).filter(User.email == email).first()
            if u:
                u.user_category = "STUDENT_MEMBER"
                u.is_mirai_entity = True
                u.student_type = "CLUB_MEMBER"
                m = db.query(ClubMembership).filter(
                    ClubMembership.club_id == club_nextcell.id,
                    ClubMembership.user_id == u.id
                ).first()
                if not m:
                    m = ClubMembership(club_id=club_nextcell.id, user_id=u.id, post=post, status="ACTIVE")
                    db.add(m)
                else:
                    m.post = post
                    m.status = "ACTIVE"

    # Kaizen Club (Strictly 2 leaders: President & Vice President, with 4 specialized branches)
    club_kaizen = db.query(Club).filter(Club.name == "Kaizen Club").first()
    if club_kaizen:
        tanvi = db.query(User).filter(User.email == "tanvi.pres@msot.org").first()
        if tanvi:
            tanvi.user_category = "STUDENT_MEMBER"
            m = db.query(ClubMembership).filter(ClubMembership.club_id == club_kaizen.id, ClubMembership.user_id == tanvi.id).first()
            if m:
                m.post = "PRESIDENT"
                m.branch = "Dev Club"
            else:
                db.add(ClubMembership(club_id=club_kaizen.id, user_id=tanvi.id, post="PRESIDENT", branch="Dev Club", status="ACTIVE"))

        karan = db.query(User).filter(User.email == "karan.fin@msot.org").first()
        if karan:
            karan.user_category = "STUDENT_MEMBER"
            m = db.query(ClubMembership).filter(ClubMembership.club_id == club_kaizen.id, ClubMembership.user_id == karan.id).first()
            if m:
                m.post = "VICE_PRESIDENT"
                m.branch = "Kaizen Intelligence"
            else:
                db.add(ClubMembership(club_id=club_kaizen.id, user_id=karan.id, post="VICE_PRESIDENT", branch="Kaizen Intelligence", status="ACTIVE"))

        s1 = db.query(User).filter(User.email == "student1@msot.org").first()
        if s1:
            s1.user_category = "STUDENT_MEMBER"
            m = db.query(ClubMembership).filter(ClubMembership.club_id == club_kaizen.id, ClubMembership.user_id == s1.id).first()
            if m:
                m.branch = "CPP Club"

    # Seed sample President Vision Report
    if club_nextcell and advisor_tech:
        aarav = db.query(User).filter(User.email == "aarav.pres@msot.org").first()
        if aarav and db.query(ClubPresidentReport).filter(ClubPresidentReport.club_id == club_nextcell.id).count() == 0:
            rep = ClubPresidentReport(
                club_id=club_nextcell.id,
                president_id=aarav.id,
                advisor_id=advisor_tech.id,
                title="Q1 Strategic Vision: Scaling DeepTech Prototypes & Regional Hackathon",
                vision_statement="Empower 50+ student founders to transition from MVPs to venture capital pitches. Organize a 24-hour Saturday DeepTech Sprint with investor demo tables.",
                vp_operational_orders="Rohan Gupta will coordinate Saturday venue setup, high-speed fiber drops, and Saturday track schedules with the facilities desk.",
                finance_budget_overview="Priya Patel has submitted ₹18,500 AWS & GPU inference budget, sanctioned by Campus Management.",
                media_campaign_plan="Neha Singh leading 4-part Instagram & YouTube Dev Reel campaign showcasing student demo previews.",
                general_secretary_notes="Kavita Deshmukh has finalized attendance compliance records, lab access logs, and safety protocols.",
                status="SUBMITTED",
                advisor_feedback="Comprehensive roadmap Aarav. Ensure the hardware testing lab safety clearance is signed by Wednesday.",
                submitted_at=datetime.datetime.utcnow() - datetime.timedelta(days=1)
            )
            db.add(rep)

    db.commit()

if __name__ == "__main__":
    seed_database()

