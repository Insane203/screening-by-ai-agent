
import streamlit as st
from datetime import date

from tools.resume_parser import extract_text_from_pdf
from agents.resume_agent import analyze_resume
from agents.scheduler_agent import (
    find_interview_slots,
    schedule_interview,
)
from database.database import (
    initialize_database,
    seed_sample_availability,
    get_interviewers,
    get_scheduled_interviews,
    add_availability,
)


# ==================================================
# INITIALIZATION
# ==================================================

st.set_page_config(
    page_title="Multi-Agent AI Recruitment System",
    page_icon="🤝",
    layout="wide",
)

initialize_database()
seed_sample_availability()

if "assessment" not in st.session_state:
    st.session_state.assessment = None

if "resume_text" not in st.session_state:
    st.session_state.resume_text = ""

if "available_slots" not in st.session_state:
    st.session_state.available_slots = []

if "booking_message" not in st.session_state:
    st.session_state.booking_message = None


# ==================================================
# APPLICATION HEADER
# ==================================================

st.title("Multi-Agent AI Recruitment System")

st.markdown(
    """
    **Agent 1:** Resume Screening  
    **Agent 2:** Interview Scheduling

    Upload a resume, evaluate the candidate against a job description,
    and schedule an interview using interviewer availability.
    """
)

st.divider()


# ==================================================
# AGENT 1: RESUME SCREENING
# ==================================================

st.header("Agent 1 — Resume Screening")

with st.form("resume_form"):
    job_title = st.text_input(
        "Job Title",
        placeholder="Python Backend Developer",
    )

    job_description = st.text_area(
        "Job Description",
        placeholder=(
            "Enter required skills, qualifications, "
            "experience, and responsibilities..."
        ),
        height=160,
    )

    resume = st.file_uploader(
        "Upload Candidate Resume (PDF)",
        type=["pdf"],
    )

    analyze_clicked = st.form_submit_button(
        "Analyze Resume",
        type="primary",
    )


if analyze_clicked:
    if resume is None:
        st.error("Please upload a PDF resume.")

    elif not job_title.strip():
        st.error("Please enter the job title.")

    elif not job_description.strip():
        st.error("Please enter the job description.")

    else:
        try:
            with st.spinner("Agent 1 is screening the resume..."):
                resume_text = extract_text_from_pdf(resume)

                if not resume_text.strip():
                    raise ValueError(
                        "No readable text was found in the PDF. "
                        "The document may require OCR."
                    )

                assessment = analyze_resume(
                    resume_text,
                    job_description,
                )

            st.session_state.assessment = assessment
            st.session_state.resume_text = resume_text
            st.session_state.job_title = job_title.strip()

            # Clear old slot selections after a new assessment.
            st.session_state.available_slots = []
            st.session_state.booking_message = None

        except Exception as exc:
            st.error(f"Resume screening failed: {exc}")


# ==================================================
# DISPLAY SCREENING REPORT
# ==================================================

assessment = st.session_state.assessment

if assessment:
    st.subheader("Screening Report")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Estimated Job Match",
            f'{assessment["match_score"]}%',
        )

    with col2:
        st.write("**Candidate**")
        st.write(assessment["candidate_name"])

    with col3:
        st.write("**Recommendation**")
        st.write(assessment["recommendation"])

    st.write(
        "**Email:**",
        assessment["email"],
    )

    st.write(
        "**Skills Found:**",
        ", ".join(assessment["skills"]) or "None identified",
    )

    st.write(
        "**Matching Skills:**",
        ", ".join(assessment["matching_skills"]) or "None identified",
    )

    st.write(
        "**Missing or Undemonstrated Skills:**",
        ", ".join(assessment["missing_skills"]) or "None identified",
    )

    st.write("**Education**")

    education = assessment.get("education", [])

    if education:
        for item in education:
            st.write(f"- {item}")
    else:
        st.write("No education details identified.")

    st.write("**Experience Summary**")
    st.write(
        assessment.get(
            "experience_summary",
            "No experience summary available.",
        )
    )

    st.write("**Screening Explanation**")
    st.write(assessment["explanation"])

    st.info(
        "The score is a preliminary, rule-based skills match, "
        "not a validated measure of candidate performance. "
        "A recruiter should review the resume before deciding "
        "whether to proceed."
    )

    st.divider()


# ==================================================
# AGENT 2: INTERVIEW SCHEDULING
# ==================================================

st.header("Agent 2 — Interview Scheduling")

if assessment is None:
    st.info(
        "First complete resume screening. "
        "The scheduling section will use the screening result."
    )

elif assessment["recommendation"] != "Shortlisted":
    st.warning(
        "This candidate was not automatically shortlisted. "
        "Review the screening report before deciding whether "
        "to proceed with scheduling."
    )

    if st.checkbox("HR approves this candidate for scheduling"):
        st.session_state.hr_override = True
    else:
        st.session_state.hr_override = False

    if not st.session_state.hr_override:
        st.stop()

    st.caption(
        "HR has chosen to proceed despite the preliminary screening result."
    )


if assessment and (
    assessment["recommendation"] == "Shortlisted"
    or st.session_state.get("hr_override", False)
):
    st.write(
        "Review the candidate information, select an interviewer "
        "and date, and find an available interview slot."
    )

    default_name = assessment.get("candidate_name", "")

    if default_name in (
        "Not reliably identified",
        "Unknown",
        "Important note",
        "",
    ):
        default_name = ""

    default_email = assessment.get("email", "")

    if default_email == "Not found":
        default_email = ""

    interviewers = get_interviewers()

    with st.form("scheduling_search_form"):
        candidate_name = st.text_input(
            "Candidate Name (verify before scheduling)",
            value="",
            placeholder="Enter the actual candidate name",
        )

        candidate_email = st.text_input(
            "Candidate Email",
            value=default_email,
        )

        if interviewers:
            interviewer = st.selectbox(
                "Select Interviewer",
                interviewers,
            )
        else:
            interviewer = None
            st.warning(
                "No interviewers are available. Add availability below."
            )

        interview_date = st.date_input(
            "Interview Date",
            value=date.today(),
            min_value=date.today(),
        )

        interview_duration = st.selectbox(
            "Interview Duration",
            [30],
            format_func=lambda x: f"{x} minutes",
        )

        check_slots_clicked = st.form_submit_button(
            "Check Available Slots",
            type="primary",
        )

    if check_slots_clicked:
        if not candidate_name.strip():
            st.error(
                "Please enter or correct the candidate name."
            )

        elif not interviewer:
            st.error("Please select an interviewer.")

        else:
            try:
                with st.spinner(
                    "Agent 2 is checking interviewer availability..."
                ):
                    slots = find_interview_slots(
                        interviewer,
                        interview_date.isoformat(),
                    )

                # Only show slots for the current search.
                st.session_state.available_slots = slots
                st.session_state.selected_interviewer = interviewer
                st.session_state.selected_date = interview_date.isoformat()
                st.session_state.selected_duration = interview_duration
                st.session_state.schedule_candidate = candidate_name.strip()
                st.session_state.schedule_email = candidate_email.strip()

                st.session_state.booking_message = None

            except Exception as exc:
                st.error(f"Could not check availability: {exc}")

    slots = st.session_state.available_slots

    if slots:
        st.subheader("Available Interview Slots")

        st.write(
            "**Interviewer:**",
            st.session_state.selected_interviewer,
        )

        st.write(
            "**Date:**",
            st.session_state.selected_date,
        )

        slot_labels = [
            f'{slot["start_time"]} – {slot["end_time"]}'
            for slot in slots
        ]

        selected_slot_label = st.selectbox(
            "Choose a free time slot",
            slot_labels,
            key="selected_slot_label",
        )

        if st.button("Schedule Interview", type="primary"):
            try:
                selected_index = slot_labels.index(
                    selected_slot_label
                )

                chosen_slot = slots[selected_index]

                result = schedule_interview(
                    candidate_name=st.session_state.schedule_candidate,
                    candidate_email=st.session_state.schedule_email,
                    interviewer=st.session_state.selected_interviewer,
                    slot_date=st.session_state.selected_date,
                    start_time=chosen_slot["start_time"],
                    duration_minutes=st.session_state.selected_duration,
                )

                st.session_state.available_slots = []
                st.session_state.booking_message = result

                st.success("Interview scheduled successfully!")

            except Exception as exc:
                st.error(
                    f"Scheduling failed: {exc}. "
                    "Check availability and select another slot if needed."
                )

    elif "selected_date" in st.session_state:
        st.info(
            "No available slots were found for the last search. "
            "Choose another date or interviewer and check again."
        )

    if st.session_state.booking_message:
        result = st.session_state.booking_message

        st.subheader("Interview Confirmation")

        st.success("Interview Scheduled")

        col1, col2 = st.columns(2)

        with col1:
            st.write("**Candidate:**", result["candidate_name"])
            st.write("**Email:**", result["candidate_email"] or "Not provided")
            st.write("**Interviewer:**", result["interviewer"])

        with col2:
            st.write("**Date:**", result["date"])
            st.write(
                "**Time:**",
                f'{result["start_time"]} – {result["end_time"]}',
            )
            st.write("**Status:**", result["status"])


# ==================================================
# SCHEDULED INTERVIEWS
# ==================================================

st.divider()
st.header("Scheduled Interviews")

interviews = get_scheduled_interviews()

if interviews:
    st.dataframe(
        interviews,
        use_container_width=True,
        hide_index=True,
    )
else:
    st.info("No interviews have been scheduled yet.")


# ==================================================
# HR: MANAGE INTERVIEWER AVAILABILITY
# ==================================================

st.divider()
st.header("Manage Interviewer Availability")

st.write(
    "Add free or busy slots for interviewers. "
    "Use the same date and time format throughout the calendar."
)

with st.form("availability_form"):
    interviewer_name = st.text_input(
        "Interviewer Name",
        placeholder="Dr. Sharma",
    )

    availability_date = st.date_input(
        "Availability Date",
        value=date.today(),
        min_value=date.today(),
        key="availability_date",
    )

    time_options = [
        f"{hour:02d}:{minute:02d}"
        for hour in range(9, 18)
        for minute in (0, 30)
    ]

    start_index = st.selectbox(
        "Start Time",
        range(len(time_options) - 1),
        index=0,
        format_func=lambda i: time_options[i],
    )

    end_index = st.selectbox(
        "End Time",
        range(1, len(time_options)),
        index=1,
        format_func=lambda i: time_options[i],
    )

    availability_status = st.selectbox(
        "Status",
        ["Free", "Busy"],
    )

    add_availability_clicked = st.form_submit_button(
        "Add Availability",
        type="primary",
    )

if add_availability_clicked:
    slot_start = time_options[start_index]
    slot_end = time_options[end_index]

    if not interviewer_name.strip():
        st.error("Please enter the interviewer name.")

    elif slot_start >= slot_end:
        st.error("End time must be later than start time.")

    else:
        try:
            add_availability(
                interviewer=interviewer_name.strip(),
                slot_date=availability_date.isoformat(),
                start_time=slot_start,
                end_time=slot_end,
                status=availability_status,
            )

            st.success(
                f"{availability_status} availability added for "
                f"{interviewer_name.strip()} on {availability_date}."
            )

        except Exception as exc:
            st.error(f"Could not add availability: {exc}")


st.caption(
    "Academic demonstration: resume screening uses local rule-based "
    "matching, and interview availability is stored in SQLite. "
    "Verify candidate details and calendar entries before relying "
    "on a scheduling result."
)
