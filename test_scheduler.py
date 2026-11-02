
from database.database import (
    initialize_database,
    seed_sample_availability,
    get_interviewers,
)
from agents.scheduler_agent import (
    find_interview_slots,
    schedule_interview,
)

initialize_database()
seed_sample_availability()

print("Interviewers:", get_interviewers())

slots = find_interview_slots(
    "Dr. Sharma",
    "2026-10-20",
)
print("Available slots:", slots)

if slots:
    slot = slots[0]

    result = schedule_interview(
        candidate_name="Test Candidate",
        candidate_email="test@example.com",
        interviewer="Dr. Sharma",
        slot_date="2026-10-20",
        start_time=slot["start_time"],
        duration_minutes=30,
    )

    print("Interview booked:", result)
