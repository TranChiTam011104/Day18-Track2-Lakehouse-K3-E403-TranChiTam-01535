# Reflection — Top 5 Lakehouse Anti-Patterns

## Which anti-pattern is our team's data most at risk of?

**Anti-Pattern #2: "The Unconstrained Catalog" — letting the lakehouse grow without catalog governance.**

Our team ingests LLM chat logs and agent trajectories from multiple upstream pipelines. Every new use case creates a new table path, often with slightly different schemas for the same entity (e.g., `user_id` vs `userId` vs `uid`). Without a centralized catalog with enforced schema contracts, we accumulate `gold` tables that diverge silently — a new column here, a renamed field there — until downstream ML training jobs silently misalign features.

**Why we are vulnerable:** We move fast and iterate on prompts. The temptation is to append new columns to existing tables without schema evolution policies, because "it works right now." Over time, this creates a gold layer where identical-looking columns have different null rates or value distributions across tables, breaking model reproducibility.

**Mitigation we will adopt:** Treat the catalog as the schema registry. All table changes must go through schema evolution (Delta `merge` mode or Iceberg `update-schema`). Every table gets a partition spec at creation time and a retention SLA in the catalog metadata. The maintenance jobs in NB6 (compaction, clustering, expiry, orphan cleanup) run on a schedule — not as one-offs.
