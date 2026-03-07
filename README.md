# Agent Channel Genie Tutorial

A **deploy-only** Genie Room setup (Agent Channel Analytics). Use the Databricks Asset Bundle to **deploy to staging**; the job is **not run** by the bundle. Run the notebook manually in the workspace, then complete the room using the included guide.

**GitHub:** [bigdatavik/agent_channel_genie_tutorial](https://github.com/bigdatavik/agent_channel_genie_tutorial) (private)

---

## Deploy to staging (do not run the job)

This repo uses **Databricks Asset Bundles (DABs)** to deploy the Genie setup job to staging only. Deployment **does not run** the job.

1. **Prerequisites:** [Databricks CLI](https://docs.databricks.com/dev-tools/cli/index.html) installed and authenticated for the staging workspace:
   ```bash
   databricks auth login --profile fevm
   ```
2. **Deploy to staging:**
   ```bash
   cd /path/to/agent_channel_genie_tutorial
   databricks bundle deploy --target staging --profile fevm
   ```
   This uploads the notebook and creates the job **genie_room_setup_staging** in the workspace. The job is **not** run.
3. **Run the job manually** in Databricks: go to Workflows → Jobs → **genie_room_setup_staging** → Run now. Or run the notebook **One_Notebook_Genie_Room_Setup.py** from the workspace.
4. **Complete the Genie room** using **[GENIE_ROOM_COMPLETE_GUIDE.md](GENIE_ROOM_COMPLETE_GUIDE.md)** (Joins, Instructions, SQL Expressions, Queries, Trusted assets, Benchmarks, explore).

---

## What’s in this repo

| File | Purpose |
|------|--------|
| **One_Notebook_Genie_Room_Setup.py** | Single notebook: creates schema (if needed), tables, synthetic data, metric view, and Genie space. Edit `CATALOG`, `SCHEMA`, and `WAREHOUSE_ID` in the top cells before running. |
| **GENIE_ROOM_COMPLETE_GUIDE.md** | Complete guide: setup, data reference, and how to configure the Genie room (Instructions, Joins, SQL Expressions, Queries, Trusted assets, Benchmarks) and explore it. Use after running the notebook. |
| **databricks.yml** | Bundle definition: staging target and one job (genie_room_setup). Deploy with `databricks bundle deploy --target staging`. |

---

## Quick start

1. Clone: `git clone https://github.com/bigdatavik/agent_channel_genie_tutorial.git`
2. Deploy: `databricks bundle deploy --target staging --profile fevm` (job is **not** run).
3. In Databricks, run the job **genie_room_setup_staging** (or the notebook) once.
4. Follow **[GENIE_ROOM_COMPLETE_GUIDE.md](GENIE_ROOM_COMPLETE_GUIDE.md)** to finish configuring and exploring the room.

Replace `YOUR_CATALOG` and `YOUR_SCHEMA` in the guide with the catalog and schema you set in the notebook.

---

## Requirements

- Databricks workspace with Genie and Unity Catalog (staging: fevm profile)
- SQL warehouse for the Genie space
- Catalog must exist; schema is created by the notebook if it does not exist
