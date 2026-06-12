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
if "interview_completed" not in st.session_state:
    st.session_state["interview_completed"] = False
if st.button("🗑 Clear Previous Interview"):

    if os.path.exists("questions.json"):
        os.remove("questions.json")

    if os.path.exists("answers.json"):
        os.remove("answers.json")

    st.success("Previous interview deleted")

    st.rerun()

# ==========================
# RESUME UPLOAD
# ==========================

uploaded_file = st.file_uploader(
    "Upload Resume",
    type=["pdf"]
)

# ==========================
# PROCESS RESUME
# ==========================

if uploaded_file:

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
    # GENERATE QUESTIONS
    # ==========================

    if st.button("Generate Questions"):

        prompt = f"""
        Based on the following resume,
        generate exactly 5 interview questions.

        Rules:
        - Return only questions
        - One question per line
        - No numbering
        - No headings

        Resume:
        {resume_text}
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

if len(voice_answers) > 0:

    if st.button(
        "🤖 Evaluate Voice Interview"
    ):

        st.subheader(
            "Interview Evaluation"
        )

        scores = []

        for item in voice_answers:

            eval_prompt = f"""
            Question:
            {item['question']}

            Answer:
            {item['answer']}

            Evaluate the answer.

            Return EXACTLY:

            Score: X

            Feedback: feedback text
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

            st.divider()

            match = re.search(
                r"Score:\s*(\d+)",
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

        # ==========================
        # AI FEEDBACK SUMMARY
        # ==========================

        summary_prompt = f"""
        Based on this interview performance:

        Overall Score: {average_score:.2f}/10

        Give:

        1. Strengths
        2. Weaknesses
        3. Suggestions for Improvement

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
                )
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

    st.dataframe(
        df,
        use_container_width=True
    )