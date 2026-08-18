"""Generate lakehouse summary for submission screenshots."""
import os
from pathlib import Path

BASE = Path("_lakehouse")
out_lines = []

def section(title):
    out_lines.append(f"\n{'='*60}")
    out_lines.append(f"  {title}")
    out_lines.append("="*60)

def tree(path, prefix="", max_show=5):
    p = Path(path)
    if not p.exists():
        out_lines.append(f"{prefix}(empty)")
        return
    items = sorted(p.iterdir())
    shown = items[:max_show]
    for i, item in enumerate(shown):
        connector = "└── " if i == len(shown) - 1 else "├── "
        out_lines.append(f"{prefix}{connector}{item.name}")
        if item.is_dir() and item.name not in ("data", "metadata", "warehouse"):
            deeper = sorted(item.iterdir())
            sub = deeper[:3]
            for j, sub_item in enumerate(sub):
                c2 = "    " if i == len(shown) - 1 else "│   "
                c3 = "└── " if j == len(sub) - 1 else "├── "
                out_lines.append(f"{prefix}{c2}{c3}{sub_item.name}")
    if len(items) > max_show:
        out_lines.append(f"{prefix}... ({len(items) - max_show} more)")


section("NB1: _delta_log JSON commits (Delta transaction log)")
tree(BASE / "scratch" / "users_delta" / "_delta_log")
log_files = list((BASE / "scratch" / "users_delta" / "_delta_log").glob("*.json"))
out_lines.append(f"\nTotal commits: {len(log_files)}")
if log_files:
    with open(log_files[0]) as f:
        line = f.readline()[:120]
    out_lines.append(f"First entry: {line}")

section("NB2: OPTIMIZE / Z-ORDER")
opt_dir = BASE / "scratch" / "events_smallfiles"
tree(opt_dir / "_delta_log")
parquet_files = list(opt_dir.glob("*.parquet")) if opt_dir.exists() else []
out_lines.append(f"Parquet files after OPTIMIZE: {len(parquet_files)}")

section("NB3: Time Travel")
tt_dir = BASE / "scratch" / "customers_tt" / "_delta_log"
tree(tt_dir)
tt_logs = list(tt_dir.glob("*.json")) if tt_dir.exists() else []
out_lines.append(f"Versions in history: {len(tt_logs)}")

section("NB4: Medallion Architecture — Bronze / Silver / Gold")
out_lines.append("\nBronze (raw):")
tree(BASE / "bronze")
out_lines.append("\nSilver (cleaned):")
tree(BASE / "silver")
out_lines.append("\nGold (aggregated):")
tree(BASE / "gold")

section("NB5: Iceberg Catalog (three-tier metadata)")
nb5_data = BASE / "iceberg" / "nb5" / "warehouse" / "lake" / "llm_events" / "data"
tree(nb5_data, max_show=6)
meta = BASE / "iceberg" / "nb5" / "warehouse" / "lake" / "llm_events" / "metadata"
if meta.exists():
    out_lines.append("\nMetadata files:")
    tree(meta, max_show=8)
    meta_files = list(meta.glob("*"))
    out_lines.append(f"Total metadata files: {len(meta_files)}")

section("NB6: Maintenance Jobs")
nb6_wh = BASE / "iceberg" / "nb6" / "warehouse" / "lake"
maint_data = nb6_wh / "maint" / "data"
tree(maint_data)

section("NB7: Vectors / Multimodal")
blobs = BASE / "blobs"
blob_count = len(list(blobs.glob("*.bin"))) if blobs.exists() else 0
out_lines.append(f"Blob files: {blob_count}")

# NB7 tables: emb_f32, emb_int8, media_inline, media_pointer, docs_intable
for table in ["emb_f32", "emb_int8", "media_inline", "media_pointer", "docs_intable"]:
    t_path = BASE / "scratch" / table
    if t_path.exists():
        tree(t_path / "_delta_log")
        pf = list(t_path.glob("*.parquet"))
        out_lines.append(f"  {table}: {len(pf)} parquet files")

tree(BASE / "silver" / "training_corpus_governed")

section("NB8: Agents / Provenance")
tree(BASE / "silver" / "agent_trajectories")

section("Summary")
all_delta = list(BASE.rglob("_delta_log/*.json"))
out_lines.append(f"Total Delta commits across all tables: {len(all_delta)}")
all_parquet = list(BASE.rglob("*.parquet"))
out_lines.append(f"Total Parquet data files: {len(all_parquet)}")
all_iceberg_meta = list((BASE / "iceberg").rglob("*.json"))
out_lines.append(f"Total Iceberg metadata files: {len(all_iceberg_meta)}")
total_bytes = sum(
    f.stat().st_size for f in BASE.rglob("*") if f.is_file()
)
out_lines.append(f"Total lakehouse size: {total_bytes / 1024 / 1024:.1f} MB")

report = "\n".join(out_lines)
print(report)

# Save to submission
os.makedirs("submission/screenshots", exist_ok=True)
with open("submission/screenshots/lakehouse_summary.txt", "w") as f:
    f.write(report)
print("\n\nSaved to submission/screenshots/lakehouse_summary.txt")
