"""Custom tools for the sales lead qualifier agent."""

from crewai.tools import tool


@tool("search_lead_database")
def search_lead_database(query: str) -> str:
    """Search the lead database for matching companies or prospects.

    Use this tool to find information about leads, companies, contacts,
    or industry data from the knowledge base.

    Args:
        query: The search query (company name, industry, person name, etc.).

    Returns:
        Matching lead and company information from the database.
    """
    from pathlib import Path

    knowledge_dir = Path(__file__).parent.parent / "knowledge"
    results: list[str] = []

    for file in knowledge_dir.glob("*.md"):
        content = file.read_text(encoding="utf-8")
        sections = content.split("\n### ")
        for section in sections:
            if query.lower() in section.lower():
                results.append(section.strip()[:800])

    if results:
        return "\n\n---\n\n".join(results[:10])
    return f"No leads found matching: {query}"


@tool("lookup_company")
def lookup_company(company_name: str) -> str:
    """Look up detailed company information by name.

    Use this tool to retrieve a specific company's profile including
    industry, size, contacts, technology stack, and BANT indicators.

    Args:
        company_name: The company name to look up (e.g., "Acme Corp").

    Returns:
        Detailed company profile and lead information.
    """
    # In production, replace with CRM API (Salesforce, HubSpot, etc.)
    # This returns sample data for the template
    sample_companies = {
        "techflow solutions": {
            "name": "TechFlow Solutions",
            "industry": "SaaS / Developer Tools",
            "size": "250 employees",
            "revenue": "$45M ARR",
            "headquarters": "Austin, TX",
            "website": "techflow.example.com",
            "key_contacts": [
                "Sarah Chen — VP of Engineering (decision-maker)",
                "Mike Rodriguez — CTO (executive sponsor)",
                "Lisa Park — Engineering Manager (champion)",
            ],
            "tech_stack": "AWS, React, PostgreSQL, Jenkins (legacy CI/CD)",
            "pain_points": "Slow deployment cycles, CI/CD bottlenecks, scaling issues",
            "budget_signal": "Recently raised Series B ($30M) — actively investing in tooling",
            "timeline_signal": "Q2 initiative to modernize DevOps pipeline",
            "current_solution": "Jenkins + custom scripts",
            "score": 82,
            "status": "Hot",
        },
        "globalmart retail": {
            "name": "GlobalMart Retail",
            "industry": "E-commerce / Retail",
            "size": "1,200 employees",
            "revenue": "$180M ARR",
            "headquarters": "Chicago, IL",
            "website": "globalmart.example.com",
            "key_contacts": [
                "James Wilson — Director of IT (evaluator)",
                "Priya Sharma — VP of Operations (decision-maker)",
            ],
            "tech_stack": "Azure, .NET, SQL Server, Shopify Plus",
            "pain_points": "Inventory management, omnichannel integration, peak season scaling",
            "budget_signal": "Annual IT budget $12M — current vendor contract renewing in 6 months",
            "timeline_signal": "Evaluating options for Q3, no hard deadline",
            "current_solution": "Custom .NET inventory system",
            "score": 65,
            "status": "Warm",
        },
        "greenleaf energy": {
            "name": "GreenLeaf Energy",
            "industry": "Clean Energy / Sustainability",
            "size": "80 employees",
            "revenue": "$8M ARR",
            "headquarters": "Portland, OR",
            "website": "greenleaf.example.com",
            "key_contacts": [
                "Tom Baker — Founder & CEO (decision-maker, but stretched thin)",
            ],
            "tech_stack": "Google Cloud, Python, basic spreadsheets for CRM",
            "pain_points": "Manual processes, no CRM, small team wearing many hats",
            "budget_signal": "Bootstrapped — limited budget, looking for free/low-cost tiers",
            "timeline_signal": "No defined timeline, 'maybe next year'",
            "current_solution": "Spreadsheets + manual email tracking",
            "score": 28,
            "status": "Cold",
        },
        "medicore health": {
            "name": "MediCore Health",
            "industry": "Healthcare Technology",
            "size": "500 employees",
            "revenue": "$72M ARR",
            "headquarters": "Boston, MA",
            "website": "medicore.example.com",
            "key_contacts": [
                "Dr. Angela Martinez — Chief Medical Officer",
                "Kevin O'Brien — VP of Product (decision-maker)",
                "Rachel Kim — Head of Data Science (technical evaluator)",
            ],
            "tech_stack": "AWS, Python, HIPAA-compliant infrastructure, Snowflake",
            "pain_points": "Data silos, compliance overhead, slow analytics pipeline",
            "budget_signal": "$2M allocated for data platform modernization in FY2026",
            "timeline_signal": "RFP due by end of Q1, decision by Q2",
            "current_solution": "Legacy on-prem data warehouse + Tableau",
            "score": 91,
            "status": "Hot",
        },
        "pinnacle consulting": {
            "name": "Pinnacle Consulting Group",
            "industry": "Management Consulting",
            "size": "150 employees",
            "revenue": "$25M ARR",
            "headquarters": "New York, NY",
            "website": "pinnacle-consulting.example.com",
            "key_contacts": [
                "David Park — Managing Partner (decision-maker)",
                "Sophie Turner — Director of Operations (champion)",
            ],
            "tech_stack": "Microsoft 365, Power BI, Salesforce, custom SharePoint apps",
            "pain_points": (
                "Knowledge management, consultant utilization tracking, client reporting"
            ),
            "budget_signal": "Mid-range budget, prefers annual contracts under $100K",
            "timeline_signal": "Active evaluation, comparing 3 vendors this month",
            "current_solution": "Salesforce + SharePoint + Power BI",
            "score": 74,
            "status": "Warm",
        },
    }

    company = sample_companies.get(company_name.lower().strip())
    if company:
        lines = [f"**{k.replace('_', ' ').title()}**: {v}" for k, v in company.items()
                 if k != "key_contacts"]
        contacts = company["key_contacts"]
        lines.append("**Key Contacts**:")
        for contact in contacts:
            lines.append(f"  - {contact}")
        return "\n".join(lines)
    return (
        f"Company not found: {company_name}. "
        f"Available companies: {', '.join(c['name'] for c in sample_companies.values())}"
    )
