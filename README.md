# Multi-Agent AI Recruitment System

A Python-based recruitment application with two agents: a rule-based Resume Screening Agent and an Interview Scheduling Agent.

## Features

### Agent 1: Resume Screening
- Upload a candidate resume in PDF format.
- Extract text from the resume.
- Compare resume skills with the job description.
- Display matched skills, missing skills, match score, and recommendation.

### Agent 2: Interview Scheduling
- Manage interviewer availability.
- Find available interview slots.
- Schedule 30-minute interviews.
- Store interview records using SQLite.
- Check for scheduling conflicts.

## Technology Stack
- Python
- Streamlit
- PyMuPDF
- SQLite

## Run Locally

1. Clone the repository.
2. Create and activate a virtual environment.
3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Start the application:

   ```bash
   python -m streamlit run app.py
   ```

## Project Structure

```text
multi_agent_recruitment/
├── app.py
├── requirements.txt
├── agents/
├── tools/
└── database/
```

## Limitations

- Resume matching is rule-based and depends on recognized skills.
- Screening scores are preliminary and should not replace human review.
- The application is an academic demonstration, not a production recruitment platform.
- SQLite data may not persist across resets on temporary hosting environments.

## Future Enhancements
- Improve resume parsing and candidate detail extraction.
- Add authentication and role-based access.
- Use persistent database hosting.
- Add automated email notifications and interview reminders.
