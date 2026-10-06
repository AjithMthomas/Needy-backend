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

    # Custom styles
    primary_color = colors.HexColor("#0F172A")
    secondary_color = colors.HexColor("#0EA5E9")
    accent_mint = colors.HexColor("#10B981")
    text_dark = colors.HexColor("#1E293B")
    bg_light = colors.HexColor("#F8FAFC")
    card_bg = colors.HexColor("#F1F5F9")
    border_color = colors.HexColor("#E2E8F0")

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Title'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=primary_color,
        alignment=0,
        spaceAfter=6
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=secondary_color,
        spaceAfter=15
    )

    h1_style = ParagraphStyle(
        'H1Style',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=19,
        textColor=primary_color,
        spaceBefore=14,
        spaceAfter=8,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'H2Style',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=secondary_color,
        spaceBefore=10,
        spaceAfter=6,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=text_dark,
        spaceAfter=6
    )

    body_bold = ParagraphStyle(
        'BodyBold',
        parent=body_style,
        fontName='Helvetica-Bold'
    )

    callout_style = ParagraphStyle(
        'CalloutText',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor("#0369A1")
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9.5,
        leading=12,
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

    # Title Banner
    story.append(Paragraph("<b>needy</b> — Influencer Pitch & Partnership Deck", title_style))
    story.append(Paragraph("Hyperlocal Micro-Marketplace & Social Utility App | 218K Audience Partnership Playbook", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=secondary_color, spaceAfter=12))

    # Executive Summary & Vision
    story.append(Paragraph("1. Executive Summary & Vision", h1_style))
    story.append(Paragraph(
        "<b>needy</b> is a safety-first hyperlocal micro-marketplace connecting people who have spare time with nearby individuals or local small businesses. "
        "It solves a universal problem: <i>People are bored or need quick help, while others nearby have spare time or specific skills.</i>",
        body_style
    ))
    story.append(Paragraph(
        "By partnering with an influencer with <b>218,000 followers</b>, we unlock instant geographic density and community trust in a target pilot zone (e.g. Madiwala / Koramangala, Bengaluru). "
        "A single post or reel converting just <b>2% to 5% of followers</b> creates a thriving ecosystem of 4,000 - 10,000 active users instantly.",
        body_style
    ))

    # Core Value Pillars Table
    pillar_data = [
        [Paragraph("Feature / Pillar", table_header_style), Paragraph("What It Does", table_header_style), Paragraph("Why Influencer Audience Will Love It", table_header_style)],
        [
            Paragraph("<b>Micro-Tasks & Errands</b>", table_cell_bold),
            Paragraph("Quick 15-60 min errands (bike wash, document pickup, grocery run).", table_cell_style),
            Paragraph("Students & young pros earn extra income in spare time.", table_cell_style)
        ],
        [
            Paragraph("<b>Time Together & Company</b>", table_cell_bold),
            Paragraph("Tea shop chats, gym buddies, walking partners, museum visits.", table_cell_style),
            Paragraph("Combats loneliness; genuine casual social connection without dating app awkwardness.", table_cell_style)
        ],
        [
            Paragraph("<b>Live Auctions Hub</b>", table_cell_bold),
            Paragraph("Time-limited auctions for gadgets, consultation, or exclusive meetups.", table_cell_style),
            Paragraph("Influencer can auction exclusive 1-on-1 tea walks or fan meetups!", table_cell_style)
        ],
        [
            Paragraph("<b>Safety & Trust Rules</b>", table_cell_bold),
            Paragraph("OTP email verification, Girls-Only / Boys-Only filters, Guardian Badges.", table_cell_style),
            Paragraph("100% peace of mind for female followers and safety-conscious users.", table_cell_style)
        ]
    ]

    t_pillars = Table(pillar_data, colWidths=[1.5*inch, 2.8*inch, 2.7*inch])
    t_pillars.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), primary_color),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, border_color),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, card_bg]),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_pillars)
    story.append(Spacer(1, 10))

    # Step-by-Step Live Demo Script
    story.append(Paragraph("2. Live App Demo Walkthrough (What to Show Him)", h1_style))
    story.append(Paragraph(
        "Hand him your phone running the app at <b>http://127.0.0.1:8090/</b> or open it live on screen. Follow this 5-step demo script:",
        body_style
    ))

    demo_steps = [
        "<b>Step 1: Cold Start Splash (Full-Screen Lottie Animation)</b> — Open the app. Point out the smooth vector full-screen <i>NEEDY</i> animation that creates an instant premium brand impression.",
        "<b>Step 2: Hyperlocal Discover Feed</b> — Show the 6 activity categories (Errands, Company, Food, Sports, Study, Culture) and the 3 Exchange Modes (<i>Paid, Free, Treat</i>).",
        "<b>Step 3: Bored Radar</b> — Open the live neighborhood pulse map showing nearby active zones and real-time community drift.",
        "<b>Step 4: Live Auctions Hub</b> — Show the Live Auctions screen with real-time bidding ticker and 'Buy It Now' instant purchase.",
        "<b>Step 5: Trust & Guardian Safety</b> — Show the safety center, female-only post filter, and verified badge system."
    ]
    for step in demo_steps:
        story.append(Paragraph(f"• {step}", body_style))

    story.append(Spacer(1, 10))

    # Financials & Earnings Calculation
    story.append(Paragraph("3. Revenue Model & Earnings Calculations", h1_style))
    story.append(Paragraph(
        "How <b>needy</b> generates revenue:<br/>"
        "1. <b>5% Platform Commission Fee</b> on all paid micro-gigs and live auctions.<br/>"
        "2. <b>Merchant Partner Perks</b> ($20 - $50 / month per local cafe, gym, or restaurant listing).<br/>"
        "3. <b>Featured Post & Karma Microtransactions</b>.",
        body_style
    ))

    # Earnings Table
    earnings_data = [
        [
            Paragraph("Activity Volume / Month", table_header_style),
            Paragraph("Average Activity Value", table_header_style),
            Paragraph("Total Monthly Volume (GMV)", table_header_style),
            Paragraph("5% Commission Income", table_header_style),
            Paragraph("Merchant Perks & Ads", table_header_style),
            Paragraph("Total Monthly Revenue", table_header_style)
        ],
        [
            Paragraph("<b>1,000 Activities</b><br/>(Initial Pilot Phase)", table_cell_style),
            Paragraph("₹350 ($4.20)", table_cell_style),
            Paragraph("₹3,50,000 ($4,200)", table_cell_style),
            Paragraph("₹17,500 ($210)", table_cell_style),
            Paragraph("₹15,000 ($180)", table_cell_style),
            Paragraph("<b>₹32,500 / month</b><br/>($390/mo)", table_cell_bold)
        ],
        [
            Paragraph("<b>10,000 Activities</b><br/>(Influencer Launch - 5% Conversion)", table_cell_style),
            Paragraph("₹350 ($4.20)", table_cell_style),
            Paragraph("₹35,00,000 ($42,000)", table_cell_style),
            Paragraph("₹1,75,000 ($2,100)", table_cell_style),
            Paragraph("₹75,000 ($900)", table_cell_style),
            Paragraph("<b>₹2,50,000 / month</b><br/>(₹30 Lakhs / year)", table_cell_bold)
        ],
        [
            Paragraph("<b>50,000 Activities</b><br/>(Multi-Zone City Scale)", table_cell_style),
            Paragraph("₹350 ($4.20)", table_cell_style),
            Paragraph("₹1,75,00,000 ($210,000)", table_cell_style),
            Paragraph("₹8,75,000 ($10,500)", table_cell_style),
            Paragraph("₹3,75,000 ($4,500)", table_cell_style),
            Paragraph("<b>₹12,50,000 / month</b><br/>(₹1.5 Crore / year)", table_cell_bold)
        ]
    ]

    t_earnings = Table(earnings_data, colWidths=[1.3*inch, 1.0*inch, 1.2*inch, 1.1*inch, 1.1*inch, 1.3*inch])
    t_earnings.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), secondary_color),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, border_color),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, card_bg]),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_earnings)
    story.append(Spacer(1, 10))

    # Development & Cloud Hosting Cost Breakdown
    story.append(Paragraph("4. Zero-Cost Development & Infrastructure Scaling", h1_style))
    story.append(Paragraph(
        "One of the strongest arguments for this project is <b>lean capital efficiency</b>. "
        "The software architecture has been built with zero upfront infrastructure cost:",
        body_style
    ))

    cost_data = [
        [Paragraph("Growth Stage", table_header_style), Paragraph("Monthly User Traffic", table_header_style), Paragraph("Infrastructure Cost", table_header_style), Paragraph("Platform Profit Margin", table_header_style)],
        [
            Paragraph("<b>Phase 1: Pilot Launch</b>", table_cell_bold),
            Paragraph("0 - 5,000 Active Users", table_cell_style),
            Paragraph("<b>₹0 / Month ($0)</b><br/>Render Free Tier + Neon Postgres Free", table_cell_style),
            Paragraph("<b>100% Margin</b>", table_cell_bold)
        ],
        [
            Paragraph("<b>Phase 2: Initial Scale</b>", table_cell_bold),
            Paragraph("5,000 - 25,000 Active Users", table_cell_style),
            Paragraph("<b>₹1,200 - ₹2,500 / Month</b> ($15-$30/mo)", table_cell_style),
            Paragraph("<b>98.5% Margin</b>", table_cell_bold)
        ],
        [
            Paragraph("<b>Phase 3: High Scale</b>", table_cell_bold),
            Paragraph("25,000 - 100,000 Active Users", table_cell_style),
            Paragraph("<b>₹5,000 - ₹12,000 / Month</b> ($60-$150/mo)", table_cell_style),
            Paragraph("<b>96% Margin</b>", table_cell_bold)
        ]
    ]

    t_cost = Table(cost_data, colWidths=[1.5*inch, 2.0*inch, 2.3*inch, 1.2*inch])
    t_cost.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), primary_color),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, border_color),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, card_bg]),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_cost)
    story.append(Spacer(1, 10))

    # Influencer Offer & Synergy
    story.append(Paragraph("5. What's in it for the Influencer (The Offer)", h1_style))
    story.append(Paragraph(
        "With <b>218,000 followers</b>, the influencer holds the key to user acquisition. Offer him a compelling co-founding partnership:",
        body_style
    ))
    offers = [
        "<b>Co-Founder / Equity Partner (15% - 25% Stake)</b>: Share true upside in a scalable tech business rather than a one-off paid promotion.",
        "<b>Revenue Share</b>: 30% of all platform commission fees generated by users joining via his exclusive referral link/code.",
        "<b>Exclusive Fan Monetization</b>: He can host exclusive live auctions on Needy (e.g. <i>'Tea Walk with Me'</i>, <i>'1-on-1 Career Consultation'</i>) where 100% of proceeds go to him or a charity.",
        "<b>Verified Badge & Featured Ambassador Status</b>: Official lead ambassador presence across the app."
    ]
    for o in offers:
        story.append(Paragraph(f"✔ {o}", body_style))

    story.append(Spacer(1, 10))

    # Critical Things to Take Care Of During the Meeting
    story.append(Paragraph("6. Critical Things to Take Care Of During the Meeting", h1_style))
    warnings = [
        "<b>1. Don't Pitch It As a Dating App</b>: Emphasize that Needy is for micro-tasks, errands, community activities, and tea walks. This keeps the audience quality high and safe.",
        "<b>2. Highlight Female Safety First</b>: Show the <i>Girls-Only filter</i> and <i>Guardian badges</i>. Influencers care deeply about protecting their audience from spam/harassment.",
        "<b>3. Focus on Hyperlocal Density</b>: Explain that we don't need 1 million global users to make money; 2,000 active users in 1 college hub or neighborhood creates full liquidity.",
        "<b>4. Show Ready Code, Not Just Slides</b>: The biggest selling point is that <b>the app is 100% built and ready to deploy today</b>. There is zero technical delay."
    ]
    for w in warnings:
        story.append(Paragraph(f"⚠️ {w}", body_style))

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
