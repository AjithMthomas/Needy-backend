import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def build_pdf():
    pdf_filename_f = r"F:\Downloads\Needy_Influencer_Pitch_Deck.pdf"
    pdf_filename_docs = r"C:\Users\hp\OneDrive\Documents\Needy_Influencer_Pitch_Deck.pdf"
    artifact_dir = r"C:\Users\hp\.gemini\antigravity-ide\brain\bdecd03e-6a3b-49cf-85ae-49a59ed5d78b"
    pdf_filename_artifact = os.path.join(artifact_dir, "Needy_Influencer_Pitch_Deck.pdf")

    os.makedirs(artifact_dir, exist_ok=True)
    target_path = pdf_filename_f if os.path.exists(r"F:\Downloads") else pdf_filename_docs

    doc = SimpleDocTemplate(
        target_path,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    # Color Palette
    primary_color = colors.HexColor("#0F172A")     # Slate 900
    secondary_color = colors.HexColor("#0EA5E9")   # Sky 500
    accent_mint = colors.HexColor("#10B981")       # Emerald 500
    accent_rose = colors.HexColor("#F43F5E")       # Rose 500 (Emergency)
    text_dark = colors.HexColor("#1E293B")         # Slate 800
    bg_card = colors.HexColor("#F8FAFC")           # Slate 50
    border_color = colors.HexColor("#E2E8F0")      # Slate 200

    # Custom Typography Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Title'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=primary_color,
        alignment=0,
        spaceAfter=4
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11.5,
        leading=15,
        textColor=secondary_color,
        spaceAfter=12
    )

    h1_style = ParagraphStyle(
        'H1Style',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=primary_color,
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'H2Style',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=14,
        textColor=secondary_color,
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=text_dark,
        spaceAfter=5
    )

    body_bold = ParagraphStyle(
        'BodyBold',
        parent=body_style,
        fontName='Helvetica-Bold'
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=11,
        textColor=colors.white,
        alignment=1
    )

    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=11.5,
        textColor=text_dark
    )

    table_cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=table_cell_style,
        fontName='Helvetica-Bold'
    )

    story = []

    # Document Header
    story.append(Paragraph("<b>needy</b> — Complete Pitch Deck & Influencer Playbook", title_style))
    story.append(Paragraph("Hyperlocal Micro-Marketplace & Community Utility Platform | INR (₹) Revenue Breakdown", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=secondary_color, spaceAfter=10))

    # 1. Executive Vision & Problem Statement
    story.append(Paragraph("1. Executive Vision & Core Value Proposition", h1_style))
    story.append(Paragraph(
        "<b>needy</b> is a safety-first hyperlocal micro-marketplace connecting people who have spare time with nearby individuals, students, or local businesses who have specific needs. "
        "It solves everyday local friction: <i>'I need help moving furniture in 30 mins'</i>, <i>'Looking for a girl companion for evening tea'</i>, <i>'Local cafe needs a 3-hour cashier'</i>, or <i>'Emergency help needed nearby'</i>.",
        body_style
    ))
    story.append(Paragraph(
        "<b>The 218K Influencer Advantage:</b> Hyperlocal apps thrive on <i>geographic density</i>. "
        "By launching with a single partner influencer (218,000 followers), converting just 2% to 5% of followers creates an instant active ecosystem of <b>4,000 to 10,000 active users</b> in a single city hub (e.g. Madiwala / Koramangala, Bengaluru).",
        body_style
    ))

    story.append(Spacer(1, 6))

    # 2. Highlighted 4 Main Specialized Options
    story.append(Paragraph("2. The Four Main Core App Hubs (Key Pillars)", h1_style))
    story.append(Paragraph(
        "needy is structured around 4 major dedicated activity hubs designed for high-frequency daily utility:",
        body_style
    ))

    main_hubs_data = [
        [
            Paragraph("Core Option / Hub", table_header_style),
            Paragraph("Purpose & Features", table_header_style),
            Paragraph("How People Use It (Use Cases)", table_header_style)
        ],
        [
            Paragraph("🚨 <b>Emergency (SOS Hub)</b>", table_cell_bold),
            Paragraph("Immediate community alert, live GPS dispatch, 1-tap SOS trigger, trusted contact broadcast.", table_cell_style),
            Paragraph("Late-night safety walk, sudden medical errand, vehicle breakdown, flat tire help.", table_cell_style)
        ],
        [
            Paragraph("💼 <b>Gigs & Hiring Hub</b>", table_cell_bold),
            Paragraph("Micro-gigs & shopkeeper hiring. Fast 2-4 hour temporary job matches.", table_cell_style),
            Paragraph("Local shops hire event helpers, flyer distributors, cashiers. Students earn quick daily cash.", table_cell_style)
        ],
        [
            Paragraph("🏠 <b>Room Finding Hub</b>", table_cell_bold),
            Paragraph("Zero-brokerage room hunting, flatmate finder, PG vacancies, temporary stay matching.", table_cell_style),
            Paragraph("Newcomers find flatmates, vacant PG beds, or emergency weekend stays without broker fees.", table_cell_style)
        ],
        [
            Paragraph("🚗 <b>Make Trip & Travel Hub</b>", table_cell_bold),
            Paragraph("Carpooling, cab split, weekend road trip team creation, getaway expense sharing.", table_cell_style),
            Paragraph("Splitting airport cabs, organizing Nandi Hills sunrise bike rides, weekend trips.", table_cell_style)
        ]
    ]

    t_hubs = Table(main_hubs_data, colWidths=[1.6*inch, 2.8*inch, 2.6*inch])
    t_hubs.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), primary_color),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, border_color),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, bg_card]),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_hubs)
    story.append(Spacer(1, 8))

    # 3. All Income Generating Methods
    story.append(Paragraph("3. Complete Revenue & Monetization Model (All Streams in INR ₹)", h1_style))
    story.append(Paragraph(
        "needy monetizes every level of local interaction through 5 distinct revenue streams:",
        body_style
    ))

    monetization_data = [
        [
            Paragraph("Income Stream", table_header_style),
            Paragraph("Mechanism & Pricing Structure", table_header_style),
            Paragraph("Revenue Potential (INR ₹)", table_header_style)
        ],
        [
            Paragraph("<b>1. Platform Transaction Commission</b>", table_cell_bold),
            Paragraph("5% fee charged on all completed paid tasks, micro-gigs, room bookings, and cab splits.", table_cell_style),
            Paragraph("<b>₹17,500</b> / 1k tasks<br/><b>₹1,75,000</b> / 10k tasks", table_cell_bold)
        ],
        [
            Paragraph("<b>2. Shop & Business Gigs Subscription</b>", table_cell_bold),
            Paragraph("Local businesses & shopkeepers pay ₹499 - ₹1,999/month for unlimited urgent gig posts & top placement.", table_cell_style),
            Paragraph("<b>₹50,000</b> / month<br/>(100 subscribed shops)", table_cell_bold)
        ],
        [
            Paragraph("<b>3. Live Auctions Platform Commission</b>", table_cell_bold),
            Paragraph("5% take rate on live auctions (gadgets, consultation, exclusive influencer meetups/tea walks).", table_cell_style),
            Paragraph("<b>₹25,000 - ₹80,000</b> / month", table_cell_bold)
        ],
        [
            Paragraph("<b>4. Merchant Partner Perks Sponsorship</b>", table_cell_bold),
            Paragraph("Local cafes, gyms & restaurants pay ₹1,500 - ₹5,000/month to feature exclusive discounts for needy members.", table_cell_style),
            Paragraph("<b>₹45,000 - ₹1,500,00</b> / month", table_cell_bold)
        ],
        [
            Paragraph("<b>5. Featured Post & Karma Micro-transactions</b>", table_cell_bold),
            Paragraph("Users pay ₹49 - ₹199 to feature their room requirement, emergency request, or profile at the top of feed.", table_cell_style),
            Paragraph("<b>₹20,000 - ₹60,000</b> / month", table_cell_bold)
        ]
    ]

    t_money = Table(monetization_data, colWidths=[1.8*inch, 3.4*inch, 1.8*inch])
    t_money.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), secondary_color),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, border_color),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, bg_card]),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_money)
    story.append(Spacer(1, 8))

    # 4. Financial Calculations Grid (INR)
    story.append(Paragraph("4. Concrete Financial Projections (All Amounts in INR ₹)", h1_style))
    
    financial_grid_data = [
        [
            Paragraph("Monthly Activity Volume", table_header_style),
            Paragraph("Avg. Activity Value", table_header_style),
            Paragraph("Monthly GMV (Gross Volume)", table_header_style),
            Paragraph("Commission Income (5%)", table_header_style),
            Paragraph("Perks, Ads & Subscriptions", table_header_style),
            Paragraph("Net Monthly Revenue (INR)", table_header_style)
        ],
        [
            Paragraph("<b>1,000 Activities</b><br/>(Initial Pilot Phase)", table_cell_style),
            Paragraph("₹350", table_cell_style),
            Paragraph("₹3,50,000", table_cell_style),
            Paragraph("₹17,500", table_cell_style),
            Paragraph("₹15,000", table_cell_style),
            Paragraph("<b>₹32,500 / month</b>", table_cell_bold)
        ],
        [
            Paragraph("<b>10,000 Activities</b><br/>(Influencer Cohort Launch)", table_cell_style),
            Paragraph("₹350", table_cell_style),
            Paragraph("₹35,00,000", table_cell_style),
            Paragraph("₹1,75,000", table_cell_style),
            Paragraph("<b>₹75,000</b>", table_cell_style),
            Paragraph("<b>₹2,50,000 / month</b><br/>(₹30 Lakhs / year)", table_cell_bold)
        ],
        [
            Paragraph("<b>50,000 Activities</b><br/>(Multi-Zone City Scale)", table_cell_style),
            Paragraph("₹350", table_cell_style),
            Paragraph("₹1,75,00,000", table_cell_style),
            Paragraph("₹8,75,000", table_cell_style),
            Paragraph("₹3,75,000", table_cell_style),
            Paragraph("<b>₹12,50,000 / month</b><br/>(₹1.5 Crore / year)", table_cell_bold)
        ]
    ]

    t_grid = Table(financial_grid_data, colWidths=[1.3*inch, 1.0*inch, 1.2*inch, 1.1*inch, 1.1*inch, 1.3*inch])
    t_grid.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), primary_color),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, border_color),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, bg_card]),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_grid)
    story.append(Spacer(1, 8))

    # 5. Full Feature Catalog & How People Use Needy
    story.append(Paragraph("5. Complete Feature Catalog & How People Use Needy", h1_style))
    
    features_data = [
        [Paragraph("Feature / Screen", table_header_style), Paragraph("Description", table_header_style), Paragraph("How Users Interact With It", table_header_style)],
        [
            Paragraph("<b>Hyperlocal Discover Feed</b>", table_cell_bold),
            Paragraph("Real-time feed sorted by distance (0-5 km) with 6 categories & 3 Exchange Modes.", table_cell_style),
            Paragraph("Users browse nearby posts, filter by free/paid/treat, and apply in 1 tap.", table_cell_style)
        ],
        [
            Paragraph("<b>Bored Radar Map</b>", table_cell_bold),
            Paragraph("Ambient neighborhood pulse map displaying active users & drift counts.", table_cell_style),
            Paragraph("Users see who is free or bored around them in real time without privacy leak.", table_cell_style)
        ],
        [
            Paragraph("<b>Live Auctions Hub</b>", table_cell_bold),
            Paragraph("Real-time bidding ticker for gadgets, consultation, and exclusive influencer meetups.", table_cell_style),
            Paragraph("Place live bids or click 'Buy It Now' for instant purchase.", table_cell_style)
        ],
        [
            Paragraph("<b>Community Board & Karma</b>", table_cell_bold),
            Paragraph("Idea upvoting system & Karma rewards ledger for helping others.", table_cell_style),
            Paragraph("Users gain Karma points for completing tasks & redeem partner perk discounts.", table_cell_style)
        ],
        [
            Paragraph("<b>Trust & Safety Rules</b>", table_cell_bold),
            Paragraph("OTP authentication, Female-Only / Male-Only post filters, Guardian badges.", table_cell_style),
            Paragraph("Women post company requests with 100% peace of mind via female-only filter.", table_cell_style)
        ]
    ]

    t_feat = Table(features_data, colWidths=[1.5*inch, 2.7*inch, 2.8*inch])
    t_feat.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), primary_color),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, border_color),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, bg_card]),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t_feat)
    story.append(Spacer(1, 8))

    # 6. Zero-Cost Development & Cloud Scaling Strategy
    story.append(Paragraph("6. Zero-Cost Infrastructure & Scaling Roadmap", h1_style))
    story.append(Paragraph(
        "Built with Flutter (Android/iOS/Web) and Django 5.2 LTS + PostgreSQL.<br/>"
        "• <b>Phase 1 (Pilot Launch)</b>: <b>₹0 / Month ($0)</b> operating cost on Render Free Tier + Neon PostgreSQL.<br/>"
        "• <b>Phase 2 (5k - 25k Users)</b>: <b>₹1,200 - ₹2,500 / Month</b> for database & container scaling.<br/>"
        "• <b>Profit Margin</b>: Remains above <b>96% - 98%</b> because server cost is negligible compared to transaction fees.",
        body_style
    ))

    story.append(Spacer(1, 8))

    # 7. Influencer Partnership Offer & Meeting Guidelines
    story.append(Paragraph("7. Influencer Co-Founding Offer & Meeting Checklist", h1_style))
    offers = [
        "<b>Co-Founding Equity Stake (15% - 25%)</b>: Partner with him as a co-founder to align long-term incentives.",
        "<b>30% Revenue Share on Referral Cohort</b>: Direct commission on every paid transaction originating from his referral link.",
        "<b>Exclusive Influencer Live Auctions</b>: Host exclusive fan meetups, tea walks, or 1-on-1 chats on Needy (100% proceeds to him).",
        "<b>Demonstrate Working App</b>: Open <b>http://127.0.0.1:8090/</b> live during the meeting to show 100% finished code."
    ]
    for o in offers:
        story.append(Paragraph(f"✔ {o}", body_style))

    doc.build(story)

    # Save copy to fallback & artifact locations
    try:
        if target_path != pdf_filename_f and os.path.exists(r"F:\Downloads"):
            import shutil
            shutil.copy(target_path, pdf_filename_f)
        if target_path != pdf_filename_docs and os.path.exists(r"C:\Users\hp\OneDrive\Documents"):
            import shutil
            shutil.copy(target_path, pdf_filename_docs)
        if target_path != pdf_filename_artifact:
            import shutil
            shutil.copy(target_path, pdf_filename_artifact)
    except Exception as e:
        print(f"Copy warning: {e}")

    print(f"PDF generated successfully at: {target_path}")

if __name__ == "__main__":
    build_pdf()
