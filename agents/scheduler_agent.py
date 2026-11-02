
from datetime import date, datetime, time

from database.database import (
    get_available_slots,
    book_interview,
)


def find_interview_slots(interviewer, slot_date):
    """Return free slots for the selected interviewer and date."""

    try:
        selected_date = date.fromisoformat(slot_date)
    except ValueError:
        raise ValueError("Date must use YYYY-MM-DD format.")

    if selected_date < date.today():
        raise ValueError("Please choose today or a future date.")

    return get_available_slots(interviewer, slot_date)


def schedule_interview(
    candidate_name,
    candidate_email,
    interviewer,
    slot_date,
    start_time,
    duration_minutes=30,
):
    """Book a free slot for the candidate."""

    if not candidate_name.strip():
        raise ValueError("Candidate name is required.")

    if duration_minutes <= 0:
        raise ValueError("Duration must be positive.")

    try:
        selected_date = date.fromisoformat(slot_date)
        start = datetime.strptime(start_time, "%H:%M").time()
    except ValueError:
        raise ValueError("Use YYYY-MM-DD for date and HH:MM for time.")

    if selected_date < date.today():
        raise ValueError("Cannot schedule an interview in the past.")

    start_minutes = start.hour * 60 + start.minute
    end_minutes = start_minutes + duration_minutes

    if end_minutes > 24 * 60:
        raise ValueError("Interview cannot extend past midnight.")

    end = time(end_minutes // 60, end_minutes % 60).strftime("%H:%M")

    # Database validates availability and checks for conflicts.
    book_interview(
        candidate_name=candidate_name.strip(),
        candidate_email=candidate_email.strip(),
        interviewer=interviewer,
        slot_date=slot_date,
        start_time=start.strftime("%H:%M"),
        end_time=end,
    )

    return {
        "candidate_name": candidate_name.strip(),
        "candidate_email": candidate_email.strip(),
        "interviewer": interviewer,
        "date": slot_date,
        "start_time": start.strftime("%H:%M"),
        "end_time": end,
        "status": "Scheduled",
    }
