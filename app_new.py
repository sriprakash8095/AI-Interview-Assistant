import streamlit as st
import pdfplumber
from groq import Groq
from dotenv import load_dotenv
import os
import json
import re
import subprocess
from datetime import datetime
import pandas as pd
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer
)

from reportlab.lib.styles import getSampleStyleSheet
import matplotlib.pyplot as plt

def generate_pdf_report(
    average_score,
    summary,
    voice_answers
):

    pdf = SimpleDocTemplate(
        "Interview_Report.pdf"
    )

    styles = getSampleStyleSheet()

    content = []

    content.append(
        Paragraph(
            "AI Interview Report",
            styles["Title"]
        )
    )

    content.append(
        Spacer(1, 12)
    )

    content.append(
        Paragraph(
            f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            styles["Normal"]
        )
    )

    content.append(
        Paragraph(
            f"Overall Score: {average_score:.2f}/10",
            styles["Normal"]
        )
    )

    content.append(
        Spacer(1, 12)
    )

    content.append(
        Paragraph(
            summary.replace("\n", "<br/>"),
            styles["BodyText"]
        )
    )

    content.append(
        Spacer(1, 12)
    )

    for item in voice_answers:

        content.append(
            Paragraph(
                f"<b>Question:</b> {item['question']}",
                styles["BodyText"]
            )
        )

        content.append(
            Paragraph(
                f"<b>Answer:</b> {item['answer']}",
                styles["BodyText"]
            )
        )

        content.append(
            Spacer(1, 10)
        )

    pdf.build(content)

    return "Interview_Report.pdf"
# ==========================
# LOAD ENV VARIABLES
# ==========================

load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

# ==========================
# HISTORY FILE
# ==========================

HISTORY_FILE = "interview_history.json"

if not os.path.exists(HISTORY_FILE):

    with open(HISTORY_FILE, "w") as f:

        json.dump([], f)
# ==========================
# Feedback FILE
# ==========================
FEEDBACK_FILE = "feedback.json"

if not os.path.exists(FEEDBACK_FILE):

    with open(FEEDBACK_FILE, "w") as f:

        json.dump([], f)

# ==========================
# PAGE CONFIG
# ==========================

st.set_page_config(
    page_title="AI Interview Assistant",
    page_icon="🤖"
)

st.title("🤖 AI Interview Assistant")
interview_type = st.selectbox(
    "🎯 Select Interview Type",
    [
        "Resume Based",
        "HR",
        "Python",
        "Java",
        "Machine Learning",
        "IoT"
    ]
)
difficulty = st.selectbox(
    "📚 Difficulty Level",
    [
        "Easy",
        "Medium",
        "Hard"
    ]
)
if difficulty == "Easy":

    question_count = 5

elif difficulty == "Medium":

    question_count = 7

else:

    question_count = 8
if interview_type != "Resume Based":

    if st.button("Generate Questions"):

        prompt = f"""
Generate exactly {question_count}
{interview_type}
interview questions.

Difficulty Level: {difficulty}

Candidate Level: Fresher

Rules:
- Return only questions
- One question per line
- No numbering
- No headings
"""

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        questions_text = response.choices[0].message.content

        clean_questions = []

        for line in questions_text.split("\n"):

            line = line.strip()

            if line:

                clean_questions.append(line)

        st.session_state["questions"] = clean_questions

        with open("questions.json", "w") as f:

            json.dump(
                clean_questions,
                f,
                indent=4
            )
         
if "interview_completed" not in st.session_state:
    st.session_state["interview_completed"] = False
if st.button("🗑 Clear Previous Interview"):
    st.session_state["interview_completed"] = False

    if os.path.exists("questions.json"):
        os.remove("questions.json")

    if os.path.exists("answers.json"):
        os.remove("answers.json")

    st.success("Previous interview deleted")

    st.rerun()

# ==========================
# RESUME UPLOAD
# ==========================

uploaded_file = None

if interview_type == "Resume Based":

    uploaded_file = st.file_uploader(
        "Upload Resume",
        type=["pdf"]
    )

# ==========================
# PROCESS RESUME
# ==========================

if (
    interview_type == "Resume Based"
    and uploaded_file
):

    resume_text = ""

    with pdfplumber.open(uploaded_file) as pdf:

        for page in pdf.pages:

            text = page.extract_text()

            if text:

                resume_text += text + "\n"
    if (
    "last_resume_text" not in st.session_state
    or st.session_state["last_resume_text"] != resume_text 
    ):

        st.session_state["last_resume_text"] = resume_text

        if "resume_analysis" in st.session_state:
            del st.session_state["resume_analysis"]

    st.success("✅ Resume Uploaded Successfully")

    st.subheader("Resume Content")

    st.text_area(
        "Extracted Resume",
        resume_text,
        height=250
    )
    # ==========================
# RESUME VALIDATION
# ==========================

    resume_score_prompt = f"""
You are an ATS resume checker.

First determine whether this document is a professional resume.

A resume must contain:

* Candidate name
* Education
* Skills
* Contact information

If this document is NOT a resume,
return ONLY:

NOT A RESUME

If the document IS a valid resume:

Do NOT mention resume validation.

Do NOT say:

* This is a resume
* I classify this as a resume
* The document appears to be a resume
* Based on the document
* I have evaluated the resume

Evaluate strictly based on:

* Education
* Technical Skills
* Projects
* Certifications
* Internship Experience
* Achievements
* LinkedIn Profile
* GitHub Profile
* Resume Structure

Scoring Guidelines:

90-100 = Exceptional
(Strong projects, GitHub, LinkedIn, internships, achievements)

80-89 = Strong
(Good projects and skills, but missing one or two important sections)

70-79 = Good
(Multiple important sections missing)

60-69 = Average
(Significant gaps in profile)

Below 60 = Needs Improvement

Important Rules:

* Do NOT consider candidate name as a strength.
* Do NOT consider email as a strength.
* Do NOT consider phone number as a strength.
* Do NOT consider address as a strength.
* Do NOT consider contact information as a strength.
* Contact details are mandatory resume requirements and should never increase the ATS score.
* Focus only on professional qualifications and career readiness.
* Be strict while scoring.
* Do not assume skills, experience, internships, achievements or certifications that are not explicitly mentioned.
* If GitHub, LinkedIn, Internship and Achievements are all missing, ATS Score must NOT exceed 75.
Strength Rules:

- Do NOT consider spoken languages as strengths.
- Do NOT consider contact information as strengths.
- Do NOT consider basic resume sections as strengths.
- Prioritize projects, technical skills, certifications, internships, achievements and academic performance.

Return ONLY in this format:

ATS Score: X/100

Strengths:

* Point 1
* Point 2
* Point 3

Missing Sections:

* Point 1
* Point 2
* Point 3

Suggestions:

* Point 1
* Point 2
* Point 3

Document:

{resume_text}
"""

    if "resume_analysis" not in st.session_state:

        resume_response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
            {
                "role": "user",
                "content": resume_score_prompt
            }
        ]
    )

        st.session_state["resume_analysis"] = (
            resume_response
            .choices[0]
            .message.content
            .strip()
        )

    resume_analysis = st.session_state["resume_analysis"]

    if "NOT A RESUME" in resume_analysis:

        st.error(
        "❌ Uploaded file is not a valid resume."
    )

        st.stop()

    st.subheader("📄 Resume Analysis")

    st.write(resume_analysis)
    

    # ==========================
# ROLE MATCH ANALYSIS
# ==========================

selected_role = st.selectbox(
    "🎯 Target Job Role",
    [
        "Software Developer",
        "Python Developer",
        "Java Developer",
        "Data Analyst",
        "AI Engineer",
        "Frontend Developer",
        "Full Stack Developer"
    ]
)

if st.button("Check Role Match"):

    role_match_prompt = f"""
You are an experienced technical recruiter.

Analyze this resume ONLY for the role:

{selected_role}

Important Rules:
Do not write:
- implied
- inferred
- likely
- may indicate
- appears to
- suggests
- probably

Use only verifiable information from the resume.

* Evaluate ONLY skills, projects, certifications, technologies and experience relevant to the selected role.
* Do NOT increase the score because of unrelated skills.
* Do NOT assume any skills, experience or technologies that are not explicitly mentioned in the resume.
* Missing important role-specific skills should reduce the score.
* Strengths must be relevant to the selected role.
Do NOT consider spoken languages as strengths for technical roles.
Project Evaluation Rules:

- Classify projects only based on technologies explicitly mentioned.
- Do NOT assume a project is Full Stack, AI, Machine Learning, Frontend, Backend, Data Analytics, or Cloud based.
- If a project uses sensors, microcontrollers, embedded systems, or wireless communication, classify it as an IoT/Embedded project.
- If a project type is unclear, describe it generically as a technical project.
- Never infer technologies that are not explicitly stated.
Evidence-Based Evaluation Rules:


- Evaluate ONLY based on information explicitly mentioned in the resume.
- Do NOT infer technologies, frameworks, skills, or experience.
- Do NOT assume project complexity.
- Do NOT assume a project uses AI, Machine Learning, Deep Learning, NLP, Computer Vision, TensorFlow, PyTorch, APIs, Databases, Cloud, Frontend, Backend, OOP, or Data Structures unless explicitly mentioned.
- If a skill is not explicitly stated, treat it as missing.
- If a project description does not mention a technology, do not assume it was used.
- Give credit only for clearly documented skills, technologies, certifications, and project work.
A strength must directly improve the candidate's suitability for the selected role.

If a skill or project is unrelated to the selected role, do not include it in Strengths.

Example:
For Full Stack Developer roles, IoT projects, sensors, microcontrollers and embedded systems should not be listed as strengths unless they involve frontend, backend, database or API development.
Role Relevance Rules:

- Strengths must come ONLY from skills directly relevant to the selected role.
- Ignore unrelated skills while generating strengths.
- Unrelated skills may be mentioned in the resume but must not appear in Strengths.

Examples:

AI Engineer:
Relevant -> Python, Machine Learning, Deep Learning, TensorFlow, PyTorch, NLP, Computer Vision
Ignore -> Java, C, SQL, HTML, CSS

Frontend Developer:
Relevant -> HTML, CSS, JavaScript, React, Angular, Vue
Ignore -> Machine Learning, Deep Learning, IoT

Data Analyst:
Relevant -> SQL, Excel, Power BI, Tableau, Pandas, Data Visualization
Ignore -> IoT, Embedded Systems, Sensors

Java Developer:
Relevant -> Java, OOP, Collections, JDBC, Spring, Hibernate
Ignore -> Deep Learning, NLP, Computer Vision

Python Developer:
Relevant -> Python, APIs, Libraries, Python Projects
Ignore -> HTML, CSS unless directly related to projects

Evidence Verification Rules:

- Every strength must be directly supported by information explicitly present in the resume.
- Never connect a skill to a project unless the project description explicitly mentions that skill.
- Never assume a programming language was used in a project unless explicitly stated.
- If evidence is missing, do not mention it.
- Do not infer problem-solving ability from project completion alone.
- Mention problem-solving as a strength only if the resume explicitly describes challenges, solutions, optimization, debugging, achievements, or measurable outcomes.
- Completing a project alone is not evidence of problem-solving ability.

Role-Relevance Verification Rules:

- A project can be considered a strength only if the technologies used in the project directly match the selected role.
- Do not claim a project demonstrates frontend, backend, database, API, AI, ML, cloud, or full stack skills unless those technologies are explicitly mentioned.
- Never convert an IoT, embedded, hardware, or sensor-based project into a software, AI, frontend, backend, or full stack project.
- Describe projects exactly as documented in the resume.

Strength Rules:

* Mention only the top 3 strengths.
* Do NOT mention basic familiarity or beginner-level knowledge as strengths.
* Do NOT mention candidate name, education alone, email, phone number or contact information as strengths.
* Prefer projects, technical skills, certifications and problem-solving ability.
Only mention strengths directly supported by explicit resume evidence.

Do not infer:
- Leadership
- Teamwork
- Problem-solving
- Communication
- Analytical ability

unless explicitly mentioned or demonstrated with evidence.

Scoring Guide:

90-100 = Strongly qualified
75-89 = Good match
60-74 = Partial match
40-59 = Weak match
Below 40 = Poor match

Role Evaluation Criteria:

Software Developer:

* Programming Fundamentals
* Data Structures
* OOP Concepts
* Academic Projects
* Problem Solving

For Software Developer roles, do not heavily penalize missing advanced industry skills such as:

* System Design
* Cloud Computing
* DevOps
* Microservices

Python Developer:

* Python
* OOP
* Python Projects
* APIs
* Python Libraries
* Problem Solving

Java Developer:

* Java
* OOP
* Collections
* JDBC
* Spring
* Hibernate
* Java Projects

Data Analyst:

* SQL
* Excel
* Power BI
* Tableau
* Pandas
* Data Visualization
* Data Analysis Projects
* A score above 70 requires evidence of SQL and at least one analytics tool such as Excel, Power BI, Tableau or Pandas.

AI Engineer:

* Machine Learning
* Deep Learning
* Python
* TensorFlow
* PyTorch
* NLP
* Computer Vision
* Model Development
Only consider AI Engineer skills if explicitly mentioned in the resume.
Do not infer AI knowledge from generic software, IoT, automation, or sensor-based projects.
* A score above 70 requires practical AI/ML project experience and relevant frameworks.

Frontend Developer:

* HTML
* CSS
* JavaScript
* React
* Angular
* Vue
* Frontend Projects
* A score above 70 requires HTML, CSS, JavaScript and at least one frontend project.

Full Stack Developer:

* Frontend Technologies
* Backend Development
* Databases
* APIs
* Full Stack Projects
- A score above 70 should generally require evidence of both frontend and backend skills.
- Missing frontend technologies (HTML, CSS, JavaScript) should significantly reduce the score.
- Missing backend development experience should significantly reduce the score.
- Generic programming skills alone should not result in a high score.
- Database knowledge alone should not result in a high score.


Before generating Strengths:

1. Identify role-relevant skills.
2. Ignore unrelated skills.
3. Generate strengths only from relevant skills.

Return ONLY in this format:

Match Score: X%

Strengths:

* Point 1
* Point 2
* Point 3

Missing Skills:

* Point 1
* Point 2
* Point 3

Improvement Suggestions:

* Point 1
* Point 2
* Point 3

Resume:

{resume_text}
"""



    role_response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "user",
                "content": role_match_prompt
            }
        ]
    )

    role_analysis = (
        role_response
        .choices[0]
        .message.content
        .strip()
    )
    

    st.subheader(
    "🎯 Role Match Analysis"
)

    st.info(
    "⚠️ AI-generated analysis may occasionally make assumptions. Use this as guidance and not as a final role assessment."
    )

    st.write(role_analysis)
    # ==========================
    # GENERATE QUESTIONS
    # ==========================
    st.info(
    f"Selected Mode: {interview_type}"
)
    st.info(
    f"Difficulty: {difficulty}"
)
    if st.button("Generate Questions"):

        if interview_type == "Resume Based":

            prompt = f"""
            Based on the following resume,
generate exactly {question_count} interview questions.

Difficulty Level: {difficulty}

Rules:
- Return only questions
- One question per line
- No numbering
- No headings

Resume:
{resume_text}
            """

        else:

            prompt = f"""
    Generate exactly {question_count} {interview_type}
    interview questions suitable for
    a fresher candidate.

    Rules:
    - Return only questions
    - One question per line
    - No numbering
    - No headings
    """

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        questions_text = response.choices[0].message.content

        clean_questions = []

        for line in questions_text.split("\n"):

            line = line.strip()

            if line:

                clean_questions.append(line)

        st.session_state.clear()

        st.session_state["interview_completed"] = False

        st.session_state["questions"] = clean_questions

        if os.path.exists("answers.json"):
            os.remove("answers.json")

        with open("questions.json", "w") as f:

            json.dump(
            clean_questions,
            f,
            indent=4
        )
        st.success(
            "✅ Questions Generated Successfully"
        )

# ==========================
# SHOW QUESTIONS
# ==========================

if "questions" in st.session_state:

    saved_questions = st.session_state["questions"]

    st.subheader("📋 Interview Questions")

    for i, q in enumerate(
        saved_questions,
        start=1
    ):

        st.write(
            f"**Question {i}:** {q}"
        )

    if st.button("🎤 Start Voice Interview"):
        st.warning(
    "🎤 Voice Interview feature will be available in the next web version."
        )
        subprocess.run(
        ["python", "voice_interview.py"]
        )
        if os.path.exists("answers.json"):

            st.session_state["interview_completed"] = True

            st.success(
            "✅ Voice Interview Completed"
            )
# ==========================
# LOAD ANSWERS
# ==========================



voice_answers = []

if os.path.exists("answers.json"):

    with open("answers.json", "r") as f:

        voice_answers = json.load(f)

# ==========================
# SHOW CAPTURED ANSWERS
# ==========================

if (
    len(voice_answers) > 0
    and st.session_state.get(
        "interview_completed",
        False
    )
):

    st.subheader(
        "🎙 Captured Answers"
    )

    for item in voice_answers:

        st.write(
            f"### Question"
        )

        st.write(
            item["question"]
        )

        st.write(
            "### Answer"
        )

        st.write(
            item["answer"]
        )

        st.divider()

# ==========================
# EVALUATE INTERVIEW
# ==========================

if (
    len(voice_answers) > 0
    and st.session_state.get(
        "interview_completed",
        False
    )
):

    if st.button(
    "📊 Generate Interview Report"
):

        st.subheader(
            "Interview Evaluation"
        )

        scores = []

        for item in voice_answers:

            eval_prompt = f"""
Main Question:
{item['question']}

Main Answer:
{item['answer']}

Follow-up Question:
{item.get('followup_question', 'N/A')}

Follow-up Answer:
{item.get('followup_answer', 'N/A')}

Evaluate the candidate's overall response considering BOTH:
1. Main answer
2. Follow-up answer

Give a score between 0 and 10.

Return EXACTLY:

Score: 8

Feedback: Good answer with relevant details and strong follow-up response.
"""
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {
                        "role": "user",
                        "content": eval_prompt
                    }
                ]
            )

            result = response.choices[0].message.content

            st.write(
                "### Evaluation"
            )

            st.write(
                result
            )
            st.write("### 🤖 Follow-up Question")

            st.info(
            item.get(
            "followup_question",
            "No follow-up available"
            )
        )
            st.divider()

            match = re.search(
    r"Score:\s*([0-9]+)",
    result
)
            if match:

                scores.append(
                    int(match.group(1))
                )

        # ==========================
        # OVERALL SCORE
        # ==========================

        if len(scores) > 0:

            average_score = (
                sum(scores)
                / len(scores)
            )

            st.subheader(
                "🏆 Overall Score"
            )

            st.success(
                f"{average_score:.2f}/10"
            )
            readiness = average_score * 10

            st.subheader(
            "🚀 Interview Readiness"
            )

            st.progress(
                int(readiness)
            )

            st.success(
                f"{readiness:.0f}% Ready"
            )
            st.info(f"Type :{interview_type}| Difficulty: {difficulty}")
            # ==========================
# HIRING RECOMMENDATION
# ==========================

            st.subheader(
                "🏢 Hiring Recommendation"
            )

            if average_score >= 8:

                st.success(
             "✅ Recommended"
            )

                st.write(
        "Candidate demonstrated strong technical knowledge and communication skills."
        )

            elif average_score >= 6:

                st.warning(
                "⚠️ Consider for Further Evaluation"
                )

                st.write(
        "Candidate shows potential but needs improvement in some areas."
                )

            else:

                st.error(
                "❌ Not Recommended"
                )

                st.write(
                "Candidate should strengthen technical concepts and interview performance."
                )

        # ==========================
        # AI FEEDBACK SUMMARY
        # ==========================

        summary_prompt = f"""
        Based on this interview performance:

        Overall Score: {average_score:.2f}/10

        Provide:

1. Strengths
2. Weak Areas
3. Suggestions
4. Recommended Topics To Learn
        Keep it concise.

        Format:

        Strengths:
        - point 1
        - point 2

        Weaknesses:
        - point 1
        - point 2

        Suggestions:
        - point 1
        - point 2
        """

        summary_response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {
                    "role": "user",
                    "content": summary_prompt
                }
            ]
        )

        summary = summary_response.choices[0].message.content

        st.subheader(
            "📈 Performance Analysis"
        )

        st.write(summary)
        pdf_file = generate_pdf_report(
            average_score,
            summary,
            voice_answers
        )

        with open(
            pdf_file,
            "rb"
        ) as file:

            st.download_button(
                label="📄 Download Interview Report",
                data=file,
                file_name="Interview_Report.pdf",
                mime="application/pdf"
            )

        # ==========================
        # SAVE HISTORY
        # ==========================

        with open(HISTORY_FILE, "r") as f:
            history = json.load(f)
        
        
        history.append(
    {
        "date": datetime.now().strftime(
            "%Y-%m-%d %H:%M"
        ),
        "score": round(
            average_score,
            2
        ),
        "type": interview_type,
        "difficulty": difficulty
    }
)

        with open(HISTORY_FILE, "w") as f:
            json.dump(
                history,
                f,
                indent=4
            )

        st.success(
            "✅ Evaluation Saved"
        )
       
# ==========================
# DASHBOARD
# ==========================

st.subheader("📊 Dashboard")

with open(HISTORY_FILE, "r") as f:

    history = json.load(f)

if len(history) == 0:

    st.info(
        "No interview history available."
    )

else:

    scores = [
        item["score"]
        for item in history
    ]
    st.subheader("📈 Performance Trend")

    fig, ax = plt.subplots()

    ax.plot(
    range(1, len(scores) + 1),
    scores,
    marker="o",
    linewidth=2
)

    ax.set_ylim(0, 10)

    ax.grid(True)
    ax.set_ylim(0, 10)

    ax.set_xlabel("Interview Number")
    ax.set_ylabel("Score")
    ax.set_title("Interview Performance Trend")

    st.pyplot(fig)

    total_interviews = len(scores)

    best_score = max(scores)

    avg_score = (
        sum(scores)
        / len(scores)
    )

    latest_score = scores[-1]

    col1, col2 = st.columns(2)

    with col1:

        st.metric(
            "Total Interviews",
            total_interviews
        )

        st.metric(
            "Best Score",
            f"{best_score}/10"
        )

    with col2:

        st.metric(
            "Average Score",
            f"{avg_score:.2f}/10"
        )

        st.metric(
            "Latest Score",
            f"{latest_score}/10"
        )

    st.subheader(
        "📜 Interview History"
    )

    df = pd.DataFrame(history)
    df["type"] = df["type"].fillna("Unknown")

    df["difficulty"] = df["difficulty"].fillna("Unknown")
    if "type" not in df.columns:
        df["type"] = "Unknown"

    if "difficulty" not in df.columns:
        df["difficulty"] = "Unknown"
    selected_type = st.selectbox(
    "🎯 Filter Interview Type",
    ["All"] + list(df["type"].unique())
)

    if selected_type != "All":

        df = df[
        df["type"] == selected_type
    ]
    selected_difficulty = st.selectbox(
    "📚 Filter Difficulty",
    ["All"] + list(df["difficulty"].unique())
)

    if selected_difficulty != "All":

        df = df[
        df["difficulty"] == selected_difficulty
    ]

    st.dataframe(
        df[
        [
            "date",
            "type",
            "difficulty",
            "score"
        ]
    ],
    use_container_width=True
)
# ==========================
# USER FEEDBACK
# ==========================

# ==========================
# USER FEEDBACK
# ==========================

st.subheader("💡 User Feedback")

with st.form("feedback_form", clear_on_submit=True):

    rating = st.slider(
        "⭐ Rate this platform",
        1,
        5,
        5
    )

    feedback = st.text_area(
        "Suggest improvements or report issues"
    )

    submitted = st.form_submit_button(
        "Submit Feedback"
    )

    if submitted:

        with open(FEEDBACK_FILE, "r") as f:
            feedback_data = json.load(f)

        feedback_data.append(
            {
                "date": datetime.now().strftime(
                    "%Y-%m-%d %H:%M"
                ),
                "rating": rating,
                "feedback": feedback
            }
        )

        with open(FEEDBACK_FILE, "w") as f:
            json.dump(
                feedback_data,
                f,
                indent=4
            )

        st.success(
            "✅ Feedback Submitted Successfully"
        )