# Genie Room Tutorial – Complete Guide

**Use this guide** so you can run the notebook, configure the **Genie Room Tutorial - Agent Channel Analytics**, and explore it end-to-end.

**Convention:** Replace `YOUR_CATALOG.YOUR_SCHEMA` everywhere with your catalog and schema (e.g. `payer_catalog_vm.genie_tutorial`).

**Printing:** This guide is formatted so content is not cut off when printed in portrait. Wide tables are split into blocks or lists; long SQL is in code blocks so it wraps.

---

## Quick start (4 steps)

1. **Edit** the notebook `One_Notebook_Genie_Room_Setup.py`: set `CATALOG`, `SCHEMA`, and `WAREHOUSE_ID`.
2. **Run** the notebook from top to bottom (creates schema, tables, data, metric view, Genie space).
3. **Configure** the room in Databricks Genie (Instructions → Text, Joins, SQL Expressions, SQL Queries, Benchmarks) using the sections below.
4. **Explore** the room: start the SQL warehouse, then ask questions in Chat and Agent mode.

---

# Part 1: Run the setup

## 1.1 What you need

- Databricks workspace with Genie and a SQL warehouse.
- In the notebook's top cells, set:
  - **CATALOG** – e.g. `payer_catalog_vm` (must already exist).
  - **SCHEMA** – e.g. `genie_tutorial` (created if it doesn't exist).
  - **WAREHOUSE_ID** – your SQL warehouse ID.

## 1.2 What the notebook creates

- Schema (if not exists), five tables, synthetic data, metric view `mv_distribution_performance`, Genie space **Genie Room Tutorial - Agent Channel Analytics**, and `config_genie` with the space ID.
- The room is recreated each run (drop + create for this room only); other Genie rooms are untouched.

---

# Part 2: Data at a glance

Use this when writing instructions or SQL.

## 2.1 Tables (base schema)

- **agent_performance:** agent_id, broker_id, region, tier, enrollments_ytd, commission_ytd, persistency_rate, complaint_count
- **broker_profile:** broker_id, broker_name, region, agent_count, enrollments_ytd, commission_ytd
- **lead_fact:** lead_id, agent_id, source, campaign_id, status, created_date, score
- **enrollment_fact:** enrollment_id, agent_id, product_type, enrollment_date, member_region
- **fact_compliance_events:** event_id, agent_id, event_type, severity, resolved_flag, event_date

## 2.2 Metric view

- **mv_distribution_performance**  
  Dimensions: agent_id, region, tier, broker_id  
  Measures: enrolled_members, persistency_12m_avg, complaint_count_total, commission_ytd_total

## 2.3 Metric views: what they are and how they're used in this room

**What metric views are**

Metric views are a Unity Catalog feature that define a **semantic layer** over your data: **dimensions** (attributes to group or filter by) and **measures** (aggregations like sums and averages). They are created with `CREATE VIEW ... WITH METRICS LANGUAGE YAML` and sit on top of a table or view. Genie (and other tools) can query them so users get consistent KPIs without writing the aggregation logic each time.

**How this Genie room uses the metric view**

- The notebook creates **mv_distribution_performance** (section 3b), built on **agent_performance**. It exposes dimensions (agent_id, region, tier, broker_id) and measures (enrolled_members, persistency_12m_avg, complaint_count_total, commission_ytd_total).
- The Genie space **data sources** include both the five tables and this metric view. So Genie can choose either the raw tables or the metric view when answering.
- The room's **text instructions** tell Genie to prefer the metric view for "common KPIs and rollups." That steers Genie to use it when the question fits the metric view's dimensions and measures.

**Tables vs metric view in this room**

- **Use the tables** when the question needs: lead-level or conversion data (lead_fact), compliance events (fact_compliance_events), broker names and row-level detail (broker_profile), enrollment detail (enrollment_fact), or custom filters/columns that aren't in the metric view.
- **Use the metric view** when the question is about agent/channel **KPIs** that match its dimensions and measures: enrollments (or “enrolled members”), persistency, complaint totals, or commission totals, grouped or filtered by agent, region, tier, or broker.

**What kind of queries use the metric view**

Queries that ask for aggregated agent or channel performance by the metric view's dimensions. Examples:

- Enrolled members (or enrollment volume) by agent, region, tier, or broker.
- Average persistency by region or tier.
- Total complaints or commission by agent or broker.
- Comparisons across regions or tiers using those measures.

**Example natural-language questions that can use the metric view**

- "Enrolled members by region"
- "Average persistency by tier"
- "Total commission by broker"
- "Top agents by enrolled members"
- "Complaint totals by region"

**Example SQL (what Genie might generate against the metric view)**

```sql
-- Enrolled members by region
SELECT region, enrolled_members, persistency_12m_avg, complaint_count_total, commission_ytd_total
FROM YOUR_CATALOG.YOUR_SCHEMA.mv_distribution_performance
GROUP BY region, enrolled_members, persistency_12m_avg, complaint_count_total, commission_ytd_total;

-- Or with proper aggregation (metric view may expose pre-aggregated or granular rows depending on definition):
SELECT region, sum(enrolled_members) AS enrolled_members, avg(persistency_12m_avg) AS persistency_avg
FROM YOUR_CATALOG.YOUR_SCHEMA.mv_distribution_performance
GROUP BY region;
```

Replace `YOUR_CATALOG.YOUR_SCHEMA` with your catalog and schema. In practice, Genie will generate the right aggregation based on the metric view's definition.

**Sample query to test that the metric view is used**

- **In Genie (natural language):** Ask: **"Enrolled members by region"** or **"Show me persistency_12m_avg and commission_ytd_total by region"**. Then open the generated SQL and check that it has `FROM ...mv_distribution_performance` and columns like `enrolled_members`, `persistency_12m_avg`.
- **Direct SQL (Databricks SQL or notebook):** Run the following (replace `YOUR_CATALOG.YOUR_SCHEMA` with your catalog and schema). If it returns rows, the metric view is working. The column names confirm you're querying the metric view.

```sql
SELECT region, enrolled_members, persistency_12m_avg, complaint_count_total, commission_ytd_total
FROM YOUR_CATALOG.YOUR_SCHEMA.mv_distribution_performance
LIMIT 20;
```

**How to know if a query is using the metric view**

1. **Check the SQL Genie shows** – After you ask a question, Genie usually displays or lets you expand the generated SQL. Look at the **FROM** (or **JOIN**) clause:
   - **Using the metric view:** `FROM your_catalog.your_schema.mv_distribution_performance` (or similar).
   - **Using tables:** `FROM ...agent_performance`, `...lead_fact`, etc.

2. **Check the column names in the result** – If the SQL or result set uses the **metric view measure names** (`enrolled_members`, `persistency_12m_avg`, `complaint_count_total`, `commission_ytd_total`), the query is likely using the metric view. The base **agent_performance** table uses `enrollments_ytd`, `persistency_rate`, `complaint_count`, `commission_ytd` instead.

3. **Genie UI** – In the response, use “See SQL”, “Show query”, or the SQL tab (depending on the Genie UI) and look for `mv_distribution_performance` in the text.

---

# Part 3: Configure the Genie room

In Databricks: **SQL → Genie** → open **Genie Room Tutorial - Agent Channel Analytics** → **Configure**.

## 3.1 Instructions → Text

Paste into **Instructions → Text** (replace YOUR_CATALOG.YOUR_SCHEMA in the text if you mention it):

```
You are querying Agent Channel Analytics data for Medicare Advantage distribution. This space helps distribution leaders, compliance teams, and channel managers explore agent and broker performance, leads, enrollments, compliance events, and plan mix.

Data Sources (YOUR_CATALOG.YOUR_SCHEMA):
- agent_performance: agent_id, broker_id, region, tier, enrollments_ytd, commission_ytd, persistency_rate, complaint_count
- broker_profile: broker_id, broker_name, region, agent_count, enrollments_ytd, commission_ytd
- lead_fact: lead_id, agent_id, source, campaign_id, status, created_date, score
- enrollment_fact: enrollment_id, agent_id, product_type, enrollment_date, member_region
- fact_compliance_events: event_id, agent_id, event_type, severity, resolved_flag, event_date
- Metric view mv_distribution_performance: dimensions agent_id, region, tier, broker_id; measures enrolled_members, persistency_12m_avg, complaint_count_total, commission_ytd_total. Prefer metric view for common KPIs.

Key concepts: Persistency higher is better; complaint count lower is better; funnel = lead status (new, contacted, qualified, enrolled, lost).

Query guidelines: (1) Agent performance: use agent_performance or mv_distribution_performance; join to broker_profile on broker_id for broker rollups. (2) Leads/conversion: use lead_fact, group by source or campaign_id, conversion = status = enrolled. (3) Compliance: use fact_compliance_events. (4) Plan mix: use enrollment_fact. (5) Broker performance by region: return one row per broker with broker_id, broker_name, region, agent_count, enrollments_ytd, commission_ytd from broker_profile; do NOT aggregate by region.

Response style: clear tables/charts; rankings with top/bottom; rates as percentages; no carrier or client names.
```

## 3.2 Instructions → Joins

**Instructions → Joins → + Add** for each join below (use full table names if the UI requires them).

**Join 1:** agent_performance → broker_profile  
- **Condition:** `agent_performance.broker_id = broker_profile.broker_id`  
- **Relationship type:** Many to One  
- **Instructions:** Use when rolling up agent metrics to broker level.

**Join 2:** agent_performance → lead_fact  
- **Condition:** `agent_performance.agent_id = lead_fact.agent_id`  
- **Relationship type:** One to Many  
- **Instructions:** Use when analyzing leads, conversion, or funnel by agent.

**Join 3:** agent_performance → enrollment_fact  
- **Condition:** `agent_performance.agent_id = enrollment_fact.agent_id`  
- **Relationship type:** One to Many  
- **Instructions:** Use when analyzing enrollments or plan mix by agent.

**Join 4:** agent_performance → fact_compliance_events  
- **Condition:** `agent_performance.agent_id = fact_compliance_events.agent_id`  
- **Relationship type:** One to Many  
- **Instructions:** Use when analyzing compliance events or risk by agent.

## 3.3 Instructions → SQL Expressions

**Instructions → SQL Expressions → + Add**. Choose **Measure**, **Filter**, or **Dimension** and fill in the fields.

**Measures**

- **conversion_rate** (Tables: lead_fact)  
  Code: `ROUND(SUM(CASE WHEN lead_fact.status = 'enrolled' THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0), 2)`  
  Synonyms: success rate, conversion ratio, conversion pct, enrollment rate  
  Instructions: Percentage of leads that reached enrolled status. Use with lead_fact.

**Filters**

- **Enrolled only** – Code: `lead_fact.status = 'enrolled'` | Synonyms: enrolled, converted, completed, successful
- **Active leads** – Code: `lead_fact.status IN ('new', 'contacted', 'qualified')` | Synonyms: active, open, pending, pipeline
- **South region** – Code: `agent_performance.region = 'South'` | Synonyms: south, southern, Southeast

**Dimensions**

- **Lead source** – Code: `lead_fact.source`
- **Plan type** – Code: `enrollment_fact.product_type`
- **Broker region** – Code: `broker_profile.region`
- **Enrollment month** – Code: `DATE_TRUNC('month', enrollment_fact.enrollment_date)`

## 3.4 Instructions → SQL Queries (example queries)

Add via **+ Add** (replace YOUR_CATALOG.YOUR_SCHEMA):

**Top agents:**
```sql
SELECT agent_id, broker_id, region, enrollments_ytd, persistency_rate, complaint_count
FROM YOUR_CATALOG.YOUR_SCHEMA.agent_performance ORDER BY enrollments_ytd DESC LIMIT 10
```

**Leads by source and conversion:**
```sql
SELECT source, COUNT(*) AS leads, SUM(CASE WHEN status = 'enrolled' THEN 1 ELSE 0 END) AS enrolled,
  ROUND(SUM(CASE WHEN status = 'enrolled' THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0), 2) AS conversion_pct
FROM YOUR_CATALOG.YOUR_SCHEMA.lead_fact GROUP BY source
```

**Compliance events by agent:**
```sql
SELECT agent_id, event_type, COUNT(*) AS event_count
FROM YOUR_CATALOG.YOUR_SCHEMA.fact_compliance_events GROUP BY agent_id, event_type ORDER BY event_count DESC
```

**Broker performance by region:**
```sql
SELECT broker_id, broker_name, region, agent_count, enrollments_ytd, commission_ytd
FROM YOUR_CATALOG.YOUR_SCHEMA.broker_profile ORDER BY enrollments_ytd DESC
```

## 3.5 Parameterized queries (Trusted responses)

Add these under **Instructions → SQL Queries**. For any `LIMIT :limit_count`, set the parameter type to **Numeric/Integer**.

**Top brokers** – Parameter: limit_count (Numeric/Integer). Example to test: 10, 25.
```sql
SELECT broker_id, broker_name, region, agent_count, enrollments_ytd, commission_ytd
FROM YOUR_CATALOG.YOUR_SCHEMA.broker_profile ORDER BY enrollments_ytd DESC LIMIT :limit_count
```

**Leads by source with region** – Parameter: region_filter (String, default ALL). Example: South, Midwest, Northeast, West, ALL.
```sql
SELECT l.source, COUNT(*) AS leads, SUM(CASE WHEN l.status = 'enrolled' THEN 1 ELSE 0 END) AS enrolled,
  ROUND(SUM(CASE WHEN l.status = 'enrolled' THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0), 2) AS conversion_pct
FROM YOUR_CATALOG.YOUR_SCHEMA.lead_fact l
JOIN YOUR_CATALOG.YOUR_SCHEMA.agent_performance a ON l.agent_id = a.agent_id
WHERE (:region_filter = 'ALL' OR a.region = :region_filter) GROUP BY l.source
```

**Compliance by severity** – Parameter: severity_filter (String). Example: High, Medium, Low, Critical.
```sql
SELECT agent_id, event_type, severity, COUNT(*) AS event_count
FROM YOUR_CATALOG.YOUR_SCHEMA.fact_compliance_events WHERE severity = :severity_filter
GROUP BY agent_id, event_type, severity ORDER BY event_count DESC
```

## 3.6 UDF (optional, for Trusted agent queries)

Run in SQL Editor or a notebook (replace YOUR_CATALOG.YOUR_SCHEMA), then add in Genie: **Configure → Add trusted asset → SQL Function**.

```sql
CREATE OR REPLACE FUNCTION YOUR_CATALOG.YOUR_SCHEMA.top_agents_by_enrollments(
  limit_count INT DEFAULT 10,
  region_filter STRING DEFAULT NULL
)
RETURNS TABLE (
  agent_id STRING,
  broker_id STRING,
  region STRING,
  enrollments_ytd BIGINT,
  persistency_rate DOUBLE,
  complaint_count INT
)
COMMENT 'Returns top agents by enrollments YTD.'
RETURN
  SELECT agent_id, broker_id, region, enrollments_ytd, persistency_rate, complaint_count
  FROM (
    SELECT agent_id, broker_id, region, enrollments_ytd, persistency_rate, complaint_count,
           ROW_NUMBER() OVER (ORDER BY enrollments_ytd DESC) AS rn
    FROM YOUR_CATALOG.YOUR_SCHEMA.agent_performance
    WHERE (top_agents_by_enrollments.region_filter IS NULL OR top_agents_by_enrollments.region_filter = '' OR region = top_agents_by_enrollments.region_filter)
  ) ranked
  WHERE rn <= GREATEST(COALESCE(NULLIF(top_agents_by_enrollments.limit_count, 0), 10), 1);
```

**Simplified (fixed LIMIT 100):** Omit `limit_count`, use only `region_filter`; call with `SELECT * FROM ... LIMIT N` for fewer rows.

## 3.7 Benchmarks (Benchmarks → Questions)

**+ Add benchmark** for each item below. **Question** = natural language; **Ground truth SQL** = replace YOUR_CATALOG.YOUR_SCHEMA in the SQL. Then click **Run all benchmarks** to compare Genie's answers to the ground truth.

**Question:** Top 10 agents by enrollments and persistency  
**Ground truth SQL:**
```sql
SELECT agent_id, broker_id, region, enrollments_ytd, persistency_rate, complaint_count
FROM YOUR_CATALOG.YOUR_SCHEMA.agent_performance ORDER BY enrollments_ytd DESC LIMIT 10
```

**Question:** Leads by source and conversion rate  
**Ground truth SQL:**
```sql
SELECT source, COUNT(*) AS leads, SUM(CASE WHEN status = 'enrolled' THEN 1 ELSE 0 END) AS enrolled,
  ROUND(SUM(CASE WHEN status = 'enrolled' THEN 1 ELSE 0 END) * 100.0 / NULLIF(COUNT(*), 0), 2) AS conversion_pct
FROM YOUR_CATALOG.YOUR_SCHEMA.lead_fact GROUP BY source
```

**Question:** Compliance events by agent  
**Ground truth SQL:**
```sql
SELECT agent_id, event_type, COUNT(*) AS event_count
FROM YOUR_CATALOG.YOUR_SCHEMA.fact_compliance_events GROUP BY agent_id, event_type ORDER BY event_count DESC
```

**Question:** Broker performance by region  
**Ground truth SQL:**
```sql
SELECT broker_id, broker_name, region, agent_count, enrollments_ytd, commission_ytd
FROM YOUR_CATALOG.YOUR_SCHEMA.broker_profile ORDER BY enrollments_ytd DESC
```

## 3.8 Settings

- **Description:** e.g. "Query agent and broker performance with natural language (tutorial)."
- **Sample questions:** Add e.g. "Best performing agents", "Leads by source and conversion rate", "Broker performance by region", "Show me 10 rows from agent_performance".

---

# Part 4: Explore the room (step-by-step)

Use this section to **explore** the Genie room after setup and configuration. It walks through Chat, Agent mode, and a quick tour of Configure so you learn the room by doing.

## 4.1 Before you start

- The setup notebook has been run (schema, tables, data, Genie space exist).
- You have the SQL Warehouse ID set in the notebook and the warehouse is available.
- In Databricks: **SQL → Genie** → open **Genie Room Tutorial - Agent Channel Analytics**.

## 4.2 Start the SQL warehouse

1. If you see a banner like **"The SQL Warehouse … is stopped"**, click **► Start Warehouse**.
2. Wait until the warehouse shows as running (green).
3. You can now ask questions in the Genie room.

## 4.3 Chat mode – basic questions

Stay in **Chat** mode and try these in order. Genie will turn them into SQL and return tables (and sometimes charts).

**2a – Top agents**

1. Type or click: **"Best performing agents"** or **"Top 10 agents by enrollments and persistency"**.
2. Submit.
3. You should see a table of agents with enrollments, persistency, complaints.
4. If you see a **Trusted** badge, Genie used a predefined query or UDF you added.

**2b – Leads and conversion**

1. Ask: **"Leads by source and conversion rate"**.
2. You should see source, lead count, enrolled count, and conversion %.
3. Conversion = (enrolled / total leads) × 100.

**2c – Compliance**

1. Ask: **"Compliance events by agent"**.
2. You should see agents and counts of compliance events by type.

**2d – Brokers**

1. Ask: **"Broker performance by region"**.
2. You should see one row per broker with region, agent count, enrollments, commission.

**Fallback:** If a question fails or returns empty, try **"Show me 10 rows from agent_performance"** to confirm the room can query the tables.

### Questions that trigger the Trusted icon

After you add the **parameterized queries** and **UDF** (Part 3.5 and 3.6), these questions typically produce a **Trusted** badge when Genie uses the matching asset:

- **Top 10 agents by enrollments** → Parameterized "Top agents" or UDF `top_agents_by_enrollments`
- **Top 25 agents by enrollments** → Parameterized "Top agents" (limit_count = 25)
- **Best performing agents** → UDF or parameterized "Top agents"
- **Top agents in South** → UDF with region_filter = South
- **Top 10 brokers by enrollments** → Parameterized "Top brokers" (limit_count = 10)
- **Top 25 brokers** → Parameterized "Top brokers" (limit_count = 25)
- **Leads by source and conversion in South** → Parameterized "Leads by source with region" (region_filter = South)
- **Conversion rate by lead source in Midwest** → Parameterized "Leads by source with region" (region_filter = Midwest)
- **High severity compliance events by agent** → Parameterized "Compliance by severity" (severity_filter = High)
- **Compliance issues with medium severity** → Parameterized "Compliance by severity" (severity_filter = Medium)

If you don't see the Trusted badge, confirm the query is added under **Instructions → SQL Queries** (or the UDF under **Add trusted asset**) and that the question phrasing is close to the examples above.

### How to see if the metric view is used for a particular query

1. **Ask a question that can use the metric view** – In Chat, try: **"Enrolled members by region"** or **"Show me persistency_12m_avg and commission_ytd_total by region"**.
2. **Open the SQL Genie generated** – In the response, use the control that shows the underlying query (e.g. "See SQL", "Show query", or an SQL tab).
3. **Check whether the metric view is used:**
   - **Yes:** The SQL has `FROM your_catalog.your_schema.mv_distribution_performance` (or similar) and result columns like `enrolled_members`, `persistency_12m_avg`, `complaint_count_total`, `commission_ytd_total`.
   - **No:** The SQL uses `FROM ...agent_performance` (or other tables) and columns like `enrollments_ytd`, `persistency_rate`, `complaint_count`, `commission_ytd`.

**Optional – run the metric view directly:** In Databricks SQL or a notebook, run (replace with your catalog and schema):

```sql
SELECT region, enrolled_members, persistency_12m_avg, complaint_count_total, commission_ytd_total
FROM YOUR_CATALOG.YOUR_SCHEMA.mv_distribution_performance
LIMIT 20;
```

If this returns rows, the metric view is working. See **Part 2.3** for more on metric views and how they're used in this room.

## 4.4 Agent mode – analysis and visuals

Switch to **Agent** mode for multi-step analysis.

**Outliers**

1. In **Agent** mode, ask: **"Identify interesting outlier entities in the dataset (and potential causes)"**.
2. The agent will analyze the data and point out outliers (e.g. very high/low commission or complaints) and possible reasons.

**Visualizations**

1. Ask: **"Visualize the interesting aspects of the dataset"**.
2. The agent may suggest and generate charts (e.g. by region, tier, or lead source).

## 4.5 Configure tour – how the room is built

Click **Configure** (gear icon) to see how the room is set up. This is the same content you added in Part 3; here you're touring it.

- **Data:** Open the **Data** tab. You should see the five tables (and metric view if linked). These are the only data sources this Genie room can use.
- **Instructions → Text:** Domain text—what the data is, key concepts, and query guidelines (Part 3.1).
- **Instructions → Joins:** How tables relate (Part 3.2). Joins tell Genie how to write correct JOINs.
- **Instructions → SQL Queries:** Example and parameterized queries (Part 3.4, 3.5). Parameterized ones can be marked Trusted.
- **Settings:** Description and **Sample questions**. Add or keep questions like "Best performing agents", "Leads by source and conversion rate", "Broker performance by region".

## 4.6 Run benchmarks (optional)

1. Click **Benchmarks** in the Genie room.
2. Open the **Questions** tab.
3. If you haven't already, add benchmarks from Part 3.7 (question + ground truth SQL).
4. Click **Run all benchmarks** to see how often Genie's answers match the expected SQL/results.

---

# Part 5: Quick reference

## Quick reference – questions to try

| Question | Mode | What you get | Trusted? |
|----------|------|--------------|----------|
| Best performing agents | Chat | Top agents by performance | Yes (if UDF/parameterized query added) |
| Top 10 agents by enrollments and persistency | Chat | Same idea, explicit top 10 | Yes |
| Top 10 brokers by enrollments | Chat | Top brokers, limit 10 | Yes |
| Leads by source and conversion in South | Chat | Conversion by source, South only | Yes |
| High severity compliance events by agent | Chat | Compliance counts, High severity | Yes |
| Show me 10 rows from agent_performance | Chat | Simple table check | No |
| Leads by source and conversion rate | Chat | Funnel/conversion by source | Maybe |
| Compliance events by agent | Chat | Compliance counts by agent | Maybe |
| Broker performance by region | Chat | One row per broker | No |
| Identify interesting outlier entities... | Agent | Outlier analysis and causes | No |
| Visualize the interesting aspects... | Agent | Charts and summaries | No |

## Questions that often trigger Trusted (after adding assets)

| Question | Asset |
|----------|--------|
| Top 10 agents by enrollments | Parameterized Top agents or UDF |
| Top 25 agents by enrollments | Parameterized Top agents (limit_count = 25) |
| Best performing agents | UDF or parameterized Top agents |
| Top agents in South | UDF with region_filter = South |
| Top 10 brokers by enrollments | Parameterized Top brokers (limit_count = 10) |
| Leads by source and conversion in South | Parameterized Leads by source with region (region_filter = South) |
| High severity compliance events by agent | Parameterized Compliance by severity (severity_filter = High) |

## Sample questions to add in Settings

Best performing agents • Show me 10 rows from agent_performance • Top 10 agents by enrollments • Leads by source and conversion rate • Compliance events by agent • Broker performance by region

## Region and severity values (for parameters)

- **Regions:** South, Midwest, Northeast, West (or ALL for no filter).
- **Severities:** High, Medium, Low, Critical.

## Next steps

- Use **Part 2 (Data at a glance)** when writing or debugging SQL and instructions.
