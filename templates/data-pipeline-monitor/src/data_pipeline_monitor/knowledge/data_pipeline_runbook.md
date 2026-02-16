# Data Pipeline Operations Runbook

> Comprehensive operational guide for data pipeline monitoring, troubleshooting, and recovery.
> Last updated: 2026-02-16

## Overview

This runbook covers operational procedures for managing data pipelines including
ETL/ELT jobs, data quality monitoring, alert configuration, and incident recovery.
All pipeline operators and data engineers should be familiar with this document.

---

### Pipeline Monitoring & Health Checks

**Key Metrics to Monitor**

| Metric                 | Description                            | Target SLA              |
| ---------------------- | -------------------------------------- | ----------------------- |
| Execution Success Rate | Percentage of successful pipeline runs | > 99.5%                 |
| Run Duration           | Time to complete a pipeline run        | Within 2x baseline      |
| Data Freshness         | Time since last successful data load   | Per schedule + 15min    |
| Rows Processed         | Number of rows ingested per run        | Within 10% of baseline  |
| Error Count            | Number of errors per run               | 0 for healthy pipelines |
| Resource Utilization   | CPU/memory usage during execution      | < 80% capacity          |

**Monitoring Dashboard**

Access the pipeline monitoring dashboard at: `https://monitoring.internal/pipelines`

Dashboard panels include:

- Pipeline execution timeline (last 24h / 7d / 30d)
- Success/failure heatmap by pipeline
- Latency trend charts
- Data freshness scorecards
- Resource utilization gauges

**Health Check Procedures**

1. Review the dashboard every morning at 09:00 for overnight pipeline status
2. Check for any failed or delayed pipelines
3. Verify data freshness SLAs are met for critical datasets
4. Review resource utilization trends for capacity planning
5. Acknowledge and triage any open alerts

**SLA Definitions**

- **Hourly pipelines**: Data must be available within 75 minutes of schedule
- **Daily pipelines**: Data must be available by 08:00 local time
- **Weekly pipelines**: Data must be available by Monday 06:00
- **Real-time pipelines**: Maximum 5-minute lag tolerance

---

### Common Pipeline Failures & Troubleshooting

**Connection Errors**

Symptoms: `ConnectionError`, `ConnectionRefused`, `TimeoutError` in pipeline logs.

Troubleshooting steps:

1. Verify source system is reachable: `ping <source_host>` or `telnet <host> <port>`
2. Check network connectivity and firewall rules
3. Verify database credentials are valid and not expired
4. Check connection pool limits — increase if hitting max connections
5. Review source system status page for planned maintenance
6. Test with a simple query: `SELECT 1` from the source database

Common root causes:

- Source database restart or maintenance window
- Expired service account credentials
- Network partition or DNS resolution failure
- Connection pool exhaustion

**Timeout Errors**

Symptoms: `TimeoutError`, `StatementTimeout`, `QueryTimeout` in pipeline logs.

Troubleshooting steps:

1. Check if query execution plan has changed (run EXPLAIN ANALYZE)
2. Look for table locks or long-running transactions blocking the pipeline
3. Verify data volume — unexpected spikes can cause timeouts
4. Increase timeout thresholds if data volume has legitimately grown
5. Consider adding indexes to improve query performance
6. Check if parallel queries are competing for resources

**Out of Memory (OOM) Errors**

Symptoms: `MemoryError`, `OOMKilled`, container restart with exit code 137.

Troubleshooting steps:

1. Check container/worker memory limits in orchestrator config
2. Review data volume — OOM often correlates with data spikes
3. Implement chunked processing: break large loads into smaller batches
4. Add memory profiling to identify memory leaks
5. Consider streaming processing instead of loading entire datasets
6. Increase worker memory allocation if data growth is legitimate

**Schema Mismatch Errors**

Symptoms: `SchemaError`, `ColumnNotFound`, `TypeMismatch`, unexpected null values.

Troubleshooting steps:

1. Compare source schema with expected schema in pipeline config
2. Check for recent DDL changes on the source system
3. Review schema drift detection alerts
4. Update pipeline schema mapping to handle new/changed columns
5. Add schema validation step before data loading
6. Coordinate with source system team for schema change notifications

**Permission Denied Errors**

Symptoms: `PermissionDenied`, `AccessDenied`, `InsufficientPrivileges`.

Troubleshooting steps:

1. Verify service account has required permissions (SELECT, INSERT, etc.)
2. Check if permissions were revoked during a security audit
3. Review IAM roles and policies for cloud storage access
4. Verify bucket/container-level permissions for object storage
5. Check row-level security policies that may block access
6. Contact the security team to request permission restoration

---

### Data Quality Checks

**Completeness Checks**

Completeness measures whether all expected data is present.

Validation rules:

- Row count should be within 10% of the previous run
- Required columns must have < 1% null rate
- All expected partitions must be present
- Foreign key references must resolve to parent tables

Remediation:

- Investigate source system for missing data
- Check ETL filters that may be excluding valid records
- Verify incremental load watermarks are correct
- Run a backfill for any missing time partitions

**Freshness Checks**

Freshness measures how recent the data is.

Validation rules:

- Timestamp of newest record should be within the SLA window
- Pipeline last_run timestamp should be within schedule tolerance
- No gaps in time-series data partitions

Remediation:

- Check if the pipeline is running on schedule
- Investigate upstream delays or dependencies
- Verify timezone handling in timestamp comparisons
- Consider adding a heartbeat check for real-time pipelines

**Accuracy Checks**

Accuracy measures whether data values are correct.

Validation rules:

- Numeric values within expected ranges (e.g., price > 0)
- Categorical values match allowed value lists
- Aggregates match source system totals (reconciliation)
- Cross-field consistency checks (e.g., end_date >= start_date)

Remediation:

- Compare pipeline output with source system sample
- Check transformation logic for calculation errors
- Verify encoding/decoding for string fields
- Add data profiling step to detect distribution changes

**Consistency Checks**

Consistency ensures data agrees across systems and tables.

Validation rules:

- Same entity should have consistent values across tables
- Aggregations at different granularities should reconcile
- Historical data should not change unexpectedly (immutability)

Remediation:

- Identify the authoritative source for each data element
- Add cross-table validation queries
- Implement slowly changing dimension (SCD) tracking
- Set up reconciliation reports for critical datasets

**Uniqueness Checks**

Uniqueness ensures no unintended duplicate records.

Validation rules:

- Primary key columns must be unique
- Natural key combinations must be unique
- Deduplication rate should be < 0.1% for clean datasets

Remediation:

- Add DISTINCT or GROUP BY to deduplication logic
- Check for replay/reprocessing that may introduce duplicates
- Verify idempotency of pipeline operations
- Implement upsert (MERGE) instead of blind INSERT

---

### Alert Configuration & Escalation

**Severity Levels**

| Severity      | Description                               | Response SLA      | Examples                                       |
| ------------- | ----------------------------------------- | ----------------- | ---------------------------------------------- |
| P1 - Critical | Data pipeline outage affecting production | 15 minutes        | Complete pipeline failure, data loss risk      |
| P2 - High     | Significant degradation or SLA breach     | 1 hour            | SLA missed, data quality below threshold       |
| P3 - Medium   | Non-critical issue requiring attention    | 4 hours           | Performance degradation, schema drift detected |
| P4 - Low      | Informational or minor issue              | Next business day | Warnings, capacity planning alerts             |

**Notification Channels**

| Channel            | Used For                       | Configuration                           |
| ------------------ | ------------------------------ | --------------------------------------- |
| PagerDuty          | P1/P2 alerts, on-call rotation | Integration key in pipeline config      |
| Slack #data-alerts | All severity levels            | Webhook URL in alert manager            |
| Email              | P2/P3 daily digest             | Distribution list: data-ops@company.com |
| Microsoft Teams    | P3/P4 notifications            | Teams webhook connector                 |

**Escalation Matrix**

| Time Elapsed | Action                       | Contact                  |
| ------------ | ---------------------------- | ------------------------ |
| 0 min        | Auto-notify on-call engineer | PagerDuty rotation       |
| 15 min (P1)  | Escalate to team lead        | Data Engineering Manager |
| 30 min (P1)  | Escalate to director         | VP of Data Platform      |
| 1 hour (P2)  | Escalate to team lead        | Data Engineering Manager |
| 4 hours (P3) | Include in daily standup     | Team triage              |

**Alert Configuration Best Practices**

1. Set meaningful thresholds — avoid alerting on every minor fluctuation
2. Use alert grouping to reduce noise from related failures
3. Add context to alerts: pipeline name, error message, affected datasets
4. Configure alert suppression during planned maintenance windows
5. Review alert volume weekly — tune noisy alerts
6. Test alert routing quarterly to verify contacts are current

---

### Recovery Procedures

**Retry Strategies**

For transient failures (connection errors, timeouts):

1. **Automatic retry**: Configure pipeline orchestrator with exponential backoff
   - First retry: 1 minute delay
   - Second retry: 5 minute delay
   - Third retry: 15 minute delay
   - Maximum retries: 3 (then alert)
2. **Manual retry**: Trigger pipeline re-run from orchestrator UI
   - Clear any failed task states before retrying
   - Verify the root cause is resolved before manual retry
3. **Partial retry**: Re-run only failed tasks in a DAG
   - Use `airflow tasks clear` or equivalent orchestrator command
   - Verify upstream task outputs are still valid

**Rollback Procedures**

For data corruption or bad data loads:

1. Identify the affected pipeline run and timestamp
2. Check if the destination table supports time travel (Snowflake/BigQuery)
3. Use time travel to restore to the last known good state:
   ```sql
   -- Snowflake example
   CREATE OR REPLACE TABLE target_table
   CLONE target_table AT (TIMESTAMP => '2026-02-15T23:00:00Z');
   ```
4. If time travel is not available, restore from backup
5. Verify data integrity after rollback
6. Re-run the pipeline with the fix applied

**Manual Intervention Steps**

When automated recovery fails:

1. Acknowledge the incident in PagerDuty
2. Join the incident Slack channel: #data-incidents
3. Gather diagnostic information:
   - Pipeline logs (last 3 runs)
   - Source system status
   - Destination system status
   - Recent configuration changes
4. Determine root cause category (see Troubleshooting section)
5. Apply the appropriate fix
6. Monitor the next pipeline run
7. Update the incident timeline
8. Write post-incident review (for P1/P2)

**Data Backfill Procedures**

For recovering missing or corrected data:

1. Determine the backfill time range (start_date to end_date)
2. Verify the source data is available for the backfill period
3. Run the pipeline in backfill mode:
   ```bash
   # Airflow example
   airflow dags backfill --start-date 2026-02-10 --end-date 2026-02-15 pipeline_dag
   ```
4. Use a separate backfill pipeline to avoid conflicting with live runs
5. Validate backfilled data against expected counts and checksums
6. Update data freshness metadata after successful backfill
7. Notify downstream consumers of the backfill completion

---

### Pipeline Architecture

**Source Systems**

| System           | Type          | Connection Method   | Refresh Frequency |
| ---------------- | ------------- | ------------------- | ----------------- |
| Salesforce       | CRM           | REST API / Bulk API | Hourly            |
| SAP              | ERP           | RFC / OData         | Daily             |
| PostgreSQL       | OLTP Database | JDBC / CDC          | Every 15 minutes  |
| Google Analytics | Web Analytics | GA4 API             | Daily             |
| Workday          | HRIS          | REST API            | Weekly            |

**Destination Systems**

| System              | Type           | Use Case                            |
| ------------------- | -------------- | ----------------------------------- |
| Snowflake           | Cloud DWH      | Analytics, reporting, ML features   |
| BigQuery            | Cloud DWH      | Marketing analytics, ad-hoc queries |
| Redshift            | Cloud DWH      | Transaction analytics, dashboards   |
| Data Lake (S3/ADLS) | Object Storage | Raw data archive, ML training data  |

**Orchestration Tools**

| Tool             | Environment | Dashboard URL                   |
| ---------------- | ----------- | ------------------------------- |
| Apache Airflow   | Production  | https://airflow.internal/home   |
| Dagster          | Development | https://dagster.internal/runs   |
| Custom Scheduler | Legacy      | https://scheduler.internal/jobs |

**Data Flow Architecture**

```
Source Systems ──► Ingestion Layer ──► Raw Zone ──► Transform ──► Curated Zone ──► Serving
  (APIs/DBs)      (Airflow DAGs)     (Data Lake)   (dbt/Spark)  (Snowflake)     (BI/ML)
```

**Key Architecture Principles**

1. **Idempotency**: All pipelines must produce the same result when re-run
2. **Schema evolution**: Handle schema changes gracefully with backward compatibility
3. **Observability**: Every pipeline must emit metrics, logs, and traces
4. **Data lineage**: Track data provenance from source to destination
5. **Separation of concerns**: Ingestion, transformation, and serving are independent
