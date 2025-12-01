"""
Supabase database client for Seek jobs
"""

import os
from supabase import create_client, Client

# Try Streamlit secrets first (for cloud), fall back to env vars (for local)
try:
    import streamlit as st
    SUPABASE_URL = st.secrets.get("SUPABASE_URL")
    SUPABASE_KEY = st.secrets.get("SUPABASE_KEY")
except:
    SUPABASE_URL = None
    SUPABASE_KEY = None

if not SUPABASE_URL or not SUPABASE_KEY:
    from dotenv import load_dotenv
    load_dotenv()
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")


def get_client() -> Client:
    """Get Supabase client instance"""
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in secrets or .env")

    return create_client(SUPABASE_URL, SUPABASE_KEY)


def get_jobs(
    search: str = None,
    region: str = None,
    job_type: str = None,
    triage_status: str = None,
    sort_by: str = "first_seen",
    limit: int = 50,
    offset: int = 0
) -> tuple[list, int]:
    """
    Fetch jobs with optional filters.
    Returns (jobs_list, total_count)
    """
    client = get_client()

    query = client.table("jobs").select("*", count="exact")

    if search:
        query = query.or_(
            f"title.ilike.%{search}%,"
            f"company.ilike.%{search}%,"
            f"description.ilike.%{search}%"
        )

    if region:
        query = query.eq("region", region)

    if job_type:
        query = query.ilike("job_type", f"%{job_type}%")

    if triage_status == "unreviewed":
        query = query.is_("triage_status", "null")
    elif triage_status in ["yes", "no"]:
        query = query.eq("triage_status", triage_status)

    # Sort options
    if sort_by == "date_listed":
        query = query.order("date_listed", desc=True)
    else:
        query = query.order("first_seen", desc=True)

    query = query.range(offset, offset + limit - 1)

    result = query.execute()

    return result.data, result.count


def update_triage(job_id: int, status: str) -> bool:
    """Update triage status for a job"""
    client = get_client()

    result = client.table("jobs").update(
        {"triage_status": status}
    ).eq("id", job_id).execute()

    return len(result.data) > 0


def get_regions() -> list[str]:
    """Get distinct regions for filter dropdown"""
    client = get_client()

    result = client.table("jobs").select("region").neq("region", "").execute()

    # Normalize: strip whitespace and deduplicate
    regions = sorted(set(row["region"].strip() for row in result.data if row["region"] and row["region"].strip()))
    return regions


def get_job_types() -> list[str]:
    """Get distinct job types for filter dropdown"""
    client = get_client()

    result = client.table("jobs").select("job_type").neq("job_type", "").execute()

    job_types = sorted(set(row["job_type"] for row in result.data if row["job_type"]))
    return job_types


def get_cv() -> str:
    """Get stored CV text"""
    client = get_client()

    result = client.table("cv_profile").select("cv_text").limit(1).execute()

    if result.data:
        return result.data[0]["cv_text"]
    return ""


def save_cv(cv_text: str) -> bool:
    """Save or update CV text"""
    client = get_client()

    existing = client.table("cv_profile").select("id").limit(1).execute()

    if existing.data:
        result = client.table("cv_profile").update(
            {"cv_text": cv_text}
        ).eq("id", existing.data[0]["id"]).execute()
    else:
        result = client.table("cv_profile").insert(
            {"cv_text": cv_text}
        ).execute()

    return len(result.data) > 0


def get_stats() -> dict:
    """Get database statistics"""
    client = get_client()

    total = client.table("jobs").select("id", count="exact").execute()
    reviewed_yes = client.table("jobs").select("id", count="exact").eq("triage_status", "yes").execute()
    reviewed_no = client.table("jobs").select("id", count="exact").eq("triage_status", "no").execute()
    unreviewed = client.table("jobs").select("id", count="exact").is_("triage_status", "null").execute()

    return {
        "total": total.count,
        "yes": reviewed_yes.count,
        "no": reviewed_no.count,
        "unreviewed": unreviewed.count
    }
