"""
generate_and_ingest_policies.py
--------------------------------
Creates 5 realistic company policy documents (PDF + CSV) and ingests them
into the Archivum AI knowledge base. Run from d:\\giganigga root.
"""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

DOCS_DIR = Path("data/docs")
DOCS_DIR.mkdir(parents=True, exist_ok=True)


# ─────────────────────────────────────────────────────────────────────────────
# Helper: build PDF from sections
# ─────────────────────────────────────────────────────────────────────────────
def make_pdf(filename: str, sections: list[tuple[str, str]]):
    """sections = list of (heading, body_text)"""
    out = DOCS_DIR / filename
    doc = SimpleDocTemplate(str(out), pagesize=letter,
                            leftMargin=54, rightMargin=54,
                            topMargin=54, bottomMargin=54)
    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("H1", parent=styles["Heading1"], fontSize=18,
                        textColor=colors.HexColor("#1A365D"), spaceAfter=12)
    h2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=13,
                        textColor=colors.HexColor("#2B6CB0"), spaceAfter=8, spaceBefore=14)
    body = ParagraphStyle("Body", parent=styles["Normal"], fontSize=10,
                           leading=15, textColor=colors.HexColor("#2D3748"), spaceAfter=8)

    story = []
    first = True
    for heading, text in sections:
        if first:
            story.append(Paragraph(heading, h1))
            first = False
        else:
            story.append(Paragraph(heading, h2))
        for line in text.strip().split("\n"):
            line = line.strip()
            if line:
                story.append(Paragraph(line, body))
        story.append(Spacer(1, 8))

    doc.build(story)
    print(f"[CREATED] {out}  ({out.stat().st_size} bytes)")
    return str(out)


# ─────────────────────────────────────────────────────────────────────────────
# Doc 1 – HR_Leave_Policy_2026.pdf
# ─────────────────────────────────────────────────────────────────────────────
def doc1_leave_policy():
    return make_pdf("HR_Leave_Policy_2026.pdf", [
        ("HR Leave & Absence Policy 2026 — NovaTech Pvt. Ltd.",
         "Document ID: NT-HR-LEAVE-2026 | Effective: 01 January 2026 | Owner: People Operations"),

        ("1. Annual Leave (Paid Time Off)",
         """Every permanent employee is entitled to 24 days of paid annual leave per calendar year.
Leave accrues at a rate of 2 days per month starting from the first month of employment.
Unused leave can be carried forward up to a maximum of 12 days to the following calendar year.
Leave balance reports are accessible through the HR self-service portal at hr.novatech.internal.
Employees must apply for annual leave at least 5 business days in advance for 3 or fewer days.
For leave exceeding 5 consecutive days, a minimum of 15 business days advance notice is required."""),

        ("2. Sick Leave",
         """Every employee is entitled to 12 days of paid sick leave per calendar year.
Sick leave does not carry forward to the following year and cannot be encashed.
For sick leave exceeding 3 consecutive days, a registered medical certificate must be submitted to HR within 2 working days of return.
Sick leave taken immediately before or after a public holiday requires a medical certificate regardless of duration.
The Company provides access to an Employee Assistance Programme (EAP) for mental health support."""),

        ("3. Maternity Leave",
         """Female employees who have completed at least 12 months of continuous service are entitled to 26 weeks of fully paid maternity leave.
Employees must notify HR at least 8 weeks before the expected date of childbirth.
Maternity leave can commence up to 8 weeks before the expected date of delivery.
After the 26-week paid period, an additional 12 weeks of unpaid extended maternity leave may be applied for, subject to management approval.
A child adoption benefit of 16 weeks paid leave is also available for primary caregivers who adopt a child below the age of 5 years."""),

        ("4. Paternity Leave",
         """Male employees and secondary caregivers are entitled to 10 working days of paid paternity leave.
Paternity leave must be taken within 6 months of the child's birth or adoption.
Paternity leave is available for biological, adopted, and foster children.
Employees must apply for paternity leave at least 4 weeks in advance where possible."""),

        ("5. Bereavement Leave",
         """Employees are entitled to 5 days of paid bereavement leave on the death of an immediate family member.
Immediate family members are defined as: spouse or domestic partner, child, parent, sibling, and in-laws (mother-in-law, father-in-law).
For the death of a grandparent, aunt, uncle, or cousin, 2 days of paid bereavement leave is provided.
Bereavement leave must be taken within 14 days of the bereavement event.
Additional unpaid leave may be granted on a case-by-case basis as approved by the department head."""),

        ("6. Public Holidays",
         """NovaTech Pvt. Ltd. observes all 13 declared national public holidays in addition to 3 regional optional holidays.
If an employee is required to work on a public holiday, they will be compensated with 2 days of compensatory time off, to be used within 60 days.
The official holiday schedule is published on the HR portal by 15 December of the preceding year."""),

        ("7. Leave Without Pay (LOP)",
         """Leave Without Pay (LOP) may be granted at the sole discretion of the department head and HR Director.
Continuous LOP shall not exceed 90 days in a calendar year.
LOP directly affects statutory benefits calculations, variable pay, and annual increment eligibility.
Employees on LOP for more than 30 days must confirm their intent to return in writing before recommencing duties."""),
    ])


# ─────────────────────────────────────────────────────────────────────────────
# Doc 2 – IT_Security_and_Equipment_Policy_2026.pdf
# ─────────────────────────────────────────────────────────────────────────────
def doc2_it_security():
    return make_pdf("IT_Security_and_Equipment_Policy_2026.pdf", [
        ("IT Security & Equipment Policy 2026 — NovaTech Pvt. Ltd.",
         "Document ID: NT-IT-SEC-2026 | Effective: 01 February 2026 | Owner: Information Security"),

        ("1. Device & Equipment Allocation",
         """All permanent employees are issued a company laptop within 3 business days of their joining date.
Engineering and developer roles receive a 16-inch MacBook Pro M3 Max with 64GB RAM and 2TB SSD.
Design roles receive a MacBook Pro 14-inch M3 Pro with 36GB RAM and 512GB SSD.
Operations and administrative roles receive a MacBook Air 15-inch M2 with 16GB RAM and 256GB SSD.
Laptops are refreshed on a 24-month cycle for engineering roles and a 36-month cycle for all other roles.
Lost or stolen devices must be reported to IT Security within 2 hours via the incident hotline at +91-80-4455-6677."""),

        ("2. Password & Authentication Policy",
         """All corporate passwords must be at least 16 characters and include uppercase letters, lowercase letters, numbers, and a special character.
Passwords must be changed every 90 days. Password reuse is prohibited for the last 12 cycles.
Multi-Factor Authentication (MFA) using Google Authenticator or a hardware YubiKey token is mandatory for all corporate accounts.
Hardware YubiKey tokens are strictly required for all AWS console access, GitHub Enterprise, and Supabase production access.
Single Sign-On (SSO) via Okta is the only approved authentication method for third-party SaaS applications.
Sharing of corporate credentials with any third party, including contractors, is strictly prohibited and subject to immediate disciplinary action."""),

        ("3. Network & VPN Usage",
         """The use of the company VPN (NovaTech Secure Connect) is mandatory when accessing any internal resources or cloud infrastructure from outside company premises.
Employees must not connect to public or untrusted Wi-Fi networks without an active VPN session.
All corporate traffic is routed through a Zero Trust Network Architecture (ZTNA) and monitored for anomalies 24/7.
Personal devices (BYOD) may only connect to the isolated Guest Wi-Fi network and not to the corporate LAN or VPN."""),

        ("4. Data Classification & Handling",
         """Data is classified into four tiers: Public, Internal, Confidential, and Restricted.
Confidential data (e.g. source code, financial reports, customer PII) must never be stored on personal devices, personal cloud accounts, or USB drives.
Restricted data (e.g. executive board communications, cryptographic keys, M&A data) requires explicit CISO approval before any sharing.
All confidential and restricted data at rest must be encrypted using AES-256 encryption.
Accidental data exposure must be reported to the Data Protection Officer (DPO) at dpo@novatech.in within 1 hour of discovery."""),

        ("5. Software & Application Policy",
         """Only software from the approved NovaTech Software Catalogue may be installed on company-issued devices.
The approved catalogue is maintained at it.novatech.internal/software-catalogue.
Requests for unlisted software must be submitted to IT via the ticketing system and approved within 5 business days.
The installation of cryptocurrency mining software, remote access tools (other than those approved by IT), or peer-to-peer sharing applications is strictly prohibited and may result in immediate termination.
Browser extensions must be approved by IT Security before installation on corporate browsers."""),

        ("6. Incident Response",
         """All suspected security incidents (phishing, malware, unauthorized access) must be reported immediately via it-security@novatech.in or via Slack #security-incidents.
IT Security will acknowledge all reports within 30 minutes during business hours and 2 hours outside business hours.
Employees must not attempt to remediate a security incident independently without guidance from the IT Security team.
The IT Security team conducts mandatory annual cybersecurity training for all employees. Non-completion by the training deadline results in temporary suspension of VPN and cloud console access."""),
    ])


# ─────────────────────────────────────────────────────────────────────────────
# Doc 3 – Employee_Code_of_Conduct_2026.pdf
# ─────────────────────────────────────────────────────────────────────────────
def doc3_code_of_conduct():
    return make_pdf("Employee_Code_of_Conduct_2026.pdf", [
        ("Employee Code of Conduct 2026 — NovaTech Pvt. Ltd.",
         "Document ID: NT-COC-2026 | Effective: 01 January 2026 | Owner: Legal & Compliance"),

        ("1. Professionalism & Workplace Behaviour",
         """All employees are expected to maintain a high standard of professionalism, integrity, and mutual respect in all interactions.
Disruptive, abusive, harassing, or discriminatory behaviour in person or via digital communication is a violation of this policy and is grounds for disciplinary action up to and including termination.
Dress code: Business casual attire is expected on client-facing days. On internal working days, a smart casual standard applies.
Work hours: Core hours are 10:00 AM to 4:30 PM Monday through Friday. Flexible working arrangements outside these hours may be agreed with line managers.
Employees are expected to maintain confidentiality of all company and client information at all times, including after their employment ends."""),

        ("2. Conflict of Interest",
         """Employees must disclose any potential conflict of interest to their manager and HR within 5 business days of its arising.
A conflict of interest includes: holding a financial interest in a competitor, supplier, or client; or a personal relationship with a direct report, vendor contact, or recruiting candidate.
Secondary employment or freelance work for clients, competitors, or suppliers of NovaTech is prohibited without written approval from the HR Director and Legal department.
Employees may not solicit or accept gifts, hospitality, or payments from clients, vendors, or business partners that exceed INR 3,000 in aggregate value per financial year without written disclosure."""),

        ("3. Anti-Bribery & Anti-Corruption",
         """NovaTech maintains a zero-tolerance policy for bribery and corruption in all forms.
Employees must not offer, promise, give, request, or accept bribes or corrupt payments in any form, whether cash, gifts, services, travel, or other benefits.
All facilitation payments, even in jurisdictions where they may be customary, are prohibited.
Violations of this policy must be reported confidentially via the NovaTech Ethics Hotline: 1800-555-NOVA (1800-555-6682), which operates 24/7 and guarantees anonymity.
Confirmed violations will be investigated and may result in immediate termination and referral to law enforcement authorities."""),

        ("4. Use of Company Resources",
         """Company assets including laptops, mobile phones, software licences, vehicles, and office supplies are provided strictly for business purposes.
Incidental personal use of company devices is permitted provided it does not: consume excessive bandwidth, expose the company to legal liability, or interfere with work performance.
Company credit cards and expense accounts may only be used for pre-approved business expenses.
Personal deliveries, parcels, or purchases must not be made to the company's registered office address without prior approval from the Office Manager."""),

        ("5. Social Media & Public Communications",
         """Employees may not make statements on social media or in public forums that represent the official views of NovaTech without written approval from the Communications team.
Employees sharing personal opinions related to NovaTech's industry, competitors, or clients must include a clear disclaimer: 'Views are my own and do not represent NovaTech.'
Sharing confidential company information, source code, internal communications, product roadmaps, or financial data on any external platform is a serious disciplinary offence and may constitute a breach of the employee's non-disclosure agreement.
All media enquiries from journalists or press agencies must be forwarded immediately to communications@novatech.in."""),

        ("6. Disciplinary Procedures",
         """Minor violations (first offence): Written warning issued by line manager, documented in employee's HR record.
Moderate violations or repeat minor violations: Final written warning issued by HR Director with a Performance Improvement Plan (PIP) of 30–60 days.
Serious violations (fraud, harassment, data theft, physical violence, or disclosure of confidential information): Summary dismissal without notice period.
All disciplinary proceedings will be conducted in accordance with the principles of natural justice, ensuring the employee has the opportunity to present their case.
Employees have the right to appeal any disciplinary decision to the Chief People Officer within 10 working days of the decision."""),
    ])


# ─────────────────────────────────────────────────────────────────────────────
# Doc 4 – Financial_Expense_Reimbursement_Policy_2026.pdf
# ─────────────────────────────────────────────────────────────────────────────
def doc4_expense_policy():
    return make_pdf("Financial_Expense_Reimbursement_Policy_2026.pdf", [
        ("Financial Expense & Reimbursement Policy 2026 — NovaTech Pvt. Ltd.",
         "Document ID: NT-FIN-EXP-2026 | Effective: 01 April 2026 | Owner: Finance"),

        ("1. Travel Expense Limits",
         """All business travel must be pre-approved by the employee's direct manager and Finance at least 5 business days before the travel date.
Domestic flights: Economy class only for flights under 4 hours. Economy Plus permitted for flights between 4 and 6 hours.
International flights: Economy Plus for flights under 8 hours. Business class is approved for flights exceeding 8 hours for Band 5 and above employees.
Hotel accommodation: Maximum of INR 7,500 per night in Tier 1 cities (Mumbai, Delhi, Bangalore, Hyderabad). Maximum of INR 5,000 per night in Tier 2 cities.
For international travel, hotel accommodation is capped at USD 200 per night.
All hotel bookings must be made via the approved corporate travel portal (travel.novatech.internal) or through the designated travel management company."""),

        ("2. Daily Meal & Per Diem Rates",
         """Domestic per diem for meals and incidentals is INR 2,500 per full travel day.
International per diem for meals and incidentals is USD 85 per full travel day.
Alcohol is not reimbursable under any circumstances as a meal expense.
Receipts are mandatory for individual meal claims exceeding INR 500.
Team meals or client entertainment expenses up to INR 15,000 may be approved by the direct manager. Amounts above INR 15,000 require VP-level or above approval.
Per diem is not payable for travel days that begin after 7:00 PM or end before 9:00 AM."""),

        ("3. Local Transportation",
         """Taxi and rideshare (Uber, Ola) fares for business travel are fully reimbursable with digital receipts.
Personal vehicle usage is reimbursed at a rate of INR 12 per kilometre for the first 100 km and INR 9 per kilometre thereafter, per trip.
Toll and parking charges are reimbursable with receipts.
Luxury vehicle categories (Uber Black, Ola Prime SUV) are not reimbursable except for VP and above levels or explicit client-facing situations.
Auto-rickshaw and public transport fares are reimbursable without receipts up to INR 500 per day."""),

        ("4. Learning & Development Expenses",
         """Each employee has an annual Learning & Development (L&D) budget of INR 75,000 (approximately $900) per financial year.
This budget covers: online courses, professional certifications, conference registrations, technical books, and approved workshops.
Reimbursements require submission of proof of completion (course certificate or attendance confirmation) along with the receipt.
L&D expenses above INR 50,000 for a single item require pre-approval from the L&D Manager and the employee's VP.
The L&D budget does not roll over to the following financial year. Unused budget is forfeited on 31 March.
NovaTech will sponsor professional certification exam fees for AWS, GCP, Azure, PMP, and CFA up to 3 attempts per year."""),

        ("5. Mobile & Internet Allowance",
         """Employees in roles requiring regular business calls (Sales, Business Development, Customer Success, Engineering Managers) are eligible for a monthly mobile data allowance of INR 1,500.
All employees who are on an approved permanent remote or hybrid work arrangement receive a monthly home internet reimbursement of INR 2,000 (approximately $24).
Reimbursements are processed automatically via payroll upon submission of a copy of the internet bill each month.
One-time home office setup allowance of INR 20,000 is available to employees transitioning to a permanent remote arrangement, subject to HR and Finance approval."""),

        ("6. Expense Submission & Processing",
         """All expense claims must be submitted via the Expenses module in Workday (workday.novatech.internal) within 30 days of incurring the expense.
Claims submitted after 60 days of the expense date will be rejected without exception.
Reimbursements are processed within 7 working days of approval for claims under INR 25,000, and within 15 working days for larger claims.
Any expense claim found to be fraudulent or deliberately inflated will result in disciplinary action including termination and potential criminal prosecution."""),
    ])


# ─────────────────────────────────────────────────────────────────────────────
# Doc 5 – NovaTech_Employee_Benefits_Matrix.csv
# ─────────────────────────────────────────────────────────────────────────────
def doc5_benefits_csv():
    out = DOCS_DIR / "Employee_Benefits_Matrix_2026.csv"
    rows = [
        ["Benefit", "Eligibility", "Value", "Details"],
        ["Health Insurance (Employee)", "All permanent employees from day 1", "INR 5,00,000 cover per year", "Cashless at 5,000+ network hospitals. Covers: hospitalisation, ICU, surgery, specialist consultations."],
        ["Health Insurance (Family)", "After 6 months of service", "INR 5,00,000 cover (shared with employee)", "Covers spouse and up to 2 dependent children below age 25."],
        ["Dental Insurance", "All permanent employees from day 1", "INR 25,000 per year", "Covers routine cleanings (2x/year), fillings, extractions, and root canals. Cosmetic dentistry excluded."],
        ["Vision Insurance", "All permanent employees from day 1", "INR 10,000 per year", "Covers comprehensive eye exam (1x/year), prescription glasses or contact lenses."],
        ["Term Life Insurance", "All permanent employees from day 1", "5x Annual CTC (up to INR 1 Crore)", "Group term life insurance. Accidental death and disability cover included."],
        ["Provident Fund (PF)", "All employees under Indian labour law", "12% of Basic Salary (employer matched)", "Employee contributes 12% of basic salary. Employer matches 12%. Managed by EPFO."],
        ["Gratuity", "After 5 years of continuous service", "As per Payment of Gratuity Act 1972", "Calculated as: 15 days salary × years of service. Payable at resignation, retirement, or death."],
        ["Annual Performance Bonus", "Permanent employees with rating >= 3/5", "Up to 20% of Annual CTC", "Payout in April each year. Prorated for employees joining mid-year. Rating < 3 receives no bonus."],
        ["Employee Stock Options (ESOPs)", "Senior Engineer and above (Band 4+)", "Varies by band and performance", "Vest over 4 years (25% per year) after a 1-year cliff. Strike price set at grant date fair market value."],
        ["Annual L&D Budget", "All permanent employees", "INR 75,000 per financial year", "Courses, certifications, conferences, books. Requires proof of completion. Does not roll over."],
        ["Home Internet Allowance", "Permanent remote/hybrid employees", "INR 2,000 per month", "Reimbursed via payroll upon submission of monthly internet bill."],
        ["Mobile Allowance", "Sales, BD, CS, EM roles", "INR 1,500 per month", "Added to monthly payroll. No receipt required."],
        ["Gym & Wellness Reimbursement", "All permanent employees", "INR 6,000 per year (INR 500/month)", "Covers gym memberships, yoga, swimming, sports club fees. Receipt required."],
        ["Meal Vouchers (Sodexo)", "All permanent employees at office", "INR 3,000 per month", "Loaded on Sodexo card. Usable at 1,500+ partner restaurants and online food platforms."],
        ["Work From Home Stipend (One-Time)", "Employees switching to permanent remote", "INR 20,000 one-time", "For ergonomic chair, desk, monitor, webcam, or other home office setup. Receipt required."],
        ["NPS Corporate Contribution", "Employees opting into NPS scheme", "INR 6,000 per year from employer", "Employer contributes INR 500/month to National Pension System Tier-1 account."],
        ["Relocation Assistance", "Employees relocating >250 km for role", "Up to INR 1,00,000 one-time", "Covers moving company, security deposit support, temporary accommodation (up to 15 days)."],
        ["Sabbatical Leave", "Employees with 5+ years of tenure", "Up to 3 months unpaid", "Subject to management approval. Benefits maintained during sabbatical. Guaranteed role on return."],
        ["Employee Referral Bonus", "All permanent employees", "INR 25,000 per successful referral", "Paid after the referred employee completes 6 months. No cap on number of referrals."],
    ]
    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(rows)
    print(f"[CREATED] {out}  ({out.stat().st_size} bytes)")
    return str(out)


# ─────────────────────────────────────────────────────────────────────────────
# Ingest all documents into Archivum
# ─────────────────────────────────────────────────────────────────────────────
def ingest_all(files: list[str]):
    from src.ingestion import ingest_document

    total = 0
    for f in files:
        try:
            doc_name = Path(f).name
            result = ingest_document(f, doc_name)
            n = result.get("chunks_created", 0)
            total += n
            print(f"  [OK]  {doc_name}  ->  {n} chunks ingested")
        except Exception as e:
            print(f"  [FAIL]  {Path(f).name}  ->  FAILED: {e}")

    print(f"\n[DONE] Total new chunks indexed: {total}")


if __name__ == "__main__":
    print("=" * 60)
    print("NovaTech Policy Document Generator & Ingestion Script")
    print("=" * 60)

    files = [
        doc1_leave_policy(),
        doc2_it_security(),
        doc3_code_of_conduct(),
        doc4_expense_policy(),
        doc5_benefits_csv(),
    ]

    print(f"\nCreated {len(files)} documents. Now ingesting into Archivum AI ...\n")
    ingest_all(files)

    print("\n" + "=" * 60)
    print("READY TO TEST! Start the server with:")
    print("  python run_server.py")
    print("\nThen open http://localhost:8000 and ask these questions:")
    print()
    print("  1. How many days of paid annual leave do employees get?")
    print("  2. What laptop do engineering roles receive?")
    print("  3. What is the password minimum length policy?")
    print("  4. What happens if an employee commits bribery?")
    print("  5. What is the domestic per diem rate for international travel?")
    print("  6. What is the annual L&D budget for employees?")
    print("  7. How much is the home internet reimbursement per month?")
    print("  8. What is the health insurance cover amount for employees?")
    print("  9. How many days of maternity leave does NovaTech offer?")
    print(" 10. What is the employee referral bonus amount?")
    print()
    print("  (Out-of-scope to test refusal):")
    print("  11. What is the capital of France?")
    print("  12. Who won the IPL 2024?")
    print("=" * 60)
