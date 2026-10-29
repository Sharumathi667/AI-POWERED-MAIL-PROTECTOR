"""
Synthetic Dataset Generator for Phishing Email & Suspicious Login Investigation
Generates >= 5,000 synthetic emails and >= 10,000 synthetic login events with
internally consistent features, realistic noise, borderline cases, and correlated
phishing-to-login compromise scenarios.
"""

import os
import random
import datetime
import math
import pandas as pd
import numpy as np

# Configurable constants
RANDOM_SEED = 42
NUM_EMAILS = 5200
NUM_LOGINS = 10500
NUM_USERS = 150

random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

CAMPUS_DOMAIN = "campus.edu"
CAMPUS_NAME = "Metropolitan University"

# Pre-defined user pool with typical baseline locations and devices
USERS = []
CITIES_BASE = [
    {"city": "Boston", "country": "United States", "lat": 42.3601, "lon": -71.0589},
    {"city": "Cambridge", "country": "United States", "lat": 42.3736, "lon": -71.1097},
    {"city": "Somerville", "country": "United States", "lat": 42.3876, "lon": -71.0995},
    {"city": "Quincy", "country": "United States", "lat": 42.2529, "lon": -71.0023},
    {"city": "Newton", "country": "United States", "lat": 42.3370, "lon": -71.2092},
]

UNUSUAL_CITIES = [
    {"city": "Moscow", "country": "Russia", "lat": 55.7558, "lon": 37.6173},
    {"city": "Lagos", "country": "Nigeria", "lat": 6.5244, "lon": 3.3792},
    {"city": "Bucharest", "country": "Romania", "lat": 44.4268, "lon": 26.1025},
    {"city": "Shenzhen", "country": "China", "lat": 22.5431, "lon": 114.0579},
    {"city": "Sao Paulo", "country": "Brazil", "lat": -23.5505, "lon": -46.6333},
    {"city": "Frankfurt", "country": "Germany", "lat": 50.1109, "lon": 8.6821},
    {"city": "Toronto", "country": "Canada", "lat": 43.6532, "lon": -79.3832},
    {"city": "London", "country": "United Kingdom", "lat": 51.5074, "lon": -0.1278},
]

DEVICES_POOL = [
    {"type": "laptop", "os": "Windows 11", "browser": "Chrome"},
    {"type": "laptop", "os": "macOS Sonoma", "browser": "Safari"},
    {"type": "mobile", "os": "iOS 17", "browser": "Safari"},
    {"type": "mobile", "os": "Android 14", "browser": "Chrome"},
    {"type": "desktop", "os": "Windows 11", "browser": "Edge"},
    {"type": "laptop", "os": "Ubuntu 22.04", "browser": "Firefox"},
]

SUSPICIOUS_BROWSERS = ["HeadlessChrome", "Unknown/TorBrowser", "Python-Requests/2.31", "curl/8.4.0"]

for i in range(1, NUM_USERS + 1):
    u_id = f"USER-{1000 + i}"
    base_loc = random.choice(CITIES_BASE)
    primary_dev = random.choice(DEVICES_POOL)
    secondary_dev = random.choice(DEVICES_POOL)
    USERS.append({
        "user_id": u_id,
        "email": f"student{i}@{CAMPUS_DOMAIN}" if i > 30 else f"staff{i}@{CAMPUS_DOMAIN}",
        "name": f"User {i}",
        "base_location": base_loc,
        "known_devices": [
            f"DEV-{u_id}-1",
            f"DEV-{u_id}-2"
        ],
        "device_configs": [primary_dev, secondary_dev]
    })


def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371.0 # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)


# -------------------------------------------------------------
# 1. EMAIL DATASET GENERATION
# -------------------------------------------------------------
PHISHING_TEMPLATES = [
    {
        "category": "password_reset",
        "subject_templates": [
            "CRITICAL: Immediate Password Reset Required",
            "Security Notice: Unauthorized Sign-in Attempt Detected - Verify Identity",
            "Password Expiry Warning for {email}",
            "Mandatory Password Change Required by IT Helpdesk",
            "Urgent: Your campus account credentials will expire today"
        ],
        "body_templates": [
            "Dear User,\n\nOur system detected multiple failed login attempts on your account. To maintain access to your student and employee portals, you are required to immediately reset your authentication credentials at the official link below:\n\n{url}\n\nFailure to verify within 12 hours will result in administrative account suspension.\n\nIT Support Services\n{campus}",
            "Attention: Your password for {email} expires in 2 hours. Click the link to update your credentials and retain access to campus services: {url}. Please do not ignore this notification."
        ],
        "sender_domains": ["campus-auth-security.xyz", "portal-metropolitan-it.com", "verify-campus-login.net", "identity-sso-support.org"],
        "display_names": ["Campus IT Support", "IT Helpdesk Security", "SSO Administration", "Account Security Team"],
        "attachment_prob": 0.1,
        "attachment_type": "html"
    },
    {
        "category": "account_suspension",
        "subject_templates": [
            "Account Deactivation Notice - Action Required",
            "Final Notice: Academic Mailbox Suspension Scheduled",
            "Termination of Access: Inactive Account Cleanup",
            "Warning: Account Suspended Due to Policy Violation"
        ],
        "body_templates": [
            "This is an automated notification from the Academic Registrar. Your mailbox and student portal access have been marked for deactivation due to missing security compliance filings. Re-activate your profile here: {url}\n\nThank you for your cooperation.",
            "Your campus email account has exceeded storage quota and has been scheduled for deletion. Expand your storage allotment free of charge by confirming your account details: {url}"
        ],
        "sender_domains": ["admin-campus-review.net", "registrar-mail-dept.com", "campus-storage-helpdesk.info"],
        "display_names": ["Academic Registrar", "Mailbox Storage Manager", "Office of the Dean"],
        "attachment_prob": 0.05,
        "attachment_type": "pdf"
    },
    {
        "category": "scholarship_financial",
        "subject_templates": [
            "Financial Aid Disbursement: Emergency Grant Awarded ($2,450.00)",
            "Tuition Overpayment Refund Notice for Fall Semester",
            "Direct Deposit Failure - Update Banking Information Immediately",
            "Approved: Student Relief Subsidy Payment Confirmation"
        ],
        "body_templates": [
            "Greetings,\n\nYou have been approved for the Student Emergency Relief Grant of $2,450.00. Funds will be deposited directly to your bank account upon verification of your university banking profile:\n\n{url}\n\nDisbursement Officer,\nFinancial Services Bureau",
            "We attempted to credit your bank account with a tuition refund of $820.50, but the routing information failed verification. Log in to correct your banking information: {url}"
        ],
        "sender_domains": ["bursar-refunds-dept.com", "student-aid-direct.org", "campus-grant-processing.net"],
        "display_names": ["Financial Aid Office", "Bursar Services", "Campus Student Accounts"],
        "attachment_prob": 0.2,
        "attachment_type": "pdf"
    },
    {
        "category": "exam_and_grades",
        "subject_templates": [
            "Confidential: Final Examination Grade Sheet Released",
            "Academic Standing Warning & Grade Review Document",
            "Document Verification Required: Official Transcript Ready"
        ],
        "body_templates": [
            "Your midterm and continuous evaluation grades have been published by the examination board. Please review the attached evaluation sheet or inspect your grades via the evaluation server: {url}\n\nExam Controller Office",
            "A faculty instructor has submitted an academic honor violation inquiry regarding your recent exam submission. Review the citation docket here: {url}"
        ],
        "sender_domains": ["exam-results-portal.com", "academic-docket-files.net", "grades-verification-edu.xyz"],
        "display_names": ["Controller of Examinations", "Academic Review Board", "Grading Committee"],
        "attachment_prob": 0.45,
        "attachment_type": "zip"
    },
    {
        "category": "subtle_phishing", # Borderline harder examples without obvious urgency
        "subject_templates": [
            "Updated Faculty Syllabus & Reading List",
            "Campus Shared OneDrive Document: 'Research Collaboration Proposal'",
            "Library Equipment Checkout Confirmation #4892",
            "Survey: University Dining Hall Feedback & Raffle Entry"
        ],
        "body_templates": [
            "Hello,\n\nPlease find the revised schedule and reading materials shared through our department OneDrive repository. Access the document via the cloud viewer: {url}\n\nBest regards,\nProf. H. Miller",
            "Thank you for requesting equipment from the Central University Library. Please review and sign the digital liability agreement: {url}"
        ],
        "sender_domains": ["onedrive-share-docsv2.com", "university-survey-cloud.org", "library-equipment-portal.net"],
        "display_names": ["Prof. Harold Miller", "Central University Library", "Student Services Committee"],
        "attachment_prob": 0.25,
        "attachment_type": "docx"
    }
]

SAFE_TEMPLATES = [
    {
        "category": "academic",
        "subject_templates": [
            "CS301: Homework 3 Solutions and Lecture Notes Posted",
            "Reminder: Office Hours Rescheduled to Thursday 3 PM",
            "Biology Lab Safety Protocols & Required Equipment",
            "Mathematics Colloquium: Dr. Sarah Jenkins on Cryptography",
            "Syllabus Update: Midterm Exam Review Session"
        ],
        "body_templates": [
            "Hi everyone,\n\nI have posted the lecture slides and homework solutions on the course LMS portal at https://lms.campus.edu/courses/301. Please review them prior to tomorrow's recitation.\n\nBest regards,\nProf. Davis",
            "Good afternoon students,\n\nDue to a departmental faculty meeting, my office hours today will be shifted from 2 PM to 4 PM in Hall 402. You can also join remotely via https://zoom.us/j/campus123.\n\nSincerely,\nDr. Linda Vance"
        ],
        "sender_domains": [CAMPUS_DOMAIN, "cs.campus.edu", "math.campus.edu", "bio.campus.edu"],
        "display_names": ["Prof. Robert Davis", "Dr. Linda Vance", "Department of Computer Science", "Academic Advising"],
        "attachment_prob": 0.35,
        "attachment_type": "pdf"
    },
    {
        "category": "administrative",
        "subject_templates": [
            "Campus Shuttle Route Schedule for Fall Recess",
            "Campus Recreation Center Holiday Operating Hours",
            "Library Book Due Date Reminder: 2 Items",
            "Spring Semester Course Registration Timetable Announced",
            "Facilities Notice: Routine Elevator Maintenance in Science Hall"
        ],
        "body_templates": [
            "Dear Campus Community,\n\nPlease take note of the modified campus transportation shuttle routes during the upcoming holiday weekend. Full route maps and live GPS trackers are accessible on our website: https://transportation.campus.edu/shuttle.\n\nDepartment of Parking and Transportation",
            "This is an automated courtesy notice from University Library Services. Your borrowed title 'Introduction to Distributed Systems' is due in 3 days. Renew your loan online at https://library.campus.edu/myaccount."
        ],
        "sender_domains": [CAMPUS_DOMAIN, "library.campus.edu", "facilities.campus.edu"],
        "display_names": ["Transportation Services", "University Library System", "Campus Facilities Management"],
        "attachment_prob": 0.15,
        "attachment_type": "pdf"
    },
    {
        "category": "urgent_safe", # Borderline hard examples: safe emails with urgent phrasing / words like password/account
        "subject_templates": [
            "ACTION REQUIRED: Mandatory Cybersecurity Awareness Training (Safe Computing)",
            "Urgent: Course Drop/Add Deadline is Today at 5:00 PM EST",
            "Important Account Reminder: Multi-Factor Authentication Verification Protocol",
            "Notice: Annual Safety Inspection of Laboratory Electrical Outlets"
        ],
        "body_templates": [
            "Campus IT Security Bulletin:\n\nAll university students and staff must complete the annual cybersecurity awareness module by November 15. The training portal can be accessed through your standard Single Sign-On dashboard at https://sso.campus.edu/training.\n\nRemember: Official campus staff will NEVER ask for your password via email or unofficial forms.",
            "URGENT NOTICE FROM REGISTRAR:\n\nThe official university add/drop registration deadline for the current academic session closes promptly at 5:00 PM today. If you need advisor sign-off, visit the portal: https://registrar.campus.edu/enrollment."
        ],
        "sender_domains": [CAMPUS_DOMAIN, "it-security.campus.edu", "registrar.campus.edu"],
        "display_names": ["Campus IT Security Office", "Office of the University Registrar", "Chief Information Security Officer"],
        "attachment_prob": 0.1,
        "attachment_type": "pdf"
    },
    {
        "category": "newsletter",
        "subject_templates": [
            "This Week at Metropolitan: Student Club Fair & Concert",
            "Career Services Newsletter: Upcoming Tech & Engineering Expo",
            "Campus Dining Weekly Menu & Sustainability Initiatives",
            "Alumni Association Quarterly Digest"
        ],
        "body_templates": [
            "Welcome back! Check out this week's featured events on the student union lawn, including the annual robotics club demonstration and musical performances. Full event calendar available at https://events.campus.edu/week.\n\nStudent Affairs Council",
            "Over 45 technology and research organizations will be recruiting on campus next Wednesday at the Student Center. Register your attendance and view attending companies: https://careers.campus.edu/expo."
        ],
        "sender_domains": [CAMPUS_DOMAIN, "alumni.campus.edu", "careers.campus.edu"],
        "display_names": ["Student Affairs", "Career Development Center", "Metropolitan Alumni Relations"],
        "attachment_prob": 0.05,
        "attachment_type": "pdf"
    }
]

def generate_emails(num_records=NUM_EMAILS):
    records = []
    base_time = datetime.datetime.now() - datetime.timedelta(days=35)
    
    # 48% phishing, 52% safe
    phishing_target = int(num_records * 0.48)
    safe_target = num_records - phishing_target
    
    print(f"Generating {num_records} emails ({phishing_target} phishing, {safe_target} safe)...")
    
    labels_pool = ["phishing"] * phishing_target + ["safe"] * safe_target
    random.shuffle(labels_pool)
    
    for idx, label in enumerate(labels_pool):
        email_id = f"EMAIL-{10000 + idx}"
        user = random.choice(USERS)
        user_id = user["user_id"]
        
        # Stagger timestamp over last 35 days
        offset_minutes = random.randint(0, 35 * 24 * 60)
        email_time = base_time + datetime.timedelta(minutes=offset_minutes)
        time_str = email_time.strftime("%Y-%m-%d %H:%M:%S")
        
        if label == "phishing":
            template_group = random.choice(PHISHING_TEMPLATES)
            subject_tmpl = random.choice(template_group["subject_templates"])
            subject = subject_tmpl.format(email=user["email"], campus=CAMPUS_NAME)
            
            sender_domain = random.choice(template_group["sender_domains"])
            display_name = random.choice(template_group["display_names"])
            sender_email = f"{display_name.lower().replace(' ', '.')[:12]}@{sender_domain}"
            
            # Simulated phishing URLs
            phish_slugs = ["login-auth", "sso-verify", "update-credentials", "secure-token", "view-grade", "disburse-funds"]
            phish_domain = random.choice([sender_domain, "bit.ly/campus-sec", "tinyurl.com/sso384", "secure-sso-gateway.tk", "auth-portal-update.org"])
            generated_url = f"https://{phish_domain}/{random.choice(phish_slugs)}"
            urls = generated_url
            link_count = random.randint(1, 4)
            
            body_tmpl = random.choice(template_group["body_templates"])
            body = body_tmpl.format(url=generated_url, email=user["email"], campus=CAMPUS_NAME)
            
            # Phishing header signals
            # Most phishing has SPF / DKIM / DMARC failures or mismatches
            spf_result = random.choices(["fail", "softfail", "none", "pass"], weights=[0.55, 0.25, 0.15, 0.05])[0]
            dkim_result = random.choices(["fail", "none", "pass"], weights=[0.60, 0.30, 0.10])[0]
            dmarc_result = random.choices(["fail", "none", "pass"], weights=[0.70, 0.20, 0.10])[0]
            
            # Display name mismatch (e.g. name says IT Helpdesk, domain is free-mail or strange domain)
            display_name_mismatch = 1 if (random.random() < 0.85) else 0
            
            # Reply-to mismatch
            if random.random() < 0.75:
                reply_to = f"service-inbox@{random.choice(['gmail-temp-relay.com', 'anonymous-mail.org', 'support-desk-tickets.xyz'])}"
            else:
                reply_to = sender_email
                
            domain_age_category = random.choices(["new_<30d", "moderate_1-12m", "established_>1y"], weights=[0.70, 0.25, 0.05])[0]
            
            has_attachment = 1 if (random.random() < template_group["attachment_prob"]) else 0
            attachment_type = template_group["attachment_type"] if has_attachment else "none"
            
        else: # SAFE
            template_group = random.choice(SAFE_TEMPLATES)
            subject_tmpl = random.choice(template_group["subject_templates"])
            subject = subject_tmpl.format(email=user["email"], campus=CAMPUS_NAME)
            
            sender_domain = random.choice(template_group["sender_domains"])
            display_name = random.choice(template_group["display_names"])
            sender_email = f"{display_name.lower().replace(' ', '.')[:12]}@{sender_domain}"
            
            # Safe official URLs
            safe_urls = [
                f"https://lms.{CAMPUS_DOMAIN}/course/view",
                f"https://registrar.{CAMPUS_DOMAIN}/schedule",
                f"https://library.{CAMPUS_DOMAIN}/catalog",
                f"https://events.{CAMPUS_DOMAIN}/calendar",
                f"https://sso.{CAMPUS_DOMAIN}/auth"
            ]
            urls = random.choice(safe_urls) if random.random() < 0.65 else ""
            link_count = random.randint(1, 2) if urls else 0
            
            body_tmpl = random.choice(template_group["body_templates"])
            body = body_tmpl.format(url=urls or f"https://www.{CAMPUS_DOMAIN}")
            
            # Safe authentication results: predominantly pass
            spf_result = random.choices(["pass", "softfail", "none"], weights=[0.92, 0.05, 0.03])[0]
            dkim_result = random.choices(["pass", "none", "fail"], weights=[0.90, 0.08, 0.02])[0]
            dmarc_result = random.choices(["pass", "none", "fail"], weights=[0.92, 0.06, 0.02])[0]
            
            display_name_mismatch = 0 if random.random() < 0.95 else 1 # Occasional guest lecturer mismatch
            reply_to = sender_email if random.random() < 0.92 else f"no-reply@{sender_domain}"
            domain_age_category = "established_>1y"
            
            has_attachment = 1 if (random.random() < template_group["attachment_prob"]) else 0
            attachment_type = template_group["attachment_type"] if has_attachment else "none"
            
        records.append({
            "email_id": email_id,
            "user_id": user_id,
            "timestamp": time_str,
            "sender_name": display_name,
            "sender_email": sender_email,
            "sender_domain": sender_domain,
            "reply_to": reply_to,
            "email_subject": subject,
            "email_body": body,
            "urls": urls,
            "link_count": link_count,
            "has_attachment": has_attachment,
            "attachment_type": attachment_type,
            "spf_result": spf_result,
            "dkim_result": dkim_result,
            "dmarc_result": dmarc_result,
            "display_name_mismatch": display_name_mismatch,
            "domain_age_category": domain_age_category,
            "label": label
        })
        
    df = pd.DataFrame(records)
    return df


# -------------------------------------------------------------
# 2. LOGIN DATASET GENERATION
# -------------------------------------------------------------
def generate_logins(num_records=NUM_LOGINS, email_df=None):
    print(f"Generating {num_records} login events...")
    records = []
    
    # Track per-user state for time series consistency
    user_state = {}
    base_time = datetime.datetime.now() - datetime.timedelta(days=35)
    
    for u in USERS:
        u_id = u["user_id"]
        user_state[u_id] = {
            "last_login_time": base_time + datetime.timedelta(hours=random.randint(0, 48)),
            "last_location": u["base_location"],
            "last_device": u["known_devices"][0],
            "last_ip": f"198.51.100.{random.randint(10, 240)}" # Synthetic documentation IP
        }
        
    # We want ~18% suspicious logins and ~82% normal logins
    suspicious_target = int(num_records * 0.18)
    normal_target = num_records - suspicious_target
    
    # We will generate sequential logins for users
    events_per_user = num_records // len(USERS)
    
    # Pre-select some users with recent phishing emails to inject direct correlation attacks!
    phish_emails = email_df[email_df["label"] == "phishing"] if email_df is not None else None
    correlated_users = set()
    if phish_emails is not None and not phish_emails.empty:
        correlated_users = set(phish_emails["user_id"].unique()[:25])
        
    event_counter = 10001
    
    for u in USERS:
        u_id = u["user_id"]
        state = user_state[u_id]
        current_time = state["last_login_time"]
        is_compromised_target = u_id in correlated_users
        
        # Calculate how many events for this user
        n_events = events_per_user + random.randint(-5, 5)
        
        for step in range(n_events):
            event_id = f"LOGIN-{event_counter}"
            event_counter += 1
            
            # Advance time by 30 mins to 24 hours
            minutes_gap = random.choices([15, 45, 120, 360, 720, 1440], weights=[0.15, 0.30, 0.30, 0.15, 0.05, 0.05])[0]
            current_time = current_time + datetime.timedelta(minutes=minutes_gap)
            time_str = current_time.strftime("%Y-%m-%d %H:%M:%S")
            
            # Determine if this event should be suspicious
            # Higher chance if target compromised user
            make_suspicious = False
            if is_compromised_target and step in (n_events // 2, n_events - 2):
                make_suspicious = True
            elif random.random() < 0.14:
                make_suspicious = True
                
            if make_suspicious:
                scenario = random.choice([
                    "impossible_travel",
                    "credential_stuffing_then_success",
                    "new_device_foreign_location",
                    "tor_night_anomaly",
                    "failed_burst"
                ])
                
                label = "suspicious"
                
                if scenario == "impossible_travel":
                    loc = random.choice(UNUSUAL_CITIES)
                    prev_loc = state["last_location"]
                    dist = haversine_distance(prev_loc["lat"], prev_loc["lon"], loc["lat"], loc["lon"])
                    short_minutes = random.randint(15, 60) # Impossible: 6,000+ km in 30 mins
                    current_time = state["last_login_time"] + datetime.timedelta(minutes=short_minutes)
                    time_str = current_time.strftime("%Y-%m-%d %H:%M:%S")
                    
                    ip = f"203.0.113.{random.randint(10, 240)}" # Synthetic documentation IP
                    dev_id = f"DEV-ROGUE-{random.randint(100, 999)}"
                    dev_config = random.choice(DEVICES_POOL)
                    login_success = 1
                    failed_attempts = 1
                    is_new_device = 1
                    is_new_location = 1
                    distance_km = dist
                    minutes_since_prev = short_minutes
                    impossible_travel = 1
                    browser = dev_config["browser"]
                    os_name = dev_config["os"]
                    dev_type = dev_config["type"]
                    
                elif scenario == "credential_stuffing_then_success":
                    loc = random.choice(UNUSUAL_CITIES)
                    prev_loc = state["last_location"]
                    dist = haversine_distance(prev_loc["lat"], prev_loc["lon"], loc["lat"], loc["lon"])
                    ip = f"198.51.100.{random.randint(100, 250)}"
                    dev_id = f"DEV-UNRECOGNIZED-{random.randint(200, 800)}"
                    dev_config = random.choice(DEVICES_POOL)
                    login_success = 1
                    failed_attempts = random.randint(4, 9) # Multiple failed then success
                    is_new_device = 1
                    is_new_location = 1
                    distance_km = dist
                    minutes_since_prev = random.randint(30, 240)
                    impossible_travel = 1 if (dist > 1000 and minutes_since_prev < 60) else 0
                    browser = dev_config["browser"]
                    os_name = dev_config["os"]
                    dev_type = dev_config["type"]
                    
                elif scenario == "new_device_foreign_location":
                    loc = random.choice(UNUSUAL_CITIES)
                    prev_loc = state["last_location"]
                    dist = haversine_distance(prev_loc["lat"], prev_loc["lon"], loc["lat"], loc["lon"])
                    ip = f"203.0.113.{random.randint(10, 200)}"
                    dev_id = f"DEV-NEW-{random.randint(500, 999)}"
                    login_success = 1
                    failed_attempts = 2
                    is_new_device = 1
                    is_new_location = 1
                    distance_km = dist
                    minutes_since_prev = random.randint(120, 600)
                    impossible_travel = 0
                    browser = random.choice(["Chrome", "Firefox"])
                    os_name = "Linux"
                    dev_type = "desktop"
                    
                elif scenario == "tor_night_anomaly":
                    loc = random.choice(UNUSUAL_CITIES)
                    dist = haversine_distance(state["last_location"]["lat"], state["last_location"]["lon"], loc["lat"], loc["lon"])
                    ip = f"192.0.2.{random.randint(10, 250)}"
                    dev_id = f"DEV-ANON-{random.randint(100, 999)}"
                    login_success = 0 # Blocked attempt
                    failed_attempts = random.randint(3, 7)
                    is_new_device = 1
                    is_new_location = 1
                    distance_km = dist
                    minutes_since_prev = random.randint(60, 400)
                    impossible_travel = 0
                    browser = "Unknown/TorBrowser"
                    os_name = "Linux"
                    dev_type = "desktop"
                    
                else: # failed_burst
                    loc = u["base_location"]
                    dist = 0.0
                    ip = f"198.51.100.{random.randint(10, 200)}"
                    dev_id = state["last_device"]
                    login_success = 0
                    failed_attempts = random.randint(5, 12)
                    is_new_device = 0
                    is_new_location = 0
                    distance_km = dist
                    minutes_since_prev = random.randint(10, 30)
                    impossible_travel = 0
                    browser = "Chrome"
                    os_name = "Windows 11"
                    dev_type = "laptop"
                    
            else: # NORMAL LOGIN
                label = "normal"
                loc = u["base_location"]
                prev_loc = state["last_location"]
                # slight local jitter in distance (0 to 15 km)
                dist = round(random.uniform(0.0, 12.5), 1)
                ip = state["last_ip"]
                dev_id = random.choice(u["known_devices"])
                dev_idx = 0 if dev_id == u["known_devices"][0] else 1
                dev_config = u["device_configs"][dev_idx]
                
                # Normal logins are mostly successful with 0 or 1 accidental mistype
                login_success = 1 if random.random() < 0.96 else 0
                failed_attempts = 1 if (login_success == 0 or random.random() < 0.08) else 0
                is_new_device = 0
                is_new_location = 0
                distance_km = dist
                minutes_since_prev = minutes_gap
                impossible_travel = 0
                browser = dev_config["browser"]
                os_name = dev_config["os"]
                dev_type = dev_config["type"]
                
            # Update user state
            state["last_login_time"] = current_time
            state["last_location"] = loc
            state["last_device"] = dev_id
            state["last_ip"] = ip
            
            records.append({
                "event_id": event_id,
                "user_id": u_id,
                "timestamp": time_str,
                "ip_address": ip,
                "country": loc["country"],
                "city": loc["city"],
                "device_id": dev_id,
                "device_type": dev_type,
                "browser": browser,
                "operating_system": os_name,
                "login_success": login_success,
                "failed_attempts": failed_attempts,
                "is_new_device": is_new_device,
                "is_new_location": is_new_location,
                "distance_from_usual_location_km": distance_km,
                "minutes_since_previous_login": minutes_since_prev,
                "impossible_travel": impossible_travel,
                "label": label
            })
            
    df = pd.DataFrame(records)
    return df


def main():
    os.makedirs("backend/data/raw", exist_ok=True)
    os.makedirs("backend/data/processed", exist_ok=True)
    
    print("--- Starting Synthetic Data Generation ---")
    email_df = generate_emails(NUM_EMAILS)
    raw_email_path = "backend/data/raw/synthetic_emails.csv"
    email_df.to_csv(raw_email_path, index=False)
    print(f"Saved {len(email_df)} emails to {raw_email_path}")
    print(f"Email label distribution:\n{email_df['label'].value_counts()}\n")
    
    login_df = generate_logins(NUM_LOGINS, email_df=email_df)
    raw_login_path = "backend/data/raw/synthetic_login_events.csv"
    login_df.to_csv(raw_login_path, index=False)
    print(f"Saved {len(login_df)} login events to {raw_login_path}")
    print(f"Login label distribution:\n{login_df['label'].value_counts()}\n")
    
    print("Synthetic data generation finished successfully!")

if __name__ == "__main__":
    main()
