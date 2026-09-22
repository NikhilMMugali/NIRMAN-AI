"""
Seed Supabase database from canonical PAIMANA parquet dataset.
"""

from __future__ import annotations

import argparse
import logging
import math
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd
from app.repositories.supabase_repo import SupabaseRepository

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("seed_supabase")

ROOT_DIR = Path(__file__).resolve().parents[3]
CANONICAL_PARQUET_PATH = ROOT_DIR / "data" / "curated" / "paimana" / "project_monthly_status.parquet"


def clean_val(val: Any) -> Any:
    """Convert NaNs, pandas NaT, empty strings (where appropriate), and infinities to None."""
    if val is None:
        return None
    if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
        return None
    if pd.isna(val):
        return None
    return val


def format_reporting_month(row: pd.Series) -> str:
    """Format reporting month as YYYY-MM string."""
    if "reporting_period" in row and pd.notna(row["reporting_period"]) and str(row["reporting_period"]).strip():
        return str(row["reporting_period"]).strip()
    
    year = int(row.get("reporting_year", 2025))
    month = int(row["reporting_month"])
    return f"{year:04d}-{month:02d}"


def validate_and_normalize(df: pd.DataFrame) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
    """
    Validate, clean, and map parquet records into Supabase projects & project_monthly_status dicts.
    Returns (projects_records, status_records, audit_summary).
    """
    logger.info("Auditing canonical dataset: %s", CANONICAL_PARQUET_PATH)
    total_raw_rows = len(df)
    
    # 1. Clean strings & project IDs
    df["project_id"] = df["project_id"].astype(str).str.strip()
    df["project_name"] = df["project_name"].astype(str).str.strip()
    
    unique_projects_count = df["project_id"].nunique()
    
    # 2. Check for duplicate logical keys (project_id, reporting_month)
    df["normalized_reporting_month"] = df.apply(format_reporting_month, axis=1)
    dup_rows = df[df.duplicated(subset=["project_id", "normalized_reporting_month"], keep=False)]
    dup_count = len(dup_rows)
    
    if dup_count > 0:
        logger.error("Found %d unexpected duplicate (project_id, reporting_month) rows!", dup_count)
        raise ValueError(f"Aborting seed: found {dup_count} duplicate project-month records.")
        
    reporting_period_min = df["normalized_reporting_month"].min()
    reporting_period_max = df["normalized_reporting_month"].max()
    
    # 3. Prepare unique `projects` table records
    proj_grouped = df.groupby("project_id", as_index=False).first()
    projects_list: List[Dict[str, Any]] = []
    
    for _, row in proj_grouped.iterrows():
        p_id = row["project_id"]
        p_name = row["project_name"]
        sector = clean_val(row.get("sector"))
        if sector == "":
            sector = None
        state = clean_val(row.get("state"))
        if state == "":
            state = None
            
        projects_list.append({
            "project_id": p_id,
            "project_name": p_name,
            "ministry": None,
            "department": None,
            "sector": sector,
            "sub_sector": None,
            "state": state,
            "district": None,
            "implementing_agency": None,
            "location": None,
            "project_type": None,
        })
        
    # 4. Prepare `project_monthly_status` table records
    monthly_list: List[Dict[str, Any]] = []
    
    for _, row in df.iterrows():
        phys_prog = clean_val(row.get("physical_progress"))
        if phys_prog is not None:
            phys_prog = float(phys_prog)
            
        orig_cost = clean_val(row.get("original_cost"))
        if orig_cost is not None:
            orig_cost = float(orig_cost)
            
        rev_cost = clean_val(row.get("revised_cost"))
        if rev_cost is not None:
            rev_cost = float(rev_cost)
            
        exp = clean_val(row.get("expenditure"))
        if exp is not None:
            exp = float(exp)
            
        page_no = clean_val(row.get("source_page"))
        if page_no is not None:
            page_no = int(page_no)

        monthly_list.append({
            "logical_project_id": row["project_id"],
            "reporting_month": row["normalized_reporting_month"],
            "original_cost": orig_cost,
            "revised_cost": rev_cost,
            "expenditure": exp,
            "physical_progress": phys_prog,
            "financial_progress": None,
            "original_start_date": None,
            "original_completion_date": None,
            "revised_completion_date": None,
            "reported_status": None,
            "data_source_id": None,
            "source_page": page_no,
            "extraction_confidence": None,
        })
        
    summary = {
        "raw_rows": total_raw_rows,
        "unique_projects": unique_projects_count,
        "duplicate_count": dup_count,
        "reporting_period_min": reporting_period_min,
        "reporting_period_max": reporting_period_max,
    }
    
    return projects_list, monthly_list, summary


def seed_data(
    repo: SupabaseRepository,
    projects: List[Dict[str, Any]],
    monthly_records: List[Dict[str, Any]],
    project_batch_size: int = 200,
    monthly_batch_size: int = 500,
) -> Dict[str, Any]:
    """Upsert projects and monthly records in batches into Supabase."""
    client = repo.client
    if client is None:
        raise RuntimeError("Supabase client is not configured or failed to initialize.")
        
    total_projects = len(projects)
    logger.info("Starting upsert for %d projects (batch size=%d)...", total_projects, project_batch_size)
    
    upserted_projects_count = 0
    for i in range(0, total_projects, project_batch_size):
        batch = projects[i : i + project_batch_size]
        res = client.table("projects").upsert(batch, on_conflict="project_id").execute()
        if not res.data:
            raise RuntimeError(f"Failed to upsert projects batch starting at index {i}")
        upserted_projects_count += len(res.data)
        logger.info("Projects progress: %d / %d", min(i + len(batch), total_projects), total_projects)
        
    logger.info("Successfully upserted %d project records into Supabase.", upserted_projects_count)
    
    # Resolve project_id (TEXT) -> id (UUID) mapping from Supabase
    logger.info("Fetching resolved Supabase project UUIDs...")
    all_projects_rows = []
    # Fetch in chunks to avoid select size caps
    start_idx = 0
    page_size = 1000
    while True:
        res = client.table("projects").select("id, project_id").range(start_idx, start_idx + page_size - 1).execute()
        rows = res.data or []
        all_projects_rows.extend(rows)
        if len(rows) < page_size:
            break
        start_idx += page_size
        
    uuid_map = {row["project_id"]: row["id"] for row in all_projects_rows}
    logger.info("Resolved %d project UUID mappings.", len(uuid_map))
    
    # Map logical_project_id to resolved Supabase UUID project_id
    prepared_monthly: List[Dict[str, Any]] = []
    missing_uuids = 0
    for m in monthly_records:
        m_copy = dict(m)
        logical_id = m_copy.pop("logical_project_id")
        uuid_val = uuid_map.get(logical_id)
        if not uuid_val:
            missing_uuids += 1
            continue
        m_copy["project_id"] = uuid_val
        prepared_monthly.append(m_copy)
        
    if missing_uuids > 0:
        raise RuntimeError(f"Could not resolve Supabase project UUID for {missing_uuids} monthly records!")
        
    total_monthly = len(prepared_monthly)
    logger.info("Starting upsert for %d monthly records (batch size=%d)...", total_monthly, monthly_batch_size)
    
    upserted_monthly_count = 0
    for i in range(0, total_monthly, monthly_batch_size):
        batch = prepared_monthly[i : i + monthly_batch_size]
        res = client.table("project_monthly_status").upsert(batch, on_conflict="project_id,reporting_month").execute()
        if not res.data:
            raise RuntimeError(f"Failed to upsert project_monthly_status batch starting at index {i}")
        upserted_monthly_count += len(res.data)
        logger.info("Monthly records progress: %d / %d", min(i + len(batch), total_monthly), total_monthly)
        
    logger.info("Successfully upserted %d monthly records into Supabase.", upserted_monthly_count)
    
    return {
        "projects_upserted": upserted_projects_count,
        "monthly_records_upserted": upserted_monthly_count,
    }


def verify_migration(repo: SupabaseRepository, summary: Dict[str, Any]) -> Dict[str, Any]:
    """Query Supabase to verify counts and sample records against local canonical summary."""
    client = repo.client
    if client is None:
        raise RuntimeError("Supabase client unavailable for verification.")
        
    # Count projects
    res_proj = client.table("projects").select("id", count="exact").execute()
    sb_proj_count = res_proj.count if res_proj.count is not None else len(res_proj.data)
    
    # Count monthly records
    res_monthly = client.table("project_monthly_status").select("id", count="exact").execute()
    sb_monthly_count = res_monthly.count if res_monthly.count is not None else len(res_monthly.data)
    
    # Sample verification
    sample_ids = ["N04000077", "N04000073", "N24000948"]
    sample_verification = {}
    for sid in sample_ids:
        p_res = client.table("projects").select("*").eq("project_id", sid).execute()
        p_data = p_res.data or []
        if not p_data:
            sample_verification[sid] = {"exists": False}
            continue
        proj_row = p_data[0]
        p_uuid = proj_row["id"]
        
        m_res = client.table("project_monthly_status").select("*").eq("project_id", p_uuid).order("reporting_month").execute()
        m_data = m_res.data or []
        months = [r["reporting_month"] for r in m_data]
        latest_month = months[-1] if months else None
        
        sample_verification[sid] = {
            "exists": True,
            "project_id": proj_row["project_id"],
            "project_name": proj_row["project_name"],
            "monthly_records_count": len(m_data),
            "months": months,
            "latest_reporting_month": latest_month,
        }
        
    return {
        "supabase_projects_count": sb_proj_count,
        "supabase_monthly_count": sb_monthly_count,
        "sample_verification": sample_verification,
    }


def main():
    parser = argparse.ArgumentParser(description="Seed Supabase from canonical PAIMANA parquet dataset.")
    parser.add_argument("--verify-only", action="store_true", help="Only verify existing Supabase data against parquet.")
    args = parser.parse_args()
    
    repo = SupabaseRepository()
    if not repo.is_configured:
        logger.error("Supabase credentials not configured in backend/.env!")
        sys.exit(1)
        
    df = pd.read_parquet(CANONICAL_PARQUET_PATH)
    projects_list, monthly_list, summary = validate_and_normalize(df)
    
    print("\n==================================================")
    print("CANONICAL DATASET AUDIT SUMMARY")
    print("==================================================")
    print(f"Local Raw Project-Month Rows: {summary['raw_rows']}")
    print(f"Local Unique Projects:       {summary['unique_projects']}")
    print(f"Duplicates (project, month): {summary['duplicate_count']}")
    print(f"Reporting Period:            {summary['reporting_period_min']} -> {summary['reporting_period_max']}")
    print("==================================================\n")
    
    if not args.verify_only:
        logger.info("Executing migration to Supabase...")
        seed_data(repo, projects_list, monthly_list)
        
    logger.info("Verifying migration against Supabase...")
    verif = verify_migration(repo, summary)
    
    print("\n==================================================")
    print("MIGRATION & VERIFICATION REPORT")
    print("==================================================")
    print(f"DATASET LOCAL PROJECT COUNT:       {summary['unique_projects']}")
    print(f"DATASET LOCAL PROJECT-MONTH COUNT: {summary['raw_rows']}")
    print(f"SUPABASE PROJECT COUNT:            {verif['supabase_projects_count']}")
    print(f"SUPABASE PROJECT-MONTH COUNT:      {verif['supabase_monthly_count']}")
    print(f"DUPLICATES:                        {summary['duplicate_count']}")
    print(f"REPORTING PERIOD:                  {summary['reporting_period_min']} -> {summary['reporting_period_max']}")
    
    proj_match = (verif["supabase_projects_count"] == summary["unique_projects"])
    month_match = (verif["supabase_monthly_count"] == summary["raw_rows"])
    migration_pass = proj_match and month_match
    
    print(f"MIGRATION:                         {'PASS' if migration_pass else 'FAIL'}")
    
    # Test Idempotency if migration passed
    if not args.verify_only:
        logger.info("Testing idempotency by re-running migration...")
        seed_data(repo, projects_list, monthly_list)
        verif_idem = verify_migration(repo, summary)
        idem_proj_match = (verif_idem["supabase_projects_count"] == summary["unique_projects"])
        idem_month_match = (verif_idem["supabase_monthly_count"] == summary["raw_rows"])
        idem_pass = idem_proj_match and idem_month_match
        print(f"IDEMPOTENCY:                       {'PASS' if idem_pass else 'FAIL'}")
    else:
        print("IDEMPOTENCY:                       N/A (verify-only)")
        
    print("\nSAMPLE PROJECT VERIFICATION:")
    for sid, sinfo in verif["sample_verification"].items():
        print(f"  {sid}:")
        if sinfo.get("exists"):
            print(f"    - Name: {sinfo['project_name']}")
            print(f"    - Monthly Count: {sinfo['monthly_records_count']}")
            print(f"    - Months: {sinfo['months']}")
            print(f"    - Latest Month: {sinfo['latest_reporting_month']}")
        else:
            print("    - NOT FOUND IN SUPABASE")
    print("==================================================\n")


if __name__ == "__main__":
    main()
