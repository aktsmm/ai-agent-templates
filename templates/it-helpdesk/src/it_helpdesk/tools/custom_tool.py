"""Custom tools for the IT helpdesk agent."""

from crewai.tools import tool


@tool("search_knowledge_base")
def search_knowledge_base(query: str) -> str:
    """Search the IT knowledge base for troubleshooting guides and procedures.

    Use this tool to find relevant IT support articles, FAQs, and
    step-by-step guides based on the employee's issue description.

    Args:
        query: The search query based on the employee's IT issue.

    Returns:
        Matching knowledge base articles and procedures.
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
    return f"No knowledge base articles found for: {query}"


@tool("lookup_ticket")
def lookup_ticket(ticket_id: str) -> str:
    """Look up an existing IT support ticket by ticket ID.

    Use this tool to check the current status and details of an
    employee's IT support ticket.

    Args:
        ticket_id: The ticket ID to look up (e.g., TKT-001).

    Returns:
        Ticket status and details.
    """
    sample_tickets = {
        "TKT-001": {
            "status": "In Progress",
            "category": "password_reset",
            "summary": "Account lockout after failed MFA attempts",
            "assignee": "IAM Team",
            "priority": "High",
            "created": "2026-02-14 09:30",
            "updated": "2026-02-14 10:15",
            "notes": "User verified via manager callback. Temporary password issued.",
        },
        "TKT-002": {
            "status": "Open",
            "category": "software_issue",
            "summary": "Microsoft Teams crashes on startup after update",
            "assignee": "Software Support",
            "priority": "Medium",
            "created": "2026-02-14 11:00",
            "updated": "2026-02-14 11:00",
            "notes": "Awaiting remote session to collect crash logs.",
        },
        "TKT-003": {
            "status": "Resolved",
            "category": "network_issue",
            "summary": "VPN disconnects every 30 minutes",
            "assignee": "Network Engineering",
            "priority": "Medium",
            "created": "2026-02-13 14:00",
            "updated": "2026-02-14 16:30",
            "notes": "Root cause: split-tunnel config conflict. Updated VPN profile.",
        },
        "TKT-004": {
            "status": "Waiting for Parts",
            "category": "hardware_issue",
            "summary": "Laptop keyboard keys sticking — replacement needed",
            "assignee": "Hardware Support",
            "priority": "Low",
            "created": "2026-02-12 10:00",
            "updated": "2026-02-14 09:00",
            "notes": "Replacement keyboard ordered. ETA 3 business days.",
        },
        "TKT-005": {
            "status": "Escalated",
            "category": "network_issue",
            "summary": "Entire floor losing Wi-Fi intermittently",
            "assignee": "Network Engineering",
            "priority": "Critical",
            "created": "2026-02-14 08:00",
            "updated": "2026-02-14 12:00",
            "notes": "AP firmware issue identified. Maintenance window scheduled tonight.",
        },
    }

    ticket = sample_tickets.get(ticket_id.upper())
    if ticket:
        lines = [
            f"**{k.replace('_', ' ').title()}**: {v}"
            for k, v in ticket.items()
        ]
        return "\n".join(lines)
    return (
        f"Ticket not found: {ticket_id}. "
        "Please check the ticket ID and try again."
    )


@tool("check_system_status")
def check_system_status(service_name: str) -> str:
    """Check the current status of an IT service or system.

    Use this tool to check if a service is experiencing any outages
    or degraded performance.

    Args:
        service_name: The name of the service to check
            (e.g., vpn, email, teams, wifi, erp).

    Returns:
        Current service status information.
    """
    service_statuses = {
        "vpn": {
            "service": "Corporate VPN (GlobalProtect)",
            "status": "Operational",
            "uptime": "99.8%",
            "last_incident": "2026-02-10 — Brief outage during maintenance",
            "notes": "All VPN gateways healthy.",
        },
        "email": {
            "service": "Email (Microsoft 365 Exchange Online)",
            "status": "Operational",
            "uptime": "99.95%",
            "last_incident": "2026-01-28 — Delayed delivery for 15 minutes",
            "notes": "All mailflow normal.",
        },
        "teams": {
            "service": "Microsoft Teams",
            "status": "Degraded",
            "uptime": "98.5%",
            "last_incident": "2026-02-15 — Screen sharing issues reported",
            "notes": "Microsoft investigating. Workaround: use browser version.",
        },
        "wifi": {
            "service": "Corporate Wi-Fi (CorpNet / GuestNet)",
            "status": "Partial Outage",
            "uptime": "97.2%",
            "last_incident": "2026-02-14 — Floor 3 AP firmware issue",
            "notes": "Floor 3 intermittent. Fix scheduled tonight.",
        },
        "erp": {
            "service": "SAP ERP System",
            "status": "Operational",
            "uptime": "99.9%",
            "last_incident": "2026-02-01 — Planned maintenance window",
            "notes": "All modules operational.",
        },
        "printing": {
            "service": "Network Printing (PaperCut)",
            "status": "Operational",
            "uptime": "99.5%",
            "last_incident": "2026-02-08 — Print queue stuck on Floor 2",
            "notes": "All printers online.",
        },
        "active_directory": {
            "service": "Active Directory / Azure AD",
            "status": "Operational",
            "uptime": "99.99%",
            "last_incident": "2026-01-15 — Sync delay resolved",
            "notes": "All domain controllers healthy. Azure AD Connect syncing.",
        },
    }

    key = service_name.strip().lower().replace(" ", "_")
    status = service_statuses.get(key)
    if status:
        lines = [
            f"**{k.replace('_', ' ').title()}**: {v}"
            for k, v in status.items()
        ]
        return "\n".join(lines)

    available = ", ".join(sorted(service_statuses.keys()))
    return (
        f"Service '{service_name}' not found. "
        f"Available services: {available}"
    )
