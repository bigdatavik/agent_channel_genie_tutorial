# Databricks notebook source
# MAGIC %md
# MAGIC # Genie Room Tutorial – One Notebook Setup
# MAGIC
# MAGIC **Tutorial / shareable setup** — creates the **Genie Room Tutorial - Agent Channel Analytics** room: schema (if needed), tables, synthetic data, `config_genie`, and the Genie space.
# MAGIC
# MAGIC - **Catalog:** Default `payer_catalog_vm` (already created). Provide your own catalog if different.
# MAGIC - **Schema:** Created if it does not exist, or reused if it does.
# MAGIC - **Not part of the main pipeline** — run manually or share for tutorials.

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Configuration (edit these and run)

# COMMAND ----------

# ----- Edit these to match your workspace -----
# Catalog: already created; use payer_catalog_vm or your own.
CATALOG = "payer_catalog_vm"
# Schema: created if not exists, or reused.
SCHEMA = "genie_tutorial"
WAREHOUSE_ID = "your-warehouse-id"  # SQL Warehouse ID from Databricks
GENIE_DISPLAY_NAME = "Genie Room Tutorial - Agent Channel Analytics"
GENIE_DESCRIPTION = "Query agent and broker performance with natural language (tutorial)"

# Optional: seed row counts (defaults shown)
NUM_AGENTS = 100
NUM_LEADS = 500
NUM_POLICIES = 1000
NUM_COMPLIANCE_EVENTS = 200

# COMMAND ----------

# Derived table names (do not edit)
BASE = f"{CATALOG}.{SCHEMA}"
BROKER_PROFILE_TABLE = f"{BASE}.broker_profile"
AGENT_PERFORMANCE_TABLE = f"{BASE}.agent_performance"
LEAD_FACT_TABLE = f"{BASE}.lead_fact"
ENROLLMENT_FACT_TABLE = f"{BASE}.enrollment_fact"
FACT_COMPLIANCE_EVENTS_TABLE = f"{BASE}.fact_compliance_events"
CONFIG_TABLE = f"{BASE}.config_genie"

print(f"Catalog: {CATALOG}, Schema: {SCHEMA}")
print(f"Warehouse: {WAREHOUSE_ID}")
print(f"Genie: {GENIE_DISPLAY_NAME}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Use catalog; create schema if not exists, then use schema

# COMMAND ----------

spark.sql(f"USE CATALOG {CATALOG}")
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {CATALOG}.{SCHEMA}")
spark.sql(f"USE SCHEMA {SCHEMA}")
print(f"Using {CATALOG}.{SCHEMA} (schema created or reused)")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Create tables (five for Genie + config_genie)

# COMMAND ----------

# Gold: broker_profile
spark.sql(f"""
CREATE TABLE IF NOT EXISTS {BROKER_PROFILE_TABLE} (
  broker_id STRING,
  broker_name STRING,
  region STRING,
  agent_count INT,
  enrollments_ytd INT,
  commission_ytd DOUBLE
) USING DELTA
""")
print(f"Table {BROKER_PROFILE_TABLE} OK")

# COMMAND ----------

# Gold: agent_performance
spark.sql(f"""
CREATE TABLE IF NOT EXISTS {AGENT_PERFORMANCE_TABLE} (
  agent_id STRING,
  broker_id STRING,
  region STRING,
  tier STRING,
  enrollments_ytd INT,
  commission_ytd DOUBLE,
  persistency_rate DOUBLE,
  complaint_count INT
) USING DELTA
""")
print(f"Table {AGENT_PERFORMANCE_TABLE} OK")

# COMMAND ----------

# Fact: lead_fact
spark.sql(f"""
CREATE TABLE IF NOT EXISTS {LEAD_FACT_TABLE} (
  lead_id STRING,
  agent_id STRING,
  source STRING,
  campaign_id STRING,
  status STRING,
  created_date DATE,
  score DOUBLE
) USING DELTA
""")
print(f"Table {LEAD_FACT_TABLE} OK")

# COMMAND ----------

# Fact: enrollment_fact
spark.sql(f"""
CREATE TABLE IF NOT EXISTS {ENROLLMENT_FACT_TABLE} (
  enrollment_id STRING,
  agent_id STRING,
  product_type STRING,
  enrollment_date DATE,
  member_region STRING
) USING DELTA
""")
print(f"Table {ENROLLMENT_FACT_TABLE} OK")

# COMMAND ----------

# Fact: fact_compliance_events
spark.sql(f"""
CREATE TABLE IF NOT EXISTS {FACT_COMPLIANCE_EVENTS_TABLE} (
  event_id STRING,
  agent_id STRING,
  event_type STRING,
  severity STRING,
  resolved_flag BOOLEAN,
  event_date DATE
) USING DELTA
""")
print(f"Table {FACT_COMPLIANCE_EVENTS_TABLE} OK")

# COMMAND ----------

# config_genie: key/value for Genie space ID (written after creating the space)
spark.sql(f"""
CREATE TABLE IF NOT EXISTS {CONFIG_TABLE} (
  config_key STRING NOT NULL,
  config_value STRING NOT NULL,
  created_at TIMESTAMP NOT NULL,
  CONSTRAINT config_genie_pk PRIMARY KEY(config_key)
)
USING DELTA
COMMENT 'Configuration for Genie room (e.g. genie_space_id)'
""")
print(f"Table {CONFIG_TABLE} OK")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3b. Create metric view (mv_distribution_performance)

# COMMAND ----------

# Metric view source: agent_performance (base schema). Dimensions and measures only use base columns.
MV_DISTRIBUTION_PERFORMANCE = f"{BASE}.mv_distribution_performance"
yaml_spec = f"""
version: 1.1
comment: "Distribution performance: enrollments, persistency, complaints, commission (tutorial base schema)"
source: {AGENT_PERFORMANCE_TABLE}
dimensions:
  - name: agent_id
    expr: agent_id
  - name: region
    expr: region
  - name: tier
    expr: tier
  - name: broker_id
    expr: broker_id
measures:
  - name: enrolled_members
    expr: sum(enrollments_ytd)
  - name: persistency_12m_avg
    expr: avg(persistency_rate)
  - name: complaint_count_total
    expr: sum(complaint_count)
  - name: commission_ytd_total
    expr: sum(commission_ytd)
"""

spark.sql(f"""
CREATE OR REPLACE VIEW {MV_DISTRIBUTION_PERFORMANCE}
WITH METRICS
LANGUAGE YAML
AS $$
{yaml_spec}
$$
""")
print(f"Metric view {MV_DISTRIBUTION_PERFORMANCE} OK")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Seed synthetic data

# COMMAND ----------

import random
from datetime import date, timedelta
from pyspark.sql.types import StructType, StructField, StringType, IntegerType, DoubleType, BooleanType, DateType

random.seed(42)
regions = ["South", "Midwest", "Northeast", "West"]
tiers = ["Elite", "Premier", "Standard"]

n_agents = min(NUM_AGENTS, 500)
agent_rows = []
for i in range(n_agents):
    agent_rows.append((
        f"agt_{i:04d}",
        f"broker_{i % 20:02d}",
        random.choice(regions),
        random.choice(tiers),
        random.randint(10, 500),
        round(random.uniform(1000, 80000), 2),
        round(random.uniform(0.7, 0.98), 4),
        random.randint(0, 5),
    ))
agent_schema = StructType([
    StructField("agent_id", StringType()),
    StructField("broker_id", StringType()),
    StructField("region", StringType()),
    StructField("tier", StringType()),
    StructField("enrollments_ytd", IntegerType()),
    StructField("commission_ytd", DoubleType()),
    StructField("persistency_rate", DoubleType()),
    StructField("complaint_count", IntegerType()),
])
spark.createDataFrame(agent_rows, agent_schema).write.mode("overwrite").saveAsTable(AGENT_PERFORMANCE_TABLE)
print(f"Wrote {n_agents} rows to {AGENT_PERFORMANCE_TABLE}")

# COMMAND ----------

# Broker profile (aggregate from agents)
from pyspark.sql.functions import col, lit, concat, count, sum as spark_sum
broker_df = spark.table(AGENT_PERFORMANCE_TABLE).groupBy("broker_id", "region").agg(
    count("agent_id").alias("agent_count"),
    spark_sum("enrollments_ytd").alias("enrollments_ytd"),
    spark_sum("commission_ytd").alias("commission_ytd"),
)
broker_df = broker_df.withColumn("broker_name", concat(lit("Broker "), col("broker_id")))
broker_df = broker_df.select(
    col("broker_id"),
    col("broker_name"),
    col("region"),
    col("agent_count").cast("int").alias("agent_count"),
    col("enrollments_ytd").cast("int").alias("enrollments_ytd"),
    col("commission_ytd"),
)
broker_df.write.mode("overwrite").saveAsTable(BROKER_PROFILE_TABLE)
print("Wrote broker_profile")

# COMMAND ----------

# lead_fact
n_leads = min(NUM_LEADS, 2000)
sources = ["web", "referral", "campaign_a", "campaign_b"]
statuses = ["new", "contacted", "qualified", "enrolled", "lost"]
agent_ids = [f"agt_{i:04d}" for i in range(min(n_agents, 100))]
lead_rows = []
for i in range(n_leads):
    lead_rows.append((
        f"lead_{i:06d}",
        random.choice(agent_ids),
        random.choice(sources),
        f"camp_{random.randint(1, 10):02d}",
        random.choice(statuses),
        date.today() - timedelta(days=random.randint(0, 365)),
        round(random.uniform(0.2, 0.95), 4),
    ))
lead_schema = StructType([
    StructField("lead_id", StringType()),
    StructField("agent_id", StringType()),
    StructField("source", StringType()),
    StructField("campaign_id", StringType()),
    StructField("status", StringType()),
    StructField("created_date", DateType()),
    StructField("score", DoubleType()),
])
spark.createDataFrame(lead_rows, lead_schema).write.mode("overwrite").saveAsTable(LEAD_FACT_TABLE)
print(f"Wrote {n_leads} rows to {LEAD_FACT_TABLE}")

# COMMAND ----------

# fact_compliance_events
n_events = min(NUM_COMPLIANCE_EVENTS, 500)
event_types = ["disclosure", "cold_call", "complaint", "documentation"]
severities = ["Low", "Medium", "High", "Critical"]
comp_rows = []
for i in range(n_events):
    comp_rows.append((
        f"evt_{i:05d}",
        random.choice(agent_ids),
        random.choice(event_types),
        random.choice(severities),
        bool(random.randint(0, 1)),
        date.today() - timedelta(days=random.randint(0, 180)),
    ))
comp_schema = StructType([
    StructField("event_id", StringType()),
    StructField("agent_id", StringType()),
    StructField("event_type", StringType()),
    StructField("severity", StringType()),
    StructField("resolved_flag", BooleanType()),
    StructField("event_date", DateType()),
])
spark.createDataFrame(comp_rows, comp_schema).write.mode("overwrite").saveAsTable(FACT_COMPLIANCE_EVENTS_TABLE)
print(f"Wrote {n_events} rows to {FACT_COMPLIANCE_EVENTS_TABLE}")

# COMMAND ----------

# enrollment_fact
n_policies = min(NUM_POLICIES, 5000)
enroll_rows = []
for i in range(n_policies):
    enroll_rows.append((
        f"enr_{i:06d}",
        random.choice(agent_ids),
        random.choice(["MA", "PDP", "MAPD"]),
        date.today() - timedelta(days=random.randint(0, 730)),
        random.choice(regions),
    ))
enroll_schema = StructType([
    StructField("enrollment_id", StringType()),
    StructField("agent_id", StringType()),
    StructField("product_type", StringType()),
    StructField("enrollment_date", DateType()),
    StructField("member_region", StringType()),
])
spark.createDataFrame(enroll_rows, enroll_schema).write.mode("overwrite").saveAsTable(ENROLLMENT_FACT_TABLE)
print(f"Wrote {n_policies} rows to {ENROLLMENT_FACT_TABLE}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 5. Create Genie space

# COMMAND ----------

# MAGIC %pip install databricks-sdk --quiet

# COMMAND ----------

import json
import uuid
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()

# COMMAND ----------

# Drop and recreate only the Genie room created by this notebook (title == GENIE_DISPLAY_NAME).
try:
    resp = w.api_client.do("GET", "/api/2.0/genie/spaces")
    for space in resp.get("spaces", []):
        if space.get("title") == GENIE_DISPLAY_NAME:
            old_id = space.get("space_id")
            w.api_client.do("DELETE", f"/api/2.0/genie/spaces/{old_id}")
            print(f"Deleted existing space '{GENIE_DISPLAY_NAME}' ({old_id})")
            break
except Exception as e:
    print(f"Check/delete existing: {e}")

# COMMAND ----------

# Build serialized_space (tables + metric view, sorted by identifier per API)
tables_sorted = sorted(
    [
        {"identifier": AGENT_PERFORMANCE_TABLE},
        {"identifier": BROKER_PROFILE_TABLE},
        {"identifier": ENROLLMENT_FACT_TABLE},
        {"identifier": LEAD_FACT_TABLE},
        {"identifier": FACT_COMPLIANCE_EVENTS_TABLE},
        {"identifier": MV_DISTRIBUTION_PERFORMANCE},
    ],
    key=lambda x: x["identifier"],
)
text_instructions = f"""This space queries Agent Channel Analytics (Medicare distribution). Tables in {CATALOG}.{SCHEMA}:
1. agent_performance: agent_id, broker_id, region, tier, enrollments_ytd, commission_ytd, persistency_rate, complaint_count
2. broker_profile: broker_id, broker_name, region, agent_count, enrollments_ytd, commission_ytd
3. enrollment_fact: enrollment_id, agent_id, product_type, enrollment_date, member_region
4. lead_fact: lead_id, agent_id, source, campaign_id, status, created_date, score
5. fact_compliance_events: event_id, agent_id, event_type, severity, resolved_flag, event_date
6. mv_distribution_performance (metric view): dimensions agent_id, region, tier, broker_id; measures enrolled_members, persistency_12m_avg, complaint_count_total, commission_ytd_total. Prefer for common KPIs and rollups.

Use these for aggregations and filters. No carrier or client names in queries."""

serialized_space = {
    "version": 1,
    "config": {
        "sample_questions": [
            {"id": str(uuid.uuid4()).replace("-", ""), "question": ["Top 10 agents by enrollments and persistency"]},
            {"id": str(uuid.uuid4()).replace("-", ""), "question": ["Leads by source and conversion rate"]},
            {"id": str(uuid.uuid4()).replace("-", ""), "question": ["Compliance events by agent"]},
            {"id": str(uuid.uuid4()).replace("-", ""), "question": ["Broker performance by region"]}
        ]
    },
    "instructions": {
        "text_instructions": [
            {"id": str(uuid.uuid4()).replace("-", ""), "content": [text_instructions]}
        ]
    },
    "data_sources": {
        "tables": tables_sorted
    }
}

payload = {
    "title": GENIE_DISPLAY_NAME,
    "description": GENIE_DESCRIPTION,
    "warehouse_id": WAREHOUSE_ID,
    "serialized_space": json.dumps(serialized_space)
}

response = w.api_client.do("POST", "/api/2.0/genie/spaces", body=payload)
GENIE_SPACE_ID = response.get("space_id")
print(f"Genie Space created: {GENIE_SPACE_ID}")

# COMMAND ----------

# Save genie_space_id to config_genie
spark.sql(f"USE CATALOG {CATALOG}")
spark.sql(f"USE SCHEMA {SCHEMA}")
spark.sql(f"""
MERGE INTO {CONFIG_TABLE} t
USING (
  SELECT 'genie_space_id' as config_key, '{GENIE_SPACE_ID}' as config_value, current_timestamp() as created_at
) s
ON t.config_key = s.config_key
WHEN MATCHED THEN UPDATE SET t.config_value = s.config_value, t.created_at = s.created_at
WHEN NOT MATCHED THEN INSERT (config_key, config_value, created_at) VALUES (s.config_key, s.config_value, s.created_at)
""")
print(f"Genie space ID saved to {CONFIG_TABLE}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Done
# MAGIC
# MAGIC Next: use the docs in this folder to refine the Genie room (Instructions, Joins, UDFs) and follow **GENIE_TUTORIAL_EXPLORE.md** to explore the room step by step.
# MAGIC
# MAGIC **Manual:** If an app uses this Genie room, grant **Can Run** on this Genie space to the app's service principal (Share → add principal → Can Run).
