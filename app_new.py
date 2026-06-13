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
- Candidate name
- Education
- Skills
- Contact information

If this document is NOT a resume,
return ONLY:

NOT A RESUME

If this document IS a resume,
return ONLY in the following format:


For a fresher resume:


90-100 = Exceptional
(Must have GitHub, LinkedIn, Internship, Achievements)

80-89 = Strong
(Most sections present)

70-79 = Good
(Some sections missing)

60-69 = Average
(Multiple sections missing)

Below 60 = Weak



ATS Score: X/100

Strengths:
- Point 1
- Point 2

Missing Sections:
- Point 1
- Point 2

Suggestions:
- Point 1
- Point 2

Important:
- Do not explain your reasoning.
- Do not say "I need to check".
- Do not add extra text.
- Be strict while scoring.
- Deduct marks for missing GitHub, LinkedIn, internship experience, achievements, and poor project descriptions.
-do not add any extra text or explanations.
Do NOT include scoring rules in the output.
Do NOT explain the calculation.
Only return the final ATS Score and analysis.


Document:

{resume_text}
"""
    resume_response = client.chat.completions.create(
    model="llama-3.1-8b-instant",
        messages=[
        {
            "role": "user",
            "content": resume_score_prompt
        }
    ]
)
    

    resume_analysis = (
    resume_response
    .choices[0]
    .message.content
    .strip()
)

    if "NOT A RESUME" in resume_analysis:

        st.error(
        "❌ Uploaded file is not a valid resume."
    )

        st.stop()

    st.subheader("📄 Resume Analysis")

    st.write(resume_analysis)
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