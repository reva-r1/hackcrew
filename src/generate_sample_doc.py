import os
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak

def create_sample_hr_policy(output_path: str):
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=22,
        leading=26,
        textColor=colors.HexColor('#1A365D'),
        spaceAfter=15
    )
    h2_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontSize=15,
        leading=18,
        textColor=colors.HexColor('#2B6CB0'),
        spaceBefore=12,
        spaceAfter=8
    )
    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#2D3748'),
        spaceAfter=10
    )

    story = []

    # Page 1: Introduction & Company Overview
    story.append(Paragraph("Enterprise Global Technologies — Employee Handbook & HR Policy 2026", title_style))
    story.append(Paragraph("Document Reference: EGT-POL-2026-V1.4 | Effective Date: January 1, 2026", body_style))
    story.append(Spacer(1, 15))
    story.append(Paragraph("1. Code of Conduct & Workplace Ethics", h2_style))
    story.append(Paragraph(
        "At Enterprise Global Technologies, we are dedicated to maintaining the highest standards of integrity, mutual respect, and professional accountability. All full-time employees, contractors, and interns must adhere to our zero-tolerance policy regarding discrimination, harassment, and conflicts of interest. Violations of the code of conduct will lead to disciplinary proceedings up to and including termination of employment.",
        body_style
    ))
    story.append(Paragraph(
        "Information security and confidentiality are core responsibilities of every team member. Proprietary code, client financial data, and architectural designs must be encrypted at rest and in transit. Sharing confidential credentials or system access keys is strictly prohibited.",
        body_style
    ))
    story.append(PageBreak())

    # Page 2: Working Hours & Attendance
    story.append(Paragraph("2. Working Hours and Time Tracking", h2_style))
    story.append(Paragraph(
        "Standard core working hours are Monday through Friday from 9:30 AM to 6:30 PM local time, with a mandatory 60-minute lunch break. Flexible core working hours allow team members to commence between 8:30 AM and 10:30 AM upon manager approval, provided they complete 40 core operational hours weekly.",
        body_style
    ))
    story.append(Paragraph(
        "Attendance and timesheets must be logged on the HR portal (Workday Pulse) by the last Friday of each calendar month. Overtime compensation is applicable only to non-exempt roles and requires pre-approval from the functional director.",
        body_style
    ))
    story.append(PageBreak())

    # Page 3: Leave and Absence Policy
    story.append(Paragraph("3. Annual Paid Leave & Absence Entitlements", h2_style))
    story.append(Paragraph(
        "Employees are entitled to 24 days of Earned Annual Paid Leave (PL) accrued at 2 days per completed month of service. A maximum of 10 unused PL days can be carried forward to the subsequent calendar year; any remaining excess beyond 10 days will lapse on December 31.",
        body_style
    ))
    story.append(Paragraph(
        "Casual and Sick Leave (CSL) is credited at 12 days per year on January 1. CSL cannot be encashed or carried forward. Medical leave exceeding 3 consecutive business days requires a valid practitioner certificate submitted within 48 hours of return to duty.",
        body_style
    ))
    story.append(Paragraph(
        "Parental leave provides 26 weeks of fully paid maternity leave for primary caregivers and 4 weeks of fully paid paternity leave for secondary caregivers, accessible within the first twelve months following childbirth or formal adoption.",
        body_style
    ))
    story.append(PageBreak())

    # Page 4: Health Insurance & Medical Benefits
    story.append(Paragraph("4. Comprehensive Group Health Insurance", h2_style))
    story.append(Paragraph(
        "Enterprise Global Technologies provides comprehensive Group Mediclaim Insurance (GMC) covering the employee, spouse, and up to two dependent children with a cumulative annual sum insured of ₹10,00,000. Coverage includes pre-existing conditions with no waiting period.",
        body_style
    ))
    story.append(Paragraph(
        "An optional parental insurance top-up is available during the annual November open-enrollment window, allowing coverage for dependent parents up to ₹5,00,000 with a 20% co-pay clause on hospitalization claims.",
        body_style
    ))
    story.append(Paragraph(
        "An annual wellness reimbursement of ₹15,000 is available per employee for gym memberships, preventive health checkups, and mental health counseling sessions through our partnered network.",
        body_style
    ))
    story.append(PageBreak())

    # Page 5: Travel & Business Expenses
    story.append(Paragraph("5. Business Travel and Entertainment Policy", h2_style))
    story.append(Paragraph(
        "All business travel must be booked via the internal TravelDesk portal at least 14 days in advance for domestic flights and 28 days in advance for international itineraries. Domestic flights under 4 hours are economy class; flights over 8 continuous hours qualify for premium economy or business tier with Vice President authorization.",
        body_style
    ))
    story.append(Paragraph(
        "Daily meal allowance (per diem) for domestic metro travel (Bangalore, Mumbai, Delhi-NCR) is capped at ₹2,500 per day. For tier-2 cities, the limit is ₹1,800 per day. Itemized receipts are mandatory for all expense filings submitted on Expensify within 30 days of travel conclusion.",
        body_style
    ))
    story.append(PageBreak())

    # Page 6: Performance Appraisal & Promotions
    story.append(Paragraph("6. Performance Appraisals, Bonuses, and Growth", h2_style))
    story.append(Paragraph(
        "Annual performance cycles run from January 1 to December 31, with mid-year check-ins in July and formal reviews in December. Performance ratings range from Level 1 (Unsatisfactory) to Level 5 (Exceptional).",
        body_style
    ))
    story.append(Paragraph(
        "Annual discretionary bonuses and merit-based salary increments are disbursed in the March payroll cycle. To be eligible for bonus consideration, an employee must have completed a minimum of 6 months of continuous service prior to October 1 of the appraisal year.",
        body_style
    ))
    story.append(PageBreak())

    # Page 7: Learning & Development Stipend
    story.append(Paragraph("7. Learning & Development Stipend and Certifications", h2_style))
    story.append(Paragraph(
        "Every full-time employee receives an annual Learning & Development (L&D) allowance of ₹75,000 per financial year. This allowance may be utilized for technical certifications (e.g. AWS, GCP, CKA), professional conferences, university executive courses, and specialized technical books.",
        body_style
    ))
    story.append(Paragraph(
        "Prior written approval from the engineering or department manager is mandatory before purchasing courses. Receipts and proof of completion must be uploaded within 15 calendar days to receive reimbursement.",
        body_style
    ))
    story.append(PageBreak())

    # Page 8: Equipment and Hardware Allocation
    story.append(Paragraph("8. IT Equipment Allocation and Refresh Cycle", h2_style))
    story.append(Paragraph(
        "Upon onboarding, standard engineering staff are provisioned with an Apple MacBook Pro 16-inch (M3 Pro, 36GB RAM) or a Dell XPS 15 (32GB RAM). Equipment remains the property of Enterprise Global Technologies and must be returned upon cessation of employment.",
        body_style
    ))
    story.append(Paragraph(
        "Hardware refreshes occur automatically on a 36-month cycle. Employees may purchase their depreciated laptop at nominal fair-market salvage value at the end of the 3-year term.",
        body_style
    ))
    story.append(PageBreak())

    # Page 9: Relocation Assistance
    story.append(Paragraph("9. Domestic and International Relocation Support", h2_style))
    story.append(Paragraph(
        "Employees relocating at the company's request to a different base location are eligible for relocation assistance. Domestic transfers include one-way flight tickets for employee and immediate family, 14 days of corporate guest house stay, and moving expenses up to ₹1,20,000.",
        body_style
    ))
    story.append(Paragraph(
        "A 12-month retention clawback clause applies: if an employee voluntarily resigns within 12 months of receiving relocation reimbursement, the full relocation sum must be reimbursed to the company upon exit settlement.",
        body_style
    ))
    story.append(PageBreak())

    # Page 10: Referral Bonus Program
    story.append(Paragraph("10. Employee Referral Bonus Scheme", h2_style))
    story.append(Paragraph(
        "Our employee referral program incentivizes staff to recommend qualified candidates. Referral rewards are structured as follows: ₹50,000 for Senior Engineer (L4/L5), ₹1,00,000 for Staff/Principal Engineer (L6+), and ₹1,50,000 for Director or Executive levels.",
        body_style
    ))
    story.append(Paragraph(
        "The referral bonus is disbursed in two equal tranches: 50% upon the candidate's successful joining date, and the remaining 50% upon the candidate successfully completing their 90-day probationary period.",
        body_style
    ))
    story.append(PageBreak())

    # Page 11: Intellectual Property & Inventions
    story.append(Paragraph("11. Proprietary Information and Inventions Agreement (PIIA)", h2_style))
    story.append(Paragraph(
        "All patentable inventions, software architectures, algorithms, and documentation developed during the tenure of employment, whether on company premises or during remote hours using company resources, are the sole exclusive intellectual property of Enterprise Global Technologies.",
        body_style
    ))
    story.append(Paragraph(
        "Employees are prohibited from contributing to external open-source repositories during company working hours without explicit written sign-off from the Open Source Review Board (OSRB).",
        body_style
    ))
    story.append(PageBreak())

    # Page 12: Remote Work & WFH Internet Allowance (Exact spec match!)
    story.append(Paragraph("12. Remote Work Policy and Internet Allowance", h2_style))
    story.append(Paragraph(
        "Enterprise Global Technologies operates under a hybrid-first model allowing eligible employees to work remotely up to four days per week subject to managerial alignment. Employees working remotely are eligible for an internet allowance of ₹1,500 per month, reimbursed quarterly upon submission of valid service provider invoices.",
        body_style
    ))
    story.append(Paragraph(
        "A one-time home office ergonomic setup grant of ₹25,000 is granted to all new hires to purchase ergonomic desks, monitors, and chairs. Claims must be submitted within the first 60 days of employment.",
        body_style
    ))
    story.append(PageBreak())

    # Page 13: Reimbursement Processing Cycle
    story.append(Paragraph("13. Expense Reimbursement Guidelines & Schedules", h2_style))
    story.append(Paragraph(
        "Reimbursement is processed quarterly upon submission of utility bills and approved expense reports via the Concur finance portal. Expense reports submitted before the 15th of the quarter-end month are paid out alongside the regular salary disbursement.",
        body_style
    ))
    story.append(Paragraph(
        "All submitted bills must clearly indicate the employee's registered residential address and tax identification number. Claims older than 90 days from the invoice date are automatically rejected.",
        body_style
    ))
    story.append(PageBreak())

    # Page 14: Separation, Resignation, and Notice Periods
    story.append(Paragraph("14. Separation, Resignation, and Notice Periods", h2_style))
    story.append(Paragraph(
        "Confirmed employees wishing to resign must serve a mandatory notice period of 60 calendar days (90 days for Engineering Leads, Managers, and Directors). Notice period buyout is solely at the company's discretion and requires Business Unit Head approval.",
        body_style
    ))
    story.append(Paragraph(
        "Full and final settlement (FnF), including leave encashment, gratuity calculation, and issuance of experience certificates, is completed within 30 days of the last working day following IT asset clearance.",
        body_style
    ))
    story.append(PageBreak())

    # Page 15: Grievance Redressal and POSH
    story.append(Paragraph("15. Grievance Redressal and POSH Committee", h2_style))
    story.append(Paragraph(
        "We are committed to providing a safe work environment free from sexual harassment and retaliation. The Internal Complaints Committee (ICC) constitutes senior leadership and an independent external NGO representative under the POSH Act.",
        body_style
    ))
    story.append(Paragraph(
        "Grievances can be reported confidentially to ethics@enterprise-global.com. All inquiries are conducted with strict confidentiality and completed within 30 working days.",
        body_style
    ))

    doc.build(story)
    print(f"Created sample PDF document at: {output_path}")

if __name__ == "__main__":
    create_sample_hr_policy("data/docs/HR_Policy_2026.pdf")
