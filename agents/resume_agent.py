
import re


def analyze_resume(resume_text: str, job_description: str) -> dict:
    """Screen a resume using local, rule-based skill matching."""

    if not resume_text.strip():
        raise ValueError("No readable text was found in the resume.")

    if not job_description.strip():
        raise ValueError("Please provide a job description.")

    text = resume_text.lower()
    job = job_description.lower()

    skill_groups = {
        "Python": ["python"],
        "Java": ["java"],
        "C++": ["c++"],
        "SQL": ["sql", "postgresql", "mysql"],
        "Django": ["django"],
        "FastAPI": ["fastapi"],
        "REST API": ["rest api", "restful api"],
        "Docker": ["docker"],
        "Kubernetes": ["kubernetes"],
        "MongoDB": ["mongodb"],
        "Git": ["git", "github"],
        "Machine Learning": ["machine learning", "scikit-learn"],
        "HTML": ["html"],
        "CSS": ["css"],
        "JavaScript": ["javascript"],
    }

    def contains_term(source, term):
        pattern = r"(?<!\w)" + re.escape(term.lower()) + r"(?!\w)"
        return bool(re.search(pattern, source))

    required_skills = [
        skill
        for skill, terms in skill_groups.items()
        if any(contains_term(job, term) for term in terms)
    ]

    if not required_skills:
        raise ValueError(
            "No supported skills were recognized in the job description. "
            "Add specific skills such as Python, SQL, Django or Docker."
        )

    skills = [
        skill
        for skill, terms in skill_groups.items()
        if any(contains_term(text, term) for term in terms)
    ]

    matching = [s for s in required_skills if s in skills]
    missing = [s for s in required_skills if s not in skills]

    score = round(len(matching) / len(required_skills) * 100)

    # Simple heuristic: this is a preliminary screening indicator,
    # not a validated prediction of candidate performance.
    if score >= 70:
        recommendation = "Shortlisted"
    elif score >= 40:
        recommendation = "Needs Human Review"
    else:
        recommendation = "Not Shortlisted"

    email_match = re.search(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
        resume_text
    )

   
    name = "Not reliably identified"

    excluded_phrases = [
        "resume",
        "curriculum vitae",
        "candidate screening report",
        "ai candidate",
        "screening report",
        "professional summary",
        "work experience",
        "technical skills",
        "contact information",
        "education",
        "projects",
        "important note",
        "disclaimer",
        "preliminary assessment",
        "recruiter should review",
    ]

    for line in resume_text.splitlines():
        line = line.strip()
        normalized = line.lower().strip(" :-|")

        if (
            line
            and len(line.split()) <= 4
            and len(line) <= 60
            and not re.search(r"[@\d]", line)
            and not any(
                phrase in normalized
                for phrase in excluded_phrases
            )
            and not normalized.startswith(
                ("note:", "warning:", "important:")
            )
        ):
            name = line
            break

    education_terms = [
        "B.Tech", "M.Tech", "B.E.", "M.E.",
        "B.Sc", "M.Sc", "BCA", "MCA", "Ph.D."
    ]
    education = [
        term for term in education_terms
        if term.lower() in text
    ]

    return {
        "candidate_name": name,
        "email": email_match.group(0) if email_match else "Not found",
        "skills": skills,
        "education": education,
        "experience_summary": (
            "Review the resume manually for work experience and projects."
        ),
        "matching_skills": matching,
        "missing_skills": missing,
        "match_score": score,
        "recommendation": recommendation,
        "explanation": (
            f"{len(matching)} of {len(required_skills)} recognized "
            f"job skills were found in the resume. The score is based "
            "only on skill matches; it does not evaluate experience, "
            "skill proficiency, or overall candidate suitability."
        ),
    }
