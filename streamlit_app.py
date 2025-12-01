"""
Seek Jobs Search - Streamlit App
Mobile-friendly job search with AI ranking
"""

import streamlit as st
import os
import html
from dotenv import load_dotenv
from openai import OpenAI
import supabase_client as db

load_dotenv()

st.set_page_config(
    page_title="Seek Jobs",
    page_icon="briefcase",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Mobile-friendly CSS
st.markdown("""
<style>
    .stButton > button {
        width: 100%;
        margin: 2px 0;
    }
    .job-card {
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 12px;
        margin: 8px 0;
        background: #fafafa;
    }
    .job-title {
        font-size: 1.1em;
        font-weight: bold;
        color: #1a1a2e;
    }
    .job-company {
        color: #4a4a4a;
        font-weight: 500;
    }
    .job-meta {
        color: #666;
        font-size: 0.9em;
    }
    .score-high { color: #28a745; font-weight: bold; }
    .score-med { color: #ffc107; font-weight: bold; }
    .score-low { color: #dc3545; font-weight: bold; }
    .main .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)


def rank_jobs_with_gpt(jobs: list, cv_text: str) -> list:
    """Use GPT to rank jobs by CV match. Returns jobs with ai_score and ai_reason."""

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        st.error("OPENAI_API_KEY not set")
        return jobs

    client = OpenAI(api_key=api_key)

    job_summaries = []
    for i, job in enumerate(jobs[:20]):  # Limit to 20 for cost control
        job_summaries.append(
            f"[{i}] {job.get('title', 'No title')} at {job.get('company', 'Unknown')} - "
            f"{job.get('location', '')} - {job.get('description', '')[:200]}"
        )

    jobs_text = "\n".join(job_summaries)

    prompt = f"""You are a job matching assistant. Given a CV and a list of jobs, rate each job's relevance.

CV:
{cv_text[:3000]}

Jobs:
{jobs_text}

For each job, provide a score 1-10 (10 = perfect match) and a brief reason (10 words max).
Format your response as:
[index]: score | reason
[index]: score | reason
...

Only include jobs from the list. Be concise."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.3
        )

        result_text = response.choices[0].message.content

        scores = {}
        for line in result_text.strip().split("\n"):
            if "]:" in line:
                try:
                    idx_part, rest = line.split("]:", 1)
                    idx = int(idx_part.replace("[", "").strip())
                    parts = rest.split("|", 1)
                    score = int(parts[0].strip())
                    reason = parts[1].strip() if len(parts) > 1 else ""
                    scores[idx] = {"score": score, "reason": reason}
                except (ValueError, IndexError):
                    continue

        for i, job in enumerate(jobs[:20]):
            if i in scores:
                job["ai_score"] = scores[i]["score"]
                job["ai_reason"] = scores[i]["reason"]
            else:
                job["ai_score"] = 0
                job["ai_reason"] = "Not scored"

        for job in jobs[20:]:
            job["ai_score"] = 0
            job["ai_reason"] = "Not scored (limit)"

        jobs.sort(key=lambda x: x.get("ai_score", 0), reverse=True)

    except Exception as e:
        st.error(f"GPT error: {e}")

    return jobs


def render_job_card(job: dict, show_score: bool = False):
    """Render a single job card with triage buttons"""

    job_id = job.get("id")
    title = job.get("title", "No title") or "No title"
    company = job.get("company", "Unknown company") or "Unknown company"
    location = job.get("location", "") or ""
    region = job.get("region", "") or ""
    salary = job.get("salary", "") or ""
    job_type = job.get("job_type", "") or ""
    description = (job.get("description", "") or "")[:300]
    url = job.get("url", "")
    triage = job.get("triage_status", "")

    # Show location with region in brackets if different
    location_display = location
    if region and region != location and region not in location:
        location_display = f"{location} ({region})"

    # Build title with badge
    title_display = f"**{title}**"
    if triage == "yes":
        title_display += " :green[[YES]]"
    elif triage == "no":
        title_display += " :red[[NO]]"

    # AI score line
    score_line = ""
    if show_score and "ai_score" in job:
        score = job["ai_score"]
        reason = job.get("ai_reason", "")
        if score >= 7:
            score_line = f":green[**[{score}/10]**] {reason}"
        elif score >= 4:
            score_line = f":orange[**[{score}/10]**] {reason}"
        else:
            score_line = f":red[**[{score}/10]**] {reason}"

    # Render using native Streamlit
    st.markdown(title_display)
    st.caption(f"{company} | {location_display} | {job_type} | {salary}")
    if score_line:
        st.markdown(score_line)
    st.text(description + "..." if description else "No description")

    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        if st.button("Yes", key=f"yes_{job_id}", type="primary"):
            db.update_triage(job_id, "yes")
            st.rerun()

    with col2:
        if st.button("No", key=f"no_{job_id}"):
            db.update_triage(job_id, "no")
            st.rerun()

    with col3:
        if url:
            st.markdown(f"[Open Job]({url})")


def main():
    st.title("Seek Jobs Search")

    tab1, tab2, tab3 = st.tabs(["Search", "CV Profile", "Stats"])

    with tab1:
        col1, col2 = st.columns([3, 1])

        with col1:
            search = st.text_input("Search", placeholder="Keywords...")

        with col2:
            triage_filter = st.selectbox(
                "Status",
                ["unreviewed", "all", "yes", "no"],
                index=0
            )

        with st.expander("More Filters"):
            filter_col1, filter_col2, filter_col3 = st.columns(3)

            with filter_col1:
                regions = [""] + db.get_regions()
                region = st.selectbox("Region", regions)

            with filter_col2:
                job_types = [""] + db.get_job_types()
                job_type = st.selectbox("Job Type", job_types)

            with filter_col3:
                sort_options = {"Date Posted": "date_listed", "Date Scraped": "first_seen"}
                sort_label = st.selectbox("Sort By", list(sort_options.keys()))
                sort_by = sort_options[sort_label]

        if st.button("AI Match (uses GPT)", type="secondary"):
            st.session_state["do_ai_match"] = True

        st.divider()

        triage_arg = triage_filter if triage_filter != "all" else None

        jobs, total = db.get_jobs(
            search=search if search else None,
            region=region if region else None,
            job_type=job_type if job_type else None,
            triage_status=triage_arg,
            sort_by=sort_by,
            limit=50
        )

        show_score = False
        if st.session_state.get("do_ai_match"):
            cv_text = db.get_cv()
            if cv_text:
                with st.spinner("Ranking jobs with GPT..."):
                    jobs = rank_jobs_with_gpt(jobs, cv_text)
                show_score = True
            else:
                st.warning("Add your CV in the CV Profile tab first")
            st.session_state["do_ai_match"] = False

        st.caption(f"Showing {len(jobs)} of {total} jobs")

        for job in jobs:
            render_job_card(job, show_score=show_score)
            st.divider()

    with tab2:
        st.subheader("Your CV Profile")
        st.caption("Paste your CV text here for AI job matching")

        current_cv = db.get_cv()

        cv_text = st.text_area(
            "CV Text",
            value=current_cv,
            height=400,
            placeholder="Paste your CV here..."
        )

        if st.button("Save CV"):
            if cv_text.strip():
                db.save_cv(cv_text.strip())
                st.success("CV saved!")
            else:
                st.warning("CV is empty")

    with tab3:
        st.subheader("Database Stats")

        stats = db.get_stats()

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Jobs", stats.get("total", 0))

        with col2:
            st.metric("Unreviewed", stats.get("unreviewed", 0))

        with col3:
            st.metric("Yes", stats.get("yes", 0))

        with col4:
            st.metric("No", stats.get("no", 0))


if __name__ == "__main__":
    main()
