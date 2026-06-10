import streamlit as st
import pdfplumber
from groq import Groq
from dotenv import load_dotenv
import os
import re

# ==========================
# LOAD ENV VARIABLES
# ==========================

load_dotenv()

API_KEY = os.getenv("GROQ_API_KEY")

client = Groq(
    api_key=API_KEY
)

# ==========================
# UI
# ==========================

st.title("AI Interview Assistant")

uploaded_file = st.file_uploader(
    "Upload Resume",
    type=["pdf"]
)

# ==========================
# RESUME PROCESSING
# ==========================

if uploaded_file:

    resume_text = ""

    with pdfplumber.open(uploaded_file) as pdf:

        for page in pdf.pages:

            text = page.extract_text()

            if text:
                resume_text += text + "\n"

    st.success("Resume Uploaded Successfully")

    st.subheader("Resume Content")

    st.text_area(
        "Extracted Text",
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

        Resume:
        {resume_text}

        Return only questions.
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

        questions = response.choices[0].message.content

        st.session_state["questions"] = questions.split("\n")

# ==========================
# DISPLAY QUESTIONS
# ==========================

if "questions" in st.session_state:

    st.subheader("Interview Questions")

    answers = []

    for i, q in enumerate(st.session_state["questions"]):

        if q.strip() == "":
            continue

        st.write(q)

        ans = st.text_area(
            f"Answer {i+1}",
            key=f"ans{i}"
        )

        answers.append((q, ans))

    # ==========================
    # EVALUATION
    # ==========================

    if st.button("Evaluate Answers"):

        st.subheader("Results")

        scores = []

        for q, ans in answers:

            if ans.strip() == "":
                continue

            eval_prompt = f"""
            Question:
            {q}

            Answer:
            {ans}

            Evaluate this answer.

            Return EXACTLY in this format:

            Score: X

            Feedback: Your feedback here
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

            match = re.search(
                r"Score:\s*(\d+)",
                result
            )

            if match:
                scores.append(
                    int(match.group(1))
                )

            st.write("### Question")
            st.write(q)

            st.write("### Evaluation")
            st.write(result)

            st.divider()

        # ==========================
        # OVERALL SCORE
        # ==========================

        if len(scores) > 0:

            average_score = (
                sum(scores) / len(scores)
            )

            st.subheader(
                "Overall Interview Score"
            )

            st.success(
                f"{average_score:.2f}/10"
            )

        st.success(
            "Interview Evaluation Completed"
        )