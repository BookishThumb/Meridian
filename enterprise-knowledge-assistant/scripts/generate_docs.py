import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

# Define target directory
OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "documents"))
os.makedirs(OUTPUT_DIR, exist_ok=True)

class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas to dynamically compute and print 'Page X of Y' or just 'Page X'
    and apply running headers and footers to the document.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_decorations(self, total_pages):
        self.saveState()
        
        # We assume doc properties are accessible, otherwise use defaults
        title = getattr(self, '_doc_title', 'Meridian Document')
        version = getattr(self, '_doc_version', 'v1.0')
        
        # Color palette - Dark Slate Blue
        primary_color = colors.HexColor("#1A365D")
        accent_color = colors.HexColor("#718096")
        
        # --- Running Header ---
        self.setFont('Helvetica-Bold', 8)
        self.setFillColor(primary_color)
        self.drawString(54, 750, "AnthraSync Technologies Pvt. Ltd.")
        
        self.setFont('Helvetica', 8)
        self.setFillColor(accent_color)
        self.drawRightString(558, 750, f"{title} | Version {version}")
        
        # Header Line
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.75)
        self.line(54, 742, 558, 742)
        
        # --- Running Footer ---
        self.line(54, 50, 558, 50)
        
        self.setFont('Helvetica', 8)
        self.setFillColor(accent_color)
        self.drawString(54, 38, "CONFIDENTIAL - INTERNAL USE ONLY")
        self.drawRightString(558, 38, f"Page {self._pageNumber} of {total_pages}")
        
        self.restoreState()

def generate_pdf(filename, title, version, content_schema):
    """
    Generates a professional multi-page PDF based on the provided schema.
    """
    pdf_path = os.path.join(OUTPUT_DIR, filename)
    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=72,
        bottomMargin=72
    )
    
    # Store title and version on canvas context
    def make_canvas_maker(title_str, version_str):
        class CustomCanvas(NumberedCanvas):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self._doc_title = title_str
                self._doc_version = version_str
        return CustomCanvas
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=colors.HexColor("#1A365D"),
        spaceAfter=15
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=10,
        leading=12,
        textColor=colors.HexColor("#4A5568"),
        spaceAfter=30
    )
    
    h1_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#2B6CB0"),
        spaceBefore=15,
        spaceAfter=10,
        keepWithNext=True
    )
    
    h2_style = ParagraphStyle(
        'SubsectionHeader',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#2D3748"),
        spaceBefore=10,
        spaceAfter=6,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#2D3748"),
        spaceAfter=10
    )
    
    bullet_style = ParagraphStyle(
        'Bullet',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        leftIndent=20,
        firstLineIndent=-10,
        textColor=colors.HexColor("#2D3748"),
        spaceAfter=6
    )

    story = []
    
    # Document Title Page Block
    story.append(Paragraph(title, title_style))
    story.append(Paragraph(f"Corporate Document Reference: {filename[:-4].replace('_', ' ')} | Version {version}", subtitle_style))
    story.append(Spacer(1, 10))
    
    # Build content from schema
    for item in content_schema:
        item_type = item.get("type")
        if item_type == "h1":
            story.append(Paragraph(item["text"], h1_style))
        elif item_type == "h2":
            story.append(Paragraph(item["text"], h2_style))
        elif item_type == "p":
            story.append(Paragraph(item["text"], body_style))
        elif item_type == "bullet":
            story.append(Paragraph(f"&bull; {item['text']}", bullet_style))
        elif item_type == "spacer":
            story.append(Spacer(1, item.get("height", 10)))
        elif item_type == "pagebreak":
            story.append(PageBreak())
        elif item_type == "table":
            t = Table(item["data"], colWidths=item.get("widths"))
            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2B6CB0")),
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,0), 9),
                ('BOTTOMPADDING', (0,0), (-1,0), 6),
                ('BACKGROUND', (0,1), (-1,-1), colors.HexColor("#F7FAFC")),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
                ('FONTNAME', (0,1), (-1,-1), 'Helvetica'),
                ('FONTSIZE', (0,1), (-1,-1), 9),
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('TOPPADDING', (0,1), (-1,-1), 5),
                ('BOTTOMPADDING', (0,1), (-1,-1), 5),
            ]))
            story.append(t)
            story.append(Spacer(1, 10))
            
    doc.build(story, canvasmaker=make_canvas_maker(title, version))
    print(f"Generated {pdf_path}")

def make_hr_policy():
    schema = [
        {"type": "h1", "text": "Section 1: General Code of Conduct"},
        {"type": "p", "text": "AnthraSync Technologies Pvt. Ltd. is committed to fostering a professional, inclusive, and collaborative working environment. All employees are expected to uphold the highest standards of integrity, respect, and professionalism in all interactions, both internal and external. Communication must always remain respectful, constructive, and aligned with company values."},
        {"type": "p", "text": "Our anti-harassment policy is strictly enforced. AnthraSync maintains a zero-tolerance policy for harassment of any kind, including sexual, verbal, or physical harassment, as well as discrimination based on race, gender, religion, age, sexual orientation, disability, or national origin. Employees are required to complete annual compliance training on anti-harassment and code of conduct expectations. Incidents must be reported immediately to the Human Resources department."},
        {"type": "spacer", "height": 10},
        
        {"type": "h1", "text": "Section 2: Comprehensive Leave Policy"},
        {"type": "p", "text": "To ensure work-life balance and support the physical and mental well-being of our staff, AnthraSync provides a comprehensive set of leave options. These allowances are calculated on a calendar year basis (January to December) and are prorated for employees joining mid-year."},
        {"type": "h2", "text": "2.1 Annual Leave Allowance"},
        {"type": "p", "text": "All permanent employees are entitled to 24 paid leaves per year. Annual leaves must be planned in advance and approved by the reporting manager to ensure business continuity. A maximum of 10 unused annual leaves can be carried forward to the next calendar year; any remaining excess unused leave will lapse at the end of the year."},
        {"type": "h2", "text": "2.2 Sick Leave Allowance"},
        {"type": "p", "text": "To support employees during illness, AnthraSync grants 12 days of sick leave per year. Sick leave is meant solely for medical recovery and cannot be accumulated or carried forward to the following year. For sick leave extending beyond three consecutive days, a valid medical certificate signed by a registered practitioner must be submitted to HR."},
        {"type": "h2", "text": "2.3 Parental Leave policies"},
        {"type": "p", "text": "AnthraSync supports new parents through generous parental leave provisions. Maternity leave is set at 26 weeks of fully paid leave, applicable for up to two children, in compliance with statutory regulations. Paternity leave is set at 4 weeks of fully paid leave, which can be taken in up to two blocks within the first six months of the child's birth or adoption. Written requests for parental leave should be submitted at least 8 weeks prior to the expected commencement date."},
        {"type": "pagebreak"},

        {"type": "h1", "text": "Section 3: Flexible Work & Remote Working"},
        {"type": "p", "text": "We recognize that flexible working conditions increase productivity and job satisfaction. Our Work From Home (WFH) policy allows employees to work remotely up to 2 days per week, subject to alignment with their team's deliverables and manager's approval. Core operating hours are 10:00 AM to 4:00 PM IST, during which employees must be accessible on Slack and email. The remaining 3 days of the week must be worked from the designated company office location."},
        {"type": "p", "text": "Employees working from home must ensure they have a quiet, dedicated workspace and a high-speed internet connection. The IT department will provision necessary hardware, but internet connectivity costs and utility management remain the responsibility of the employee, except where covered by corporate reimbursement allowances."},
        {"type": "spacer", "height": 10},

        {"type": "h1", "text": "Section 4: Performance Review Cycle"},
        {"type": "p", "text": "AnthraSync runs a structured bi-annual performance review cycle to support career development, align expectations, and reward achievements. The appraisal cycles occur twice every year, specifically in the months of April and October."},
        {"type": "bullet", "text": "April Cycle: Focuses on mid-year progress review, goal adjustments, and developmental feedback."},
        {"type": "bullet", "text": "October Cycle: Focuses on the annual comprehensive appraisal, salary increments, promotions, and new goal setting."},
        {"type": "p", "text": "The evaluation process includes self-appraisal, peer reviews, manager evaluation, and a final one-on-one discussion. Ratings are calibrated across departments to ensure fairness and transparency."},
        {"type": "spacer", "height": 10},

        {"type": "h1", "text": "Section 5: Notice Period & Resignation"},
        {"type": "p", "text": "To ensure smooth handover of projects and operations, the notice period required is based on role seniority. The notice period is 30 days for junior roles and 60 days for senior roles (Lead, Manager, and above). The resignation must be submitted in writing via the HR portal. In exceptional circumstances, a manager may request a shorter notice period or buy-out option, subject to written approval from the Head of HR."},
        {"type": "pagebreak"},

        {"type": "h1", "text": "Section 6: Expense Reimbursement Guidelines"},
        {"type": "p", "text": "Employees are eligible to claim reimbursements for business-related expenses incurred during the discharge of their duties. Claims must be submitted with original receipts through the finance portal by the 25th of each month. The approved reimbursement categories and monthly limits are defined below:"},
        {"type": "table", "data": [
            ["Reimbursement Category", "Monthly Limit", "Eligibility & Guidelines"],
            ["Travel Expense", "Up to \u20b95,000/month", "Covers local business commute, auto/cab fares, and fuel claims."],
            ["Food & Meals", "Up to \u20b92,000/month", "Covers team lunches, late-working dinners, and business meal meetings."]
        ], "widths": [150, 100, 250]},
        {"type": "p", "text": "Any expense exceeding the specified limits requires prior approval from the department head. Falsifying expense reports or submitting personal expenses for corporate reimbursement will lead to strict disciplinary action, up to and including termination."}
    ]
    generate_pdf("HR_Policy.pdf", "Employee Handbook & HR Policies", "2026.1", schema)

def make_customer_faq():
    schema = [
        {"type": "h1", "text": "Section 1: Subscription Cancellation & Refund Policy"},
        {"type": "p", "text": "At AnthraSync, we aim to provide high-quality services. If a customer is not satisfied with their SaaS subscription, they can request a cancellation and refund. The refund eligibility guidelines are structured as follows:"},
        {"type": "bullet", "text": "Full Refund: Customers are eligible for a full refund of their payment if the refund request is submitted within 30 days of the initial purchase or billing date."},
        {"type": "bullet", "text": "Partial Refund: A partial refund (calculated prorata based on unused days) is available if the request is submitted within 60 days of the billing date."},
        {"type": "bullet", "text": "No Refund: No refunds are issued for cancellations requested after 60 days of the billing date. Access to the product will continue until the end of the current billing cycle."},
        {"type": "h2", "text": "1.1 Subscription Cancellation Notice"},
        {"type": "p", "text": "To cancel a recurring subscription and prevent automatic renewal, customers must submit a cancellation request through the billing dashboard. A subscription cancellation requires a 7 days notice prior to the next scheduled billing date. If notice is given less than 7 days before renewal, the subscription will renew, and cancellation will apply to the subsequent cycle."},
        {"type": "spacer", "height": 10},

        {"type": "h1", "text": "Section 2: Support Hours & Channels"},
        {"type": "p", "text": "Our customer support team is available to assist users with technical, billing, or general queries. Support hours are Monday to Friday, 9:00 AM to 6:00 PM IST. Support is closed on weekends and national holidays. Customers can reach us via the support portal, in-app chat, or by emailing support@anthrasync.com. Tickets submitted outside business hours will be queued and handled sequentially on the next business day."},
        {"type": "pagebreak"},

        {"type": "h1", "text": "Section 3: Escalation Process"},
        {"type": "p", "text": "To resolve customer queries efficiently, AnthraSync operates a structured three-tier support escalation framework. Every support ticket is initially logged at Level 1 and escalated if required."},
        {"type": "table", "data": [
            ["Support Tier", "Primary Responsibility", "Target Handling"],
            ["L1 Support", "General queries, account access, simple troubleshooting.", "Initial response & resolution within business hours."],
            ["L2 Support", "Technical issues, configuration problems, integration support.", "Escalated by L1 if technical deep-dive is required."],
            ["L3 Support", "Bug fixes, backend issues, database or system failures.", "Escalated by L2 to engineering and product teams."]
        ], "widths": [100, 220, 180]},
        {"type": "p", "text": "Customers may request an expedited escalation if their business operations are severely impacted, subject to validation by the support manager."},
        {"type": "spacer", "height": 10},

        {"type": "h1", "text": "Section 4: Service Level Agreements (SLA)"},
        {"type": "p", "text": "We are committed to maintaining high availability and resolving issues promptly. Our resolution SLAs are categorized by issue severity:"},
        {"type": "bullet", "text": "Critical Issues: Issues where the core application is down, or data access is completely blocked. Resolution SLA: Within 4 hours of ticket creation."},
        {"type": "bullet", "text": "Major Issues: Core features are broken with no workaround, but the application is running. Resolution SLA: Within 24 hours of ticket creation."},
        {"type": "bullet", "text": "Minor Issues: Cosmetic bugs, minor functional glitches, or general questions. Resolution SLA: Within 3 business days."},
        {"type": "p", "text": "SLAs apply to active business hours (Monday to Friday, 9 AM to 6 PM IST) and are monitored by our customer success operations team."},
        {"type": "pagebreak"},

        {"type": "h1", "text": "Section 5: Data Deletion & Privacy Policy"},
        {"type": "p", "text": "AnthraSync respects user privacy and complies with data protection regulations. Upon request, a customer can ask for permanent deletion of their account data. A data deletion request must be submitted by the account owner via the privacy dashboard or email. Once verified, the data deletion request is processed within 30 days of the request. This process involves purging all user files, account profiles, activity logs, and personal identifiers from our production systems and databases. Backups are cleared in accordance with our 90-day retention schedule."}
    ]
    generate_pdf("Customer_FAQ.pdf", "Customer Support FAQ & SLA Guidelines", "1.4", schema)

def make_it_security_guide():
    schema = [
        {"type": "h1", "text": "Section 1: Password & Authentication Policy"},
        {"type": "p", "text": "Passwords are the first line of defense for our digital infrastructure. All employees must follow strict password guidelines to secure their accounts. Passwords must be a minimum of 12 characters and contain a mix of uppercase, lowercase, numbers, and special characters. Sequential numbers (e.g., 12345) or simple dictionary words are prohibited."},
        {"type": "p", "text": "Accounts are configured to force password rotation every 90 days. Users cannot reuse any of their last 5 passwords. Multi-Factor Authentication (MFA) is mandatory for all corporate accounts, including email, Slack, GitHub, and internal databases. Five failed login attempts will trigger a temporary lock on the account for 30 minutes, requiring IT administrator intervention to unlock."},
        {"type": "spacer", "height": 10},

        {"type": "h1", "text": "Section 2: Remote Access & VPN Usage"},
        {"type": "p", "text": "With the flexibility of hybrid work, securing remote connections is critical. A secure Virtual Private Network (VPN) is mandatory for remote access to any internal corporate network, server, database, or staging environment. This requirement applies to employees working from home or public Wi-Fi spots (catered spaces, airports, cafes)."},
        {"type": "p", "text": "Connecting to AnthraSync resources without an active VPN connection is a violation of security protocols and is blocked automatically by network firewalls. Sharing VPN credentials or configuration profiles with anyone, including colleagues, is strictly prohibited."},
        {"type": "pagebreak"},

        {"type": "h1", "text": "Section 3: Approved Devices & Security Software"},
        {"type": "p", "text": "Employees must conduct corporate work only on approved devices provisioned by the IT department. Personal devices (BYOD) are allowed for email and Slack communication only if they have been registered and enrolled in the company's Mobile Device Management (MDM) software. The MDM system enforces screen lock codes, disk encryption, and remote-wipe capabilities. Security software, including mandatory Antivirus and Endpoint Detection & Response (EDR) agents, must remain active and updated on all corporate laptops. Disabling these security systems will result in immediate network access revocation."},
        {"type": "spacer", "height": 10},

        {"type": "h1", "text": "Section 4: Data Classification Framework"},
        {"type": "p", "text": "To ensure appropriate handling and protection of data, AnthraSync classifies all information assets into four distinct tiers:"},
        {"type": "table", "data": [
            ["Classification", "Description", "Handling & Storage Rules"],
            ["Public", "Information approved for public distribution (e.g. marketing, blogs).", "No special storage constraints. Safe to share."],
            ["Internal", "Standard company communications, operational processes.", "Accessible to all employees. Do not share externally."],
            ["Confidential", "HR records, product roadmaps, pricing discussions.", "Restricted to specific teams. Encryption required in transit."],
            ["Restricted", "Customer database tables, financial records, API keys.", "Highly restricted access. Logged access, encrypted storage."]
        ], "widths": [100, 180, 220]},
        {"type": "spacer", "height": 10},

        {"type": "h1", "text": "Section 5: Security Incident Reporting"},
        {"type": "p", "text": "Timely reporting of security incidents is vital to limit damage and contain breaches. A security incident is defined as any event that compromises the confidentiality, integrity, or availability of company assets. This includes lost or stolen laptops, suspected malware infections, leaked passwords, or unauthorized system access. Employees must report security incidents to the security response team within 1 hour of discovery. Incident report tickets are logged through the security channel on Slack or by emailing security@anthrasync.com."},
        {"type": "pagebreak"},

        {"type": "h1", "text": "Section 6: Software Installation & Phishing Awareness"},
        {"type": "h2", "text": "6.1 Software Installation Policy"},
        {"type": "p", "text": "Employees are prohibited from installing unauthorized software on corporate-issued devices. Only IT-approved software from the official software repository or pre-cleared by the security team is allowed. Browser extensions must be reviewed for data permissions before installation. P2P file sharing, torrent software, and unauthorized developer tools are blocked and audited monthly."},
        {"type": "h2", "text": "6.2 Phishing Awareness Guidelines"},
        {"type": "p", "text": "Phishing remains a primary attack vector. Employees must practice vigilance when reviewing external emails. Key pointers to identify phishing include mismatching sender domain names, urgent requests for financial transactions or password resets, and suspicious attachment formats (.exe, .zip, macro-enabled documents). If a phishing attempt is suspected, employees should click the 'Report Phishing' button in Outlook or Gmail to alert the security team. Regular simulated phishing tests are conducted to build cyber resilience."}
    ]
    generate_pdf("IT_Security_Guide.pdf", "Information Technology Security Guide", "3.2", schema)

def make_product_manual():
    schema = [
        {"type": "h1", "text": "Section 1: SyncFlow Product Overview & Core Features"},
        {"type": "p", "text": "SyncFlow is a premium, cloud-native project management and team collaboration SaaS platform designed by AnthraSync Technologies. It streamlines delivery pipelines, tracks resource allocation, and provides real-time team insights. The core features of SyncFlow include:"},
        {"type": "bullet", "text": "Task Management: Interactive Kanban boards, task dependencies, priority mapping, and customizable workflows."},
        {"type": "bullet", "text": "Time Tracking: In-app timers, timesheet logging, billable hour tracking, and payroll integrations."},
        {"type": "bullet", "text": "Team Collaboration: Threaded discussions, shared document editing, live notifications, and project chat rooms."},
        {"type": "bullet", "text": "Reporting & Analytics: Custom dashboard creation, sprint burn-down charts, velocity tracking, and resource utilization reports."},
        {"type": "spacer", "height": 10},

        {"type": "h1", "text": "Section 2: Integrations Portfolio"},
        {"type": "p", "text": "SyncFlow integrates seamlessly with standard tools to consolidate work processes. The supported integrations list includes:"},
        {"type": "bullet", "text": "Slack: Send automated task updates, trigger alerts, and create tasks directly using slash commands."},
        {"type": "bullet", "text": "Jira: Bi-directional synchronization of issues, status transitions, and epic mapping."},
        {"type": "bullet", "text": "GitHub: Link code commits and pull requests to SyncFlow cards, and automate task completion upon code merges."},
        {"type": "bullet", "text": "Google Workspace: Sync calendars, attach documents from Google Drive, and import contact lists."},
        {"type": "pagebreak"},

        {"type": "h1", "text": "Section 3: Pricing & Subscription Tiers"},
        {"type": "p", "text": "SyncFlow offers a flexible pricing model tailored for organizations of all sizes. The pricing structures are defined as follows:"},
        {"type": "table", "data": [
            ["Pricing Tier", "Monthly Cost", "Key Features & Allowances"],
            ["Free Tier", "Free", "Up to 5 users, basic Kanban boards, 1GB storage, basic reports."],
            ["Pro Tier", "\u20b9999/month", "Unlimited users, advanced time tracking, 50GB storage, core integrations."],
            ["Enterprise", "Custom pricing", "Dedicated servers, custom integrations, unlimited storage, 24/7 SLA support."]
        ], "widths": [100, 100, 300]},
        {"type": "p", "text": "Billing is processed monthly or annually. Annual subscriptions are eligible for a 20% discount on the Pro Tier pricing."},
        {"type": "spacer", "height": 10},

        {"type": "h1", "text": "Section 4: System Requirements & Installation"},
        {"type": "p", "text": "SyncFlow is primarily accessed via a modern web browser. Supported browsers include Google Chrome (v90+), Mozilla Firefox (v88+), Safari (v14+), and Microsoft Edge (v92+). Cookies and JavaScript must be enabled in the browser settings."},
        {"type": "p", "text": "For offline capabilities, desktop clients are available for download. System requirements for the desktop application are: Windows 10 (64-bit) or later with 4GB RAM, or macOS 11 Big Sur or later with Apple Silicon or Intel Core processors. Mobile applications are supported on iOS 14+ and Android 8.0+."},
        {"type": "pagebreak"},

        {"type": "h1", "text": "Section 5: Troubleshooting Common Errors"},
        {"type": "p", "text": "If users encounter issues while using SyncFlow, they should refer to the following common resolutions:"},
        {"type": "bullet", "text": "Error Code 401 (Unauthorized): Clear browser cache and cookies, then re-authenticate using the login page. Ensure MFA is completed."},
        {"type": "bullet", "text": "Sync Failures (Spinner spinning indefinitely): Verify network connection. If using a corporate VPN, check if security ports 443 and 8443 are open for SyncFlow domains."},
        {"type": "bullet", "text": "Integration Failures: Disconnect and reconnect the third-party application from the settings panel. Check OAuth permissions."},
        {"type": "spacer", "height": 10},

        {"type": "h1", "text": "Section 6: API Reference & Rate Limits"},
        {"type": "p", "text": "Developers can extend SyncFlow using our REST API. Access requires a valid API bearer token generated from the developer dashboard. API rate limits are applied per subscription tier. The Pro plan is limited to 1000 requests/hour. Exceeding this rate limit will return a HTTP 429 Too Many Requests response with a 'Retry-After' header indicating the wait time in seconds. Enterprise plans can request custom rate limits based on operational requirements."}
    ]
    generate_pdf("Product_Manual.pdf", "SyncFlow SaaS Product Manual & API Reference", "4.1", schema)

def make_onboarding_guide():
    schema = [
        {"type": "h1", "text": "Section 1: Day 1 Checklist & Setup"},
        {"type": "p", "text": "Welcome to AnthraSync Technologies! We are thrilled to have you join our team. Your first day will focus on getting set up and acclimated to our environment. Please complete the following Day 1 checklist:"},
        {"type": "bullet", "text": "Hardware Procurement: Collect your laptop, charger, and access keycard from the IT service desk."},
        {"type": "bullet", "text": "Credential Initialization: Follow the IT setup sheet to initialize your corporate email account and set up a secure password."},
        {"type": "bullet", "text": "Slack & Communication: Set up your profile on Slack, upload a professional photo, and join key channels including #announcements, #general, and #welcome."},
        {"type": "bullet", "text": "Access Provisioning: Submit requests for development tools, Notion workspaces, and GitHub organization access through the IT support portal."},
        {"type": "spacer", "height": 10},

        {"type": "h1", "text": "Section 2: First Week Milestones"},
        {"type": "p", "text": "During your first week, you will focus on building relationships and understanding our projects. Your main goals include:"},
        {"type": "bullet", "text": "Team Introductions: Schedule short 15-minute meet-and-greets with all direct team members and key stakeholders."},
        {"type": "bullet", "text": "Project Overview: Review project documentation, code repositories, and roadmap sheets on Notion. Attend the architecture walkthrough with your Lead."},
        {"type": "bullet", "text": "Local Dev Environment: Complete the local setup instructions for your active project. Verify you can run builds and tests successfully."},
        {"type": "pagebreak"},

        {"type": "h1", "text": "Section 3: First Month Expectations"},
        {"type": "p", "text": "In your first 30 days, we want to ensure you are fully integrated into our operational cadence. You are expected to:"},
        {"type": "bullet", "text": "Complete Compliance Training: Go through the mandatory security, GDPR compliance, and anti-harassment training modules within the HR portal."},
        {"type": "bullet", "text": "Shadow Team Members: Attend stand-ups, planning meetings, and debugging sessions. Shadow a senior team member on at least two sprint deliveries."},
        {"type": "bullet", "text": "Initial Contributions: Take on small, well-defined tasks (bug fixes, document updates, simple features) to understand our release pipeline."},
        {"type": "spacer", "height": 10},

        {"type": "h1", "text": "Section 4: Enterprise Collaboration Tools"},
        {"type": "p", "text": "At AnthraSync, we utilize a suite of collaboration tools to ensure transparency and efficiency across teams. The core tools used include:"},
        {"type": "table", "data": [
            ["Tool Name", "Primary Purpose", "Access Guidelines"],
            ["Notion", "Knowledge base, product specs, team documentation.", "Shared access. All pages public to employees unless restricted."],
            ["Slack", "Real-time communication, team updates, operational alerts.", "Channels structured by project and department."],
            ["GitHub", "Version control, pull requests, code reviews.", "SSO login required. Review by at least one peer mandatory."],
            ["Jira", "Sprint planning, task tracking, bug reporting.", "Tickets updated daily during standup reviews."],
            ["Google Meet", "Video conferencing, daily standups, alignment calls.", "Default calendar event link for all meetings."]
        ], "widths": [90, 230, 180]},
        {"type": "pagebreak"},

        {"type": "h1", "text": "Section 5: Buddy Program & Mentorship"},
        {"type": "p", "text": "To help you transition smoothly, AnthraSync assigns a buddy to every new hire for their first 30 days. Your buddy is a peer from your department who will help you navigate company culture, find documents, answer informal questions, and guide you through the setup process. Feel free to schedule daily quick syncs with your buddy to address any blockers or seek advice. HR will monitor the program through a short check-in at the end of week 2 and week 4."},
        {"type": "spacer", "height": 10},

        {"type": "h1", "text": "Section 6: Probation Period & Expectations"},
        {"type": "p", "text": "All new hires go through a probation period of 3 months. This period is an opportunity for both the employee and the company to evaluate alignment, capability, and fit. During probation, regular feedback sessions will be held by your manager. A formal probation review will take place at the end of 90 days. Upon successful completion of the review, your employment status will be confirmed in writing. In cases where performance criteria are not met, the probation period may be extended up to an additional 3 months, or employment may be terminated by either party with a 15-day notice period."}
    ]
    generate_pdf("Onboarding_Guide.pdf", "New Employee Onboarding Guide", "1.1", schema)

def make_compliance_guidelines():
    schema = [
        {"type": "h1", "text": "Section 1: GDPR Compliance Requirements"},
        {"type": "p", "text": "AnthraSync Technologies takes data privacy seriously. As a processor and controller of user data, we comply strictly with General Data Protection Regulation (GDPR) requirements. The core pillars of our compliance include:"},
        {"type": "bullet", "text": "Data Minimization: We collect and process only the personal data that is strictly necessary for our services."},
        {"type": "bullet", "text": "User Consent: Explicit, verifiable consent must be obtained from users before any tracking or marketing cookies are stored."},
        {"type": "bullet", "text": "Right to be Forgotten: Customer requests for account and data deletion must be fulfilled in a timely manner. Data must be purged permanently within 30 days of the verified request."},
        {"type": "bullet", "text": "Breach Notification: In the event of a data breach, the Data Protection Officer (DPO) must notify regulatory authorities within 72 hours of detection."},
        {"type": "spacer", "height": 10},

        {"type": "h1", "text": "Section 2: Data Retention & Archival Policy"},
        {"type": "p", "text": "To satisfy legal requirements and maintain operational efficiency, we enforce a strict data retention policy. Records are archived and deleted based on their category rules. Financial and tax-related records must be retained for 7 years from the end of the fiscal year. Operational logs, system monitoring logs, and email history are retained for 3 years, after which they are automatically purged. Customer data is retained for the duration of the active subscription plus 90 days, unless a deletion request is initiated sooner. Archived data must be encrypted at rest using AES-256 keys managed by the IT Security team."},
        {"type": "pagebreak"},

        {"type": "h1", "text": "Section 3: Internal & External Audits"},
        {"type": "p", "text": "AnthraSync undergoes regular audits to verify process compliance, financial accuracy, and data security. The audit schedule is structured as follows:"},
        {"type": "bullet", "text": "Quarterly Internal Audits: Conducted by our internal compliance team. These focus on access log reviews, user privilege verification, and security controls check-ups. Reports are reviewed by the CTO."},
        {"type": "bullet", "text": "Annual External Audits: Conducted by an accredited independent third-party auditor. These audit reports verify SOC2 Type II, ISO 27001, and GDPR certifications. Summaries are shared with enterprise clients upon request."},
        {"type": "spacer", "height": 10},

        {"type": "h1", "text": "Section 4: Whistleblower & Non-Retaliation Policy"},
        {"type": "p", "text": "We are committed to maintaining an ethical culture. If an employee becomes aware of illegal activities, ethical violations, fraud, or violations of company policies, they are urged to report it immediately. Reports can be filed through our anonymous whistleblower portal or by contacting the legal department directly. AnthraSync guarantees protection against retaliation, discrimination, or harassment for any employee reporting in good faith. Investigations are conducted by the Chief Compliance Officer, and findings are escalated directly to the board of directors."},
        {"type": "pagebreak"},

        {"type": "h1", "text": "Section 5: Conflict of Interest Declaration"},
        {"type": "p", "text": "To prevent conflicts and protect corporate integrity, all employees are required to submit an annual Conflict of Interest Declaration. A conflict of interest arises when an employee's personal interests, external activities, or financial relationships influence, or appear to influence, their objective judgment in performing company duties. Examples include holding shares in a competitor, working as an advisor for a vendor, or hiring close relatives. Declarations must be updated during the annual renewal cycle in January through the HR portal. If a potential conflict arises mid-year, it must be disclosed within 15 days of occurrence."},
        {"type": "spacer", "height": 10},

        {"type": "h1", "text": "Section 6: Third-Party Vendor Risk Assessment"},
        {"type": "p", "text": "Before onboarding any third-party vendor or SaaS tool that handles company or customer data, a comprehensive vendor assessment process must be completed. This process ensures the vendor's security posture aligns with our requirements. The workflow involves:"},
        {"type": "bullet", "text": "Security Questionnaire: The vendor must complete our standard security checklist covering data hosting, encryption, access control, and incident response."},
        {"type": "bullet", "text": "Compliance Review: Verification of certifications (SOC2, ISO 27001) and privacy policies."},
        {"type": "bullet", "text": "Risk Scoring: A security analyst assigns a risk rating (Low, Medium, High). High-risk vendors require sign-off from the CISO."},
        {"type": "bullet", "text": "Contractual Safeguards: Legal reviews contracts to include Data Processing Addendums (DPA) and standard liability clauses."}
    ]
    generate_pdf("Compliance_Guidelines.pdf", "Corporate Compliance & Governance Guidelines", "2.0", schema)

def main():
    print("Generating corporate PDF documents...")
    try:
        make_hr_policy()
        make_customer_faq()
        make_it_security_guide()
        make_product_manual()
        make_onboarding_guide()
        make_compliance_guidelines()
        print("All documents generated successfully in data/documents/!")
    except Exception as e:
        print(f"Error generating documents: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
