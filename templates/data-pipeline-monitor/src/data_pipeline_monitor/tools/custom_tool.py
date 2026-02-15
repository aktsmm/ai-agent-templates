"""Custom tools for the data pipeline monitor agent."""

from crewai.tools import tool


@tool("check_pipeline_status")
def check_pipeline_status(pipeline_id: str) -> str:
    """Check the current execution status and performance metrics of a data pipeline.

    Use this tool to look up a pipeline's run status, duration,
    throughput, error count, and scheduling information.

    Args:
        pipeline_id: The pipeline ID to check (e.g., ETL-001).

    Returns:
        Pipeline status and performance metrics.
    """
    sample_pipelines = {
        "ETL-001": {
            "name": "Customer Data Sync",
            "source": "Salesforce",
            "destination": "Snowflake",
            "schedule": "hourly",
            "status": "running",
            "last_run": "2026-02-16T08:00:00Z",
            "duration_min": 12,
            "rows_processed": 45230,
            "error_count": 0,
        },
        "ETL-002": {
            "name": "Product Inventory Update",
            "source": "SAP",
            "destination": "BigQuery",
            "schedule": "daily",
            "status": "completed",
            "last_run": "2026-02-16T06:00:00Z",
            "duration_min": 45,
            "rows_processed": 128500,
            "error_count": 0,
        },
        "ETL-003": {
            "name": "Transaction Log ETL",
            "source": "PostgreSQL",
            "destination": "Redshift",
            "schedule": "every_15min",
            "status": "failed",
            "last_run": "2026-02-16T07:45:00Z",
            "duration_min": 3,
            "rows_processed": 0,
            "error_count": 5,
            "last_error": "ConnectionError: Unable to connect to source database",
        },
        "ETL-004": {
            "name": "Marketing Analytics",
            "source": "Google Analytics",
            "destination": "Snowflake",
            "schedule": "daily",
            "status": "delayed",
            "last_run": "2026-02-15T23:00:00Z",
            "duration_min": 0,
            "rows_processed": 0,
            "error_count": 0,
            "delay_reason": "Upstream dependency not ready",
        },
        "ETL-005": {
            "name": "HR Payroll Export",
            "source": "Workday",
            "destination": "Data Lake",
            "schedule": "weekly",
            "status": "scheduled",
            "next_run": "2026-02-17T02:00:00Z",
            "last_run": "2026-02-10T02:00:00Z",
            "duration_min": 90,
            "rows_processed": 52000,
            "error_count": 0,
        },
    }

    key = pipeline_id.strip().upper()
    pipeline = sample_pipelines.get(key)
    if pipeline:
        lines = [
            f"**{k.replace('_', ' ').title()}**: {v}"
            for k, v in pipeline.items()
        ]
        return "\n".join(lines)

    available = ", ".join(sorted(sample_pipelines.keys()))
    return (
        f"Pipeline not found: {pipeline_id}. "
        f"Available pipelines: {available}"
    )


@tool("query_data_metrics")
def query_data_metrics(dataset_name: str) -> str:
    """Query data quality metrics for a specific dataset.

    Use this tool to check data completeness, freshness, schema drift,
    null rates, duplicate rates, and row counts for a dataset.

    Args:
        dataset_name: The dataset name to query (e.g., customers, products).

    Returns:
        Data quality metrics for the specified dataset.
    """
    sample_metrics = {
        "customers": {
            "table": "dim_customers",
            "row_count": 1250000,
            "completeness_pct": 99.2,
            "freshness": "2026-02-16T08:15:00Z",
            "schema_drift": False,
            "null_rate_pct": 0.8,
            "duplicate_rate_pct": 0.02,
        },
        "products": {
            "table": "dim_products",
            "row_count": 85000,
            "completeness_pct": 97.5,
            "freshness": "2026-02-16T06:30:00Z",
            "schema_drift": True,
            "drift_details": "New column 'sustainability_score' detected",
            "null_rate_pct": 2.5,
            "duplicate_rate_pct": 0.1,
        },
        "transactions": {
            "table": "fact_transactions",
            "row_count": 15000000,
            "completeness_pct": 100.0,
            "freshness": "2026-02-16T07:45:00Z",
            "schema_drift": False,
            "null_rate_pct": 0.0,
            "duplicate_rate_pct": 0.0,
        },
        "marketing_events": {
            "table": "fact_marketing_events",
            "row_count": 320000,
            "completeness_pct": 85.3,
            "freshness": "2026-02-15T23:00:00Z",
            "schema_drift": False,
            "null_rate_pct": 14.7,
            "duplicate_rate_pct": 1.2,
        },
        "payroll": {
            "table": "fact_payroll",
            "row_count": 52000,
            "completeness_pct": 100.0,
            "freshness": "2026-02-10T02:00:00Z",
            "schema_drift": False,
            "null_rate_pct": 0.0,
            "duplicate_rate_pct": 0.0,
        },
    }

    key = dataset_name.strip().lower().replace(" ", "_")
    metrics = sample_metrics.get(key)
    if metrics:
        lines = [
            f"**{k.replace('_', ' ').title()}**: {v}"
            for k, v in metrics.items()
        ]
        return "\n".join(lines)

    available = ", ".join(sorted(sample_metrics.keys()))
    return (
        f"Dataset not found: {dataset_name}. "
        f"Available datasets: {available}"
    )


@tool("search_runbook")
def search_runbook(query: str) -> str:
    """Search the data pipeline runbook for operational procedures and troubleshooting guides.

    Use this tool to find relevant runbook sections covering pipeline monitoring,
    failure troubleshooting, data quality checks, alert configuration, and
    recovery procedures.

    Args:
        query: The search query based on the operator's issue.

    Returns:
        Matching runbook sections and procedures.
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
    return f"No runbook articles found for: {query}"
