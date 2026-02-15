"""Custom tools for the HR onboarding assistant."""

from crewai.tools import tool


@tool("search_onboarding_guide")
def search_onboarding_guide(query: str) -> str:
    """Search the onboarding knowledge base for procedures, checklists, and policies.

    Use this tool to find relevant onboarding articles, HR forms,
    training schedules, and step-by-step guides for new hire processes.

    Args:
        query: The search query based on the onboarding request.

    Returns:
        Matching onboarding guide articles and procedures.
    """
    from pathlib import Path

    knowledge_dir = Path(__file__).parent.parent / "knowledge"
    results: list[str] = []

    for file in knowledge_dir.glob("*.md"):
        content = file.read_text(encoding="utf-8")
        sections = content.split("\n### ")
        for section in sections:
            lower_section = section.lower()
            query_lower = query.lower()
            if query_lower in lower_section:
                idx = lower_section.index(query_lower)
                start = max(0, idx - 200)
                end = min(len(section), idx + 600)
                snippet = section[start:end].strip()
                results.append(snippet[:800])

    if results:
        return "\n\n---\n\n".join(results[:10])
    return f"No onboarding guide articles found for: {query}"


@tool("lookup_employee")
def lookup_employee(employee_id: str) -> str:
    """Look up a new hire's onboarding record by employee ID.

    Use this tool to check the current onboarding status, assigned
    department, start date, and completed steps for a new hire.

    Args:
        employee_id: The employee ID to look up (e.g., EMP-001).

    Returns:
        Employee onboarding status and details.
    """
    sample_employees = {
        "EMP-001": {
            "name": "Alice Johnson",
            "department": "Engineering",
            "role": "Software Engineer",
            "start_date": "2026-03-01",
            "manager": "Bob Smith",
            "location": "Tokyo Office",
            "status": "pre-boarding",
            "documents": {
                "contract": "signed",
                "tax_forms": "pending",
                "id_verification": "completed",
                "bank_details": "pending",
            },
            "it_setup": {
                "laptop": "ordered",
                "email": "not_started",
                "vpn": "not_started",
                "badge": "not_started",
            },
            "training": {
                "orientation": "scheduled_2026-03-01",
                "compliance": "not_started",
                "role_specific": "not_started",
            },
            "buddy": "not_assigned",
        },
        "EMP-002": {
            "name": "Carlos Rivera",
            "department": "Marketing",
            "role": "Content Strategist",
            "start_date": "2026-02-24",
            "manager": "Diana Chen",
            "location": "Osaka Office",
            "status": "in_progress",
            "documents": {
                "contract": "signed",
                "tax_forms": "completed",
                "id_verification": "completed",
                "bank_details": "completed",
            },
            "it_setup": {
                "laptop": "ready",
                "email": "created",
                "vpn": "configured",
                "badge": "ready_for_pickup",
            },
            "training": {
                "orientation": "scheduled_2026-02-24",
                "compliance": "scheduled_2026-02-25",
                "role_specific": "scheduled_2026-03-03",
            },
            "buddy": "assigned_to_Yuki_Tanaka",
        },
        "EMP-003": {
            "name": "Fatima Al-Hassan",
            "department": "Finance",
            "role": "Financial Analyst",
            "start_date": "2026-03-15",
            "manager": "George Wilson",
            "location": "Remote (Nagoya)",
            "status": "pre-boarding",
            "documents": {
                "contract": "sent_awaiting_signature",
                "tax_forms": "not_started",
                "id_verification": "not_started",
                "bank_details": "not_started",
            },
            "it_setup": {
                "laptop": "not_started",
                "email": "not_started",
                "vpn": "not_started",
                "badge": "not_applicable_remote",
            },
            "training": {
                "orientation": "not_scheduled",
                "compliance": "not_scheduled",
                "role_specific": "not_scheduled",
            },
            "buddy": "not_assigned",
        },
        "EMP-004": {
            "name": "Kenji Yamamoto",
            "department": "Sales",
            "role": "Account Executive",
            "start_date": "2026-02-17",
            "manager": "Lisa Park",
            "location": "Tokyo Office",
            "status": "completed",
            "documents": {
                "contract": "signed",
                "tax_forms": "completed",
                "id_verification": "completed",
                "bank_details": "completed",
            },
            "it_setup": {
                "laptop": "delivered",
                "email": "active",
                "vpn": "active",
                "badge": "activated",
            },
            "training": {
                "orientation": "completed",
                "compliance": "in_progress",
                "role_specific": "scheduled_2026-02-24",
            },
            "buddy": "assigned_to_Mei_Suzuki",
        },
        "EMP-005": {
            "name": "Priya Nair",
            "department": "Human Resources",
            "role": "HR Business Partner",
            "start_date": "2026-03-10",
            "manager": "Tom Anderson",
            "location": "Tokyo Office",
            "status": "pre-boarding",
            "documents": {
                "contract": "signed",
                "tax_forms": "completed",
                "id_verification": "pending",
                "bank_details": "pending",
            },
            "it_setup": {
                "laptop": "ordered",
                "email": "not_started",
                "vpn": "not_started",
                "badge": "not_started",
            },
            "training": {
                "orientation": "scheduled_2026-03-10",
                "compliance": "not_scheduled",
                "role_specific": "not_scheduled",
            },
            "buddy": "not_assigned",
        },
    }

    if employee_id.upper() in sample_employees:
        emp = sample_employees[employee_id.upper()]
        lines = [
            f"Employee: {emp['name']} ({employee_id.upper()})",
            f"Department: {emp['department']} | Role: {emp['role']}",
            f"Start Date: {emp['start_date']} | Location: {emp['location']}",
            f"Manager: {emp['manager']}",
            f"Overall Status: {emp['status']}",
            "",
            "Documents:",
        ]
        for doc, status in emp["documents"].items():
            lines.append(f"  - {doc}: {status}")
        lines.append("")
        lines.append("IT Setup:")
        for item, status in emp["it_setup"].items():
            lines.append(f"  - {item}: {status}")
        lines.append("")
        lines.append("Training:")
        for item, status in emp["training"].items():
            lines.append(f"  - {item}: {status}")
        lines.append("")
        lines.append(f"Buddy: {emp['buddy']}")

        return "\n".join(lines)

    return f"Employee not found: {employee_id}. Valid IDs: EMP-001 to EMP-005."


@tool("check_onboarding_status")
def check_onboarding_status(department: str) -> str:
    """Check the onboarding pipeline status for a department or company-wide.

    Use this tool to see how many new hires are in each stage of
    onboarding and identify any bottlenecks or overdue items.

    Args:
        department: Department name or 'all' for company-wide status.

    Returns:
        Onboarding pipeline status summary.
    """
    pipeline_data = {
        "engineering": {
            "pre_boarding": 3,
            "week_1": 1,
            "week_2_4": 2,
            "month_2_3": 1,
            "completed": 15,
            "overdue_items": ["EMP-001: tax forms due in 5 days"],
        },
        "marketing": {
            "pre_boarding": 1,
            "week_1": 2,
            "week_2_4": 0,
            "month_2_3": 1,
            "completed": 8,
            "overdue_items": [],
        },
        "sales": {
            "pre_boarding": 2,
            "week_1": 1,
            "week_2_4": 1,
            "month_2_3": 0,
            "completed": 12,
            "overdue_items": ["EMP-004: compliance training overdue by 2 days"],
        },
        "finance": {
            "pre_boarding": 1,
            "week_1": 0,
            "week_2_4": 1,
            "month_2_3": 0,
            "completed": 6,
            "overdue_items": [],
        },
        "human resources": {
            "pre_boarding": 1,
            "week_1": 0,
            "week_2_4": 0,
            "month_2_3": 0,
            "completed": 4,
            "overdue_items": ["EMP-005: ID verification due in 3 days"],
        },
    }

    dept_key = department.strip().lower()

    if dept_key == "all":
        lines = ["=== Company-Wide Onboarding Status ===", ""]
        total = {
            "pre_boarding": 0, "week_1": 0, "week_2_4": 0,
            "month_2_3": 0, "completed": 0,
        }
        all_overdue: list[str] = []

        for dept_name, data in pipeline_data.items():
            for key in total:
                total[key] += data[key]
            all_overdue.extend(data["overdue_items"])

        lines.append(f"Pre-boarding: {total['pre_boarding']}")
        lines.append(f"Week 1 (Orientation): {total['week_1']}")
        lines.append(f"Week 2-4 (Ramp-up): {total['week_2_4']}")
        lines.append(f"Month 2-3 (Integration): {total['month_2_3']}")
        lines.append(f"Completed: {total['completed']}")
        lines.append("")
        if all_overdue:
            lines.append("⚠ Overdue Items:")
            for item in all_overdue:
                lines.append(f"  - {item}")
        else:
            lines.append("✓ No overdue items")

        return "\n".join(lines)

    if dept_key in pipeline_data:
        data = pipeline_data[dept_key]
        lines = [
            f"=== {department.title()} Onboarding Status ===",
            "",
            f"Pre-boarding: {data['pre_boarding']}",
            f"Week 1 (Orientation): {data['week_1']}",
            f"Week 2-4 (Ramp-up): {data['week_2_4']}",
            f"Month 2-3 (Integration): {data['month_2_3']}",
            f"Completed: {data['completed']}",
            "",
        ]
        if data["overdue_items"]:
            lines.append("⚠ Overdue Items:")
            for item in data["overdue_items"]:
                lines.append(f"  - {item}")
        else:
            lines.append("✓ No overdue items")

        return "\n".join(lines)

    available = ", ".join(pipeline_data.keys()) + ", all"
    return f"Department not found: {department}. Available: {available}"
