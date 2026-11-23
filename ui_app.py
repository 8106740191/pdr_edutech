import os
import urllib.parse
import streamlit as st
import mysql.connector

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="PDR Edutech & Admission Portal",
    page_icon="🎓",
    layout="wide"
)

# --- OWNER CREDENTIALS ---
OWNER_USERNAME = "PraveenYapala"
OWNER_PASSWORD = "Praven@#123"

# Folder for faculty profile pictures
PROFILE_PIC_DIR = "faculty_pics"
os.makedirs(PROFILE_PIC_DIR, exist_ok=True)
DEFAULT_AVATAR = "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"

# --- CLOUD DATABASE CONNECTION (Uses Streamlit Secrets) ---
def get_db_connection():
    return mysql.connector.connect(
        host=st.secrets["pg-c81cfe2-yapalapraveenreddy2002-169b.j.aivencloud.com"],
        port=int(st.secrets["17441"]),
        user=st.secrets["avnadmin"],
        password=st.secrets["AVNS_UUP4iHpQpNoCYU0wM4z"],
        database=st.secrets["defaultdb"]
    )

# --- AUTO-CREATE TABLES & SAMPLE COURSES ---
def init_db():
    try:
        db = get_db_connection()
        cursor = db.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS courses (
                course_id INT AUTO_INCREMENT PRIMARY KEY,
                course_name VARCHAR(100) UNIQUE NOT NULL,
                description TEXT NOT NULL,
                duration_days INT NOT NULL,
                max_seats INT NOT NULL,
                filled_seats INT DEFAULT 0
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS faculty (
                faculty_id INT AUTO_INCREMENT PRIMARY KEY,
                full_name VARCHAR(100) NOT NULL,
                username VARCHAR(50) UNIQUE NOT NULL,
                password VARCHAR(50) NOT NULL,
                course_name VARCHAR(100) NOT NULL,
                profile_pic VARCHAR(255) DEFAULT NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS student_inquiries (
                inquiry_id INT AUTO_INCREMENT PRIMARY KEY,
                student_name VARCHAR(100) NOT NULL,
                mobile_number VARCHAR(20) NOT NULL,
                course_name VARCHAR(100) NOT NULL,
                submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("SELECT COUNT(*) FROM courses")
        if cursor.fetchone()[0] == 0:
            sample_courses = [
                (
                    "PGDCA",
                    "Post Graduate Diploma in Computer Applications covering fundamentals, OS, MS Office, DBMS, and programming.",
                    180, 30, 15
                ),
                (
                    "MS Office Basics",
                    "Hands-on office productivity training in Word, Excel, PowerPoint, and practical workplace documentation.",
                    45, 20, 20
                ),
                (
                    "Python Programming",
                    "Learn Python from scratch including data structures, file handling, MySQL connectivity, and real-world projects.",
                    90, 25, 10
                ),
                (
                    "Java Full Stack",
                    "Complete enterprise development with Core Java, Spring Boot, REST APIs, SQL, and frontend integration.",
                    120, 30, 12
                ),
                (
                    "Web Development",
                    "Build responsive websites using HTML5, CSS3, JavaScript, React, and modern UI design practices.",
                    90, 25, 8
                ),
                (
                    "Tally Prime & GST",
                    "Practical accounting, inventory management, payroll, and GST filing for business and finance careers.",
                    60, 25, 14
                ),
            ]
            cursor.executemany(
                "INSERT INTO courses (course_name, description, duration_days, max_seats, filled_seats) VALUES (%s, %s, %s, %s, %s)",
                sample_courses
            )

        db.commit()
        cursor.close()
        db.close()
    except mysql.connector.Error as err:
        st.error(f"Database Initialization Error: {err}")

init_db()

# --- HELPERS ---
def save_profile_picture(uploaded_file, username):
    if uploaded_file is None:
        return None
    ext = os.path.splitext(uploaded_file.name)[1].lower()
    file_path = os.path.join(PROFILE_PIC_DIR, f"{username}{ext}")
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path

def get_avatar(faculty):
    pic = faculty.get("profile_pic")
    if pic and os.path.exists(pic):
        return pic
    return DEFAULT_AVATAR

def fetch_courses():
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)
    cursor.execute("SELECT * FROM courses")
    rows = cursor.fetchall()
    cursor.close()
    db.close()
    return rows

# --- COURSE IMAGES ---
COURSE_IMAGES = {
    "PGDCA": "https://images.unsplash.com/photo-1517694712202-14dd9538aa97?w=600&q=80",
    "MS Office Basics": "https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?w=600&q=80",
    "Python Programming": "https://images.unsplash.com/photo-1526379095098-d400fd0bf935?w=600&q=80",
    "Java Full Stack": "https://images.unsplash.com/photo-1555066931-4365d14bab8c?w=600&q=80",
    "Web Development": "https://images.unsplash.com/photo-1547658719-da2b51169166?w=600&q=80",
    "Tally Prime & GST": "https://images.unsplash.com/photo-1554224155-6726b3ff858f?w=600&q=80",
}
DEFAULT_COURSE_IMG = "https://images.unsplash.com/photo-1523050854058-8df90110c9f1?w=600&q=80"

# --- CUSTOM CSS ---
st.markdown("""
<style>
    .hero-banner {
        background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 100%);
        padding: 2rem;
        border-radius: 14px;
        color: white;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 15px rgba(37, 99, 235, 0.2);
    }
    .hero-banner h1 { margin: 0; font-size: 2.2rem; color: white; }
    .hero-banner p { margin: 0.4rem 0 0 0; font-size: 1.05rem; opacity: 0.92; }
    .badge-open {
        background-color: #dcfce7; color: #166534;
        padding: 4px 10px; border-radius: 20px; font-size: 0.8rem; font-weight: 600;
    }
    .badge-full {
        background-color: #fee2e2; color: #991b1b;
        padding: 4px 10px; border-radius: 20px; font-size: 0.8rem; font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE ---
if "role" not in st.session_state:
    st.session_state.role = None  # None, "owner", or "faculty"
if "faculty" not in st.session_state:
    st.session_state.faculty = None

courses = fetch_courses()
course_names = [c["course_name"] for c in courses]

# ==============================================================================
# VIEW 1: PUBLIC SITE (COURSES + STUDENT INQUIRY) + LOGIN ONLY IN SIDEBAR
# ==============================================================================
def show_public_portal():
    with st.sidebar:
        st.markdown("## 🔐 Portal Login")
        tab_fac_login, tab_owner_login = st.tabs(["👨‍🏫 Faculty Login", "👑 Owner Login"])

        # Faculty Login
        with tab_fac_login:
            with st.form("faculty_login_form", clear_on_submit=True):
                f_user = st.text_input("👤 Faculty Username", placeholder="Enter username")
                f_pass = st.text_input("🔑 Password", type="password", placeholder="Enter password")
                btn_f_login = st.form_submit_button("Faculty Login ➜", use_container_width=True, type="primary")

            if btn_f_login:
                if not f_user or not f_pass:
                    st.warning("⚠️ Enter username and password.")
                else:
                    try:
                        db = get_db_connection()
                        cursor = db.cursor(dictionary=True)
                        cursor.execute(
                            "SELECT * FROM faculty WHERE username = %s AND password = %s",
                            (f_user, f_pass)
                        )
                        fac = cursor.fetchone()
                        cursor.close()
                        db.close()
                        if fac:
                            st.session_state.role = "faculty"
                            st.session_state.faculty = fac
                            st.rerun()
                        else:
                            st.error("❌ Invalid faculty credentials.")
                    except mysql.connector.Error as err:
                        st.error(f"DB Error: {err}")

        # Owner Login
        with tab_owner_login:
            with st.form("owner_login_form", clear_on_submit=True):
                o_user = st.text_input("👑 Owner Username", placeholder="Enter owner username")
                o_pass = st.text_input("🔑 Owner Password", type="password", placeholder="Enter owner password")
                btn_o_login = st.form_submit_button("Owner Login ➜", use_container_width=True, type="primary")

            if btn_o_login:
                if o_user == OWNER_USERNAME and o_pass == OWNER_PASSWORD:
                    st.session_state.role = "owner"
                    st.rerun()
                else:
                    st.error("❌ Invalid owner credentials.")

    # --- MAIN PUBLIC PAGE ---
    st.markdown("""
    <div class="hero-banner">
        <h1>🎓 PDR Edutech & Admission Portal</h1>
        <p>Explore our job-ready IT & vocational courses. Interested? Send your details directly to our course faculty!</p>
    </div>
    """, unsafe_allow_html=True)

    # 1. ALL COURSES GRID (Visible to everyone)
    st.subheader("📚 Our Courses")
    cols = st.columns(3, gap="medium")
    for idx, course in enumerate(courses):
        is_full = course["filled_seats"] >= course["max_seats"]
        img_url = COURSE_IMAGES.get(course["course_name"], DEFAULT_COURSE_IMG)

        with cols[idx % 3]:
            with st.container(border=True):
                st.image(img_url, use_container_width=True)
                st.markdown(f"#### 📘 {course['course_name']}")
                if is_full:
                    st.markdown('<span class="badge-full">🔴 Batch Full (Try after 90 days)</span>', unsafe_allow_html=True)
                else:
                    st.markdown('<span class="badge-open">🟢 Admissions Open</span>', unsafe_allow_html=True)

                st.write("")
                st.write(course["description"])
                st.caption(f"⏱️ **Duration:** {course['duration_days']} Days  |  💺 **Seats:** {course['filled_seats']} / {course['max_seats']}")
                st.progress(min(course["filled_seats"] / course["max_seats"], 1.0))

    st.divider()

    # 2. STUDENT INTEREST / INQUIRY FORM
    st.subheader("📩 Interested in a Course? Send Your Details to the Institute")
    col_form, col_info = st.columns([1.3, 1], gap="large")

    with col_form:
        with st.container(border=True):
            with st.form("student_inquiry_form", clear_on_submit=True):
                s_name = st.text_input("🪪 Trainee / Student Full Name", placeholder="Enter your full name")
                s_mobile = st.text_input("📱 Mobile Number", placeholder="Enter 10-digit mobile number")
                s_course = st.selectbox("📘 Interested Course", course_names)
                submit_inq = st.form_submit_button("Submit Interest 🚀", use_container_width=True, type="primary")

            if submit_inq:
                if not s_name or not s_mobile:
                    st.warning("⚠️ Please enter your Name and Mobile Number.")
                else:
                    try:
                        db = get_db_connection()
                        cursor = db.cursor()
                        cursor.execute(
                            "INSERT INTO student_inquiries (student_name, mobile_number, course_name) VALUES (%s, %s, %s)",
                            (s_name, s_mobile, s_course)
                        )
                        db.commit()
                        cursor.close()
                        db.close()
                        st.success(f"✅ Thank you, **{s_name}**! Your details have been sent to our **{s_course}** faculty.")
                    except mysql.connector.Error as err:
                        st.error(f"Database Error: {err}")

    with col_info:
        st.image(
            "https://images.unsplash.com/photo-1522202176988-66273c2fd55f?w=800&q=80",
            caption="Our faculty will contact you with batch timings & syllabus details.",
            use_container_width=True
        )


# ==============================================================================
# VIEW 2: OWNER DASHBOARD (COURSE-WISE STUDENTS + FACULTY REG + QR CODE)
# ==============================================================================
def show_owner_dashboard():
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=95)
        st.markdown("### 👑 Institute Owner")
        st.caption("Admin Access: Full Control")
        st.divider()
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.role = None
            st.rerun()

    st.markdown("""
    <div class="hero-banner">
        <h1>👑 PDR Edutech — Owner Dashboard</h1>
        <p>Monitor course-wise trainee counts, view individual course inquiries, register faculty, and generate your portal QR code.</p>
    </div>
    """, unsafe_allow_html=True)

    tab_overview, tab_reg_fac, tab_qr = st.tabs([
        "📊 Course-wise Students",
        "➕ Register & Manage Faculty",
        "📱 Site QR Code"
    ])

    # --- TAB 1: COURSE-WISE STUDENT COUNTS & INDIVIDUAL COURSE VIEW ---
    with tab_overview:
        try:
            db = get_db_connection()
            cursor = db.cursor(dictionary=True)

            cursor.execute("""
                SELECT c.course_name, COUNT(s.inquiry_id) AS total_students
                FROM courses c
                LEFT JOIN student_inquiries s ON c.course_name = s.course_name
                GROUP BY c.course_name
            """)
            counts = cursor.fetchall()
            cursor.close()
            db.close()
        except mysql.connector.Error as err:
            st.error(f"Database Error: {err}")
            return

        st.subheader("📈 Total Students by Course")
        metric_cols = st.columns(3)
        for idx, row in enumerate(counts):
            with metric_cols[idx % 3]:
                st.metric(f"📘 {row['course_name']}", f"{row['total_students']} Students")

        st.divider()

        st.subheader("📋 View Trainees by Course")
        selected_course = st.selectbox("Select a Course to View Trainees", course_names)

        try:
            db = get_db_connection()
            cursor = db.cursor(dictionary=True)
            cursor.execute(
                "SELECT inquiry_id, student_name, mobile_number, submitted_at FROM student_inquiries WHERE course_name = %s ORDER BY submitted_at DESC",
                (selected_course,)
            )
            course_students = cursor.fetchall()
            cursor.close()
            db.close()
        except mysql.connector.Error as err:
            st.error(f"Database Error: {err}")
            return

        if course_students:
            table_md = "| ID | Trainee Name | Mobile Number | Submitted At |\n"
            table_md += "|---|---|---|---|\n"
            for row in course_students:
                table_md += f"| {row['inquiry_id']} | {row['student_name']} | {row['mobile_number']} | {row['submitted_at']} |\n"
            st.markdown(table_md)
        else:
            st.info(f"No students have registered interest in **{selected_course}** yet.")

    # --- TAB 2: REGISTER FACULTY (OWNER ONLY) ---
    with tab_reg_fac:
        col_form, col_list = st.columns([1, 1.4], gap="large")

        with col_form:
            st.subheader("➕ Register New Faculty")
            with st.form("owner_faculty_reg_form", clear_on_submit=True):
                reg_name = st.text_input("🪪 Faculty Full Name", placeholder="e.g., Praveen Kumar")
                reg_course = st.selectbox("📘 Assigned Course", course_names)
                reg_user = st.text_input("👤 Faculty Username", placeholder="e.g., pgdca_faculty")
                reg_pass = st.text_input("🔑 Faculty Password", type="password", placeholder="Create password")
                reg_pic = st.file_uploader("🖼️ Profile Pic (Optional)", type=["png", "jpg", "jpeg"])
                btn_reg = st.form_submit_button("Register Faculty ✅", use_container_width=True, type="primary")

            if btn_reg:
                if not reg_name or not reg_user or not reg_pass:
                    st.warning("⚠️ Full Name, Username, and Password are required.")
                else:
                    try:
                        pic_path = save_profile_picture(reg_pic, reg_user)
                        db = get_db_connection()
                        cursor = db.cursor()
                        cursor.execute(
                            "INSERT INTO faculty (full_name, username, password, course_name, profile_pic) VALUES (%s, %s, %s, %s, %s)",
                            (reg_name, reg_user, reg_pass, reg_course, pic_path)
                        )
                        db.commit()
                        cursor.close()
                        db.close()
                        st.success(f"🎉 Faculty **{reg_name}** registered for **{reg_course}**!")
                    except mysql.connector.IntegrityError:
                        st.error("❌ Username already exists.")
                    except mysql.connector.Error as err:
                        st.error(f"DB Error: {err}")

        with col_list:
            st.subheader("👨‍🏫 Registered Faculty List")
            try:
                db = get_db_connection()
                cursor = db.cursor(dictionary=True)
                cursor.execute("SELECT faculty_id, full_name, username, course_name FROM faculty ORDER BY faculty_id DESC")
                all_fac = cursor.fetchall()
                cursor.close()
                db.close()

                if all_fac:
                    fac_md = "| ID | Faculty Name | Username | Assigned Course |\n"
                    fac_md += "|---|---|---|---|\n"
                    for f in all_fac:
                        fac_md += f"| {f['faculty_id']} | {f['full_name']} | `{f['username']}` | {f['course_name']} |\n"
                    st.markdown(fac_md)
                else:
                    st.info("No faculty members registered yet.")
            except mysql.connector.Error as err:
                st.error(f"Database Error: {err}")

    # --- TAB 3: QR CODE GENERATOR ---
    with tab_qr:
        st.subheader("📱 Generate Portal QR Code")
        st.write("Paste your permanent Streamlit Cloud URL to generate a scannable QR code.")
        live_url = st.text_input("🌐 Live Website URL", placeholder="https://your-app.streamlit.app")

        if live_url:
            encoded_url = urllib.parse.quote(live_url.strip(), safe="")
            qr_img_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={encoded_url}"

            st.image(qr_img_url, caption="Scan this QR code to open the PDR Edutech Portal", width=280)
            st.markdown(f"**Direct Link:** [{live_url.strip()}]({live_url.strip()})")
            st.info("💡 Right-click the QR code image above and choose **Save image as...** to print it on posters or share on WhatsApp.")


# ==============================================================================
# VIEW 3: FACULTY DASHBOARD (ONLY SHOWS STUDENTS INTERESTED IN THEIR COURSE)
# ==============================================================================
def show_faculty_dashboard():
    fac = st.session_state.faculty
    assigned_course = fac["course_name"]

    with st.sidebar:
        st.image(get_avatar(fac), width=110)
        st.markdown(f"### 👨‍🏫 {fac['full_name']}")
        st.caption(f"📘 Course: **{assigned_course}**")
        st.caption(f"👤 Username: `@{fac['username']}`")
        st.divider()
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.role = None
            st.session_state.faculty = None
            st.rerun()

    st.markdown(f"""
    <div class="hero-banner">
        <h1>👨‍🏫 {assigned_course} — Faculty Dashboard</h1>
        <p>Welcome, {fac['full_name']}. Below are the trainees who expressed interest in <b>{assigned_course}</b>.</p>
    </div>
    """, unsafe_allow_html=True)

    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute(
            "SELECT inquiry_id, student_name, mobile_number, course_name, submitted_at FROM student_inquiries WHERE course_name = %s ORDER BY submitted_at DESC",
            (assigned_course,)
        )
        inquiries = cursor.fetchall()
        cursor.close()
        db.close()
    except mysql.connector.Error as err:
        st.error(f"Database Error: {err}")
        return

    tab_leads, tab_profile = st.tabs([f"📋 Interested Trainees ({len(inquiries)})", "👤 Faculty Profile"])

    with tab_leads:
        st.metric(f"📩 Total Inquiries for {assigned_course}", len(inquiries))
        st.write("")
        if inquiries:
            table_md = "| ID | Trainee Name | Mobile Number | Course | Submitted At |\n"
            table_md += "|---|---|---|---|---|\n"
            for row in inquiries:
                table_md += f"| {row['inquiry_id']} | {row['student_name']} | {row['mobile_number']} | {row['course_name']} | {row['submitted_at']} |\n"
            st.markdown(table_md)
        else:
            st.info(f"No student inquiries received for **{assigned_course}** yet.")

    with tab_profile:
        st.subheader("👤 Faculty Details")
        col_pic, col_det = st.columns([1, 2.5], gap="large")
        with col_pic:
            st.image(get_avatar(fac), width=160)
            new_pic = st.file_uploader("📸 Update Profile Picture", type=["png", "jpg", "jpeg"], key="fac_pic_up")
            if new_pic is not None and st.button("💾 Save Photo", type="primary"):
                saved = save_profile_picture(new_pic, fac["username"])
                db = get_db_connection()
                cursor = db.cursor()
                cursor.execute("UPDATE faculty SET profile_pic = %s WHERE faculty_id = %s", (saved, fac["faculty_id"]))
                db.commit()
                cursor.close()
                db.close()
                st.session_state.faculty["profile_pic"] = saved
                st.success("✅ Profile picture updated!")
                st.rerun()

        with col_det:
            c1, c2, c3 = st.columns(3)
            c1.metric("🆔 Faculty ID", fac["faculty_id"])
            c2.metric("🪪 Full Name", fac["full_name"])
            c3.metric("📘 Assigned Course", assigned_course)


# --- ROUTER ---
if st.session_state.role == "owner":
    show_owner_dashboard()
elif st.session_state.role == "faculty" and st.session_state.faculty is not None:
    show_faculty_dashboard()
else:
    show_public_portal()