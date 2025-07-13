from fpdf import FPDF
import unicodedata

def clean(text):
    return unicodedata.normalize("NFKD", text).encode("latin-1", "ignore").decode("latin-1")

pdf = FPDF()
pdf.add_page()
pdf.set_auto_page_break(auto=True, margin=15)
pdf.set_font("Arial", 'B', 14)
pdf.cell(0, 10, clean("TechCorp Solutions – RAG-Optimized Company Info"), ln=1, align='C')


# Company Overview
pdf.set_font("Arial", 'B', 12)
pdf.cell(0, 10, "Company Overview", ln=1)
pdf.set_font("Arial", '', 11)
pdf.multi_cell(0, 10, clean("""TechCorp Solutions is a premier technology consulting and services company founded in 2020. We specialize in digital transformation, cloud computing, artificial intelligence, and cybersecurity solutions.
- Founded: 2020
- Employees: 200+
- Clients Served: 500+
- Headquarters: Multan
- Phone: +1 (555) 123-4567
- Email: info@gmail.com
- Website: www.techcorpsolutions.com
- Certifications: ISO 9001, SOC 2 Type II
"""))

# Contact Information
pdf.set_font("Arial", 'B', 12)
pdf.cell(0, 10, "Contact Information", ln=1)
pdf.set_font("Arial", '', 11)
pdf.multi_cell(0, 10, clean("""General Inquiries: info@gmail.com, +1 (555) 123-4567
Sales: sales@gmail.com, +1 (555) 123-4567
Technical Support: support@gmail.com, 1-800-TECHCORP
Emergency: emergency@gmail.com, +1 (555) 123-4567
Locations: Headquarters - Tech City, TC | East Coast - NY | West Coast - SF | Europe - London | Asia - Singapore
"""))

# Payment Terms
pdf.set_font("Arial", 'B', 12)
pdf.cell(0, 10, "Payment Terms", ln=1)
pdf.set_font("Arial", '', 11)
pdf.multi_cell(0, 10, clean("""Standard Terms: 50% upfront, 25% midpoint, 25% on completion
Flexible options: Monthly/Quarterly/Custom payment schedules for enterprise clients
Methods: All major payment methods accepted
"""))

# Support Plans
pdf.set_font("Arial", 'B', 12)
pdf.cell(0, 10, "Support Plans and Response Times", ln=1)
pdf.set_font("Arial", '', 11)
pdf.multi_cell(0, 10, clean("""Basic Plan ($500/month): Email (24h), Phone (business hours)
Professional ($1,500/month): Email (8h), 24/7 Phone, Proactive monitoring
Enterprise ($3,000/month): Dedicated engineer, 1h response, real-time monitoring
Emergency Support: Critical ($500/hr, 1h), High Priority ($300/hr, 4h), Standard ($200/hr, 24h)
"""))

# AI/ML Services
pdf.set_font("Arial", 'B', 12)
pdf.cell(0, 10, "AI/ML Services", ln=1)
pdf.set_font("Arial", '', 11)
pdf.multi_cell(0, 10, clean("""Services:
- AI Strategy Consulting: $3,000 - $8,000
- Custom ML Models: $15,000 - $100,000
- AI Applications: $25,000 - $200,000
- Maintenance: $3,000/month

FAQs:
Q: What types of AI solutions do you offer?
A: Predictive analytics, NLP, computer vision, recommender systems, custom AI.

Q: How long does AI development take?
A: Simple (8-12 wks), Medium (12-16 wks), Complex (16-24 wks), Enterprise (20-32 wks).

Q: Do you provide AI consulting?
A: Yes – Strategy, Tech Assessment, ROI, Roadmap, Vendor selection, Advisory.
"""))

# Cybersecurity Services
pdf.set_font("Arial", 'B', 12)
pdf.cell(0, 10, "Cybersecurity Services", ln=1)
pdf.set_font("Arial", '', 11)
pdf.multi_cell(0, 10, clean("""Services:
- Security Assessment: $8,000 - $25,000
- Penetration Testing: $5,000 - $20,000
- Monitoring: $2,500/month
- Incident Response: $15,000 - $50,000
- Compliance Consulting: $10,000 - $30,000

FAQs:
Q: What security certifications do you have?
A: ISO 27001, SOC 2 Type II, AWS/Microsoft certifications, NIST/HIPAA/PCI DSS compliant.

Q: Do you offer 24/7 security monitoring?
A: Yes, included in Professional/Enterprise plans with guaranteed response times.

Q: What's your incident response time?
A: Critical (1hr), High (4hr), Standard (24hr). Enterprise clients get dedicated engineers.
"""))

# Web Development Services
pdf.set_font("Arial", 'B', 12)
pdf.cell(0, 10, "Web Development Services", ln=1)
pdf.set_font("Arial", '', 11)
pdf.multi_cell(0, 10, clean("""Services:
- Business Website: $8,000 - $25,000
- E-commerce Platform: $15,000 - $50,000
- Custom Web App: $25,000 - $150,000
- Maintenance: $500 - $2,000/month

FAQs:
Q: What technologies do you use?
A: React, Vue.js, Angular, Node.js, Python, PHP, MySQL, PostgreSQL, MongoDB, AWS.

Q: Do you provide ongoing maintenance?
A: Yes. Basic ($500), Professional ($1,000), Enterprise ($2,000) with 24/7 support.

Q: Can you help with e-commerce platforms?
A: Yes – Shopify, WooCommerce, payment integration, order automation, inventory systems.
"""))

# Mobile App Development
pdf.set_font("Arial", 'B', 12)
pdf.cell(0, 10, "Mobile App Development", ln=1)
pdf.set_font("Arial", '', 11)
pdf.multi_cell(0, 10, clean("""Services:
- Native iOS: $20,000 - $100,000
- Native Android: $18,000 - $90,000
- Cross-platform: $25,000 - $120,000
- App Maintenance: $1,000 - $5,000/month

FAQs:
Q: Do you develop for iOS & Android?
A: Yes – native (Swift/Kotlin), cross-platform (React Native/Flutter).

Q: What's the cost?
A: Simple ($20k-$40k), Medium ($40k-$80k), Complex ($80k-$150k), Enterprise ($150k+).

Q: Do you offer app maintenance?
A: Yes – Basic ($1k), Pro ($2.5k), Enterprise ($5k) with updates & priority support.
"""))

# Data Analytics Services
pdf.set_font("Arial", 'B', 12)
pdf.cell(0, 10, "Data Analytics Services", ln=1)
pdf.set_font("Arial", '', 11)
pdf.multi_cell(0, 10, clean("""Services:
- Data Strategy Consulting: $5,000 - $15,000
- Platform Setup: $10,000 - $50,000
- Custom Dashboards: $8,000 - $30,000
- Analytics Support: $2,000/month

FAQs:
Q: What BI tools do you use?
A: Tableau, Power BI, Looker, QlikView, Snowflake, BigQuery, Redshift.

Q: Can you help with data strategy?
A: Yes – audit, governance, architecture, analytics roadmap, ROI planning.

Q: Do you provide custom dashboards?
A: Yes – executive, operational, real-time, interactive dashboards with training.
"""))

# Save the output
pdf.output("TechCorp_Solutions_RAG_Optimized.pdf")
