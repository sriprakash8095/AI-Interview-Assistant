import streamlit as st
import pdfplumber
from groq import Groq
from dotenv import load_dotenv
import os
import re
import json
from datetime import datetime
import pandas as pd
import speech_recognition as sr
import pyttsx3
import subprocess
# ==========================
# LOAD ENV VARIABLES
# ==========================

load_dotenv()

API_KEY = os.getenv("GROQ_API_KEY")

client = Groq(
    api_key=API_KEY
)
def speak(text):

    engine = pyttsx3.init()

    engine.say(text)

    engine.runAndWait()


def listen():

    r = sr.Recognizer()

    with sr.Microphone() as source:

        st.info("🎤 Listening...")

        audio = r.listen(source)

    try:

        text = r.recognize_google(audio)

        return text

    except:

        return "Could not understand"

# ==========================
# INTERVIEW HISTORY FILE
# ==========================

HISTORY_FILE = "interview_history.json"

if not os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, "w") as f:
        json.dump([], f)

# ==========================
# UI
# ==========================

st.set_page_config(
    page_title="AI Interview Assistant",
    page_icon="🤖"
)

st.title("🤖 AI Interview Assistant")

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

    st.success("✅ Resume Uploaded Successfully")

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
        Based on the following resume, generate exactly 5 interview questions.

        Rules:
        - Return ONLY questions.
        - No introduction.
        - No headings.
        - No explanations.
        - One question per line.

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

            if line == "":
                continue

            clean_questions.append(line)

# Save only after ALL questions are collected

        st.session_state["questions"] = clean_questions

        with open("questions.json", "w") as f:
            json.dump(clean_questions, f, indent=4)

        st.success("Questions saved successfully")
if "questions" in st.session_state:

    st.subheader("Interview Questions")

    answers = []

    question_no = 1

    for q in st.session_state["questions"]:

        st.write(f"### Question {question_no}")

        st.write(q)

        if st.button(
            f"🔊 Speak Question {question_no}",
            key=f"speak{question_no}"
        ):
            speak(q)

        ans = st.text_area(
            f"Answer {question_no}",
            key=f"ans{question_no}"
        )

        if st.button(
            f"🎤 Record Answer {question_no}",
            key=f"record{question_no}"
        ):

            voice_text = listen()

            st.success(
                f"You said: {voice_text}"
            )

        answers.append((q, ans))

        question_no += 1
        # ==========================
# VOICE INTERVIEW
# ==========================

if st.button("🎤 Start Voice Interview"):

    subprocess.run(
        ["python", "voice_interview.py"]
    )

    st.success(
        "Voice Interview Completed!"
    )

    # ==========================
    # EVALUATE ANSWERS
    # ==========================

    if st.button("Evaluate Answers"):

        st.subheader("Evaluation Results")

        scores = []

        # rest of your evaluation code...
        for q, ans in answers:

            if ans.strip() == "":
                continue

            eval_prompt = f"""
            Question:
            {q}

            Answer:
            {ans}

            Evaluate this answer.

            Return EXACTLY in the format:

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

            average_score = sum(scores) / len(scores)

            st.subheader("🏆 Overall Interview Score")

            st.success(
                f"{average_score:.2f}/10"
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
            "✅ Interview Evaluation Completed"
        )


    # ==========================
# DASHBOARD
# ==========================

st.subheader("📊 Dashboard")

with open(HISTORY_FILE, "r") as f:
    history = json.load(f)

if len(history) == 0:

    st.info("No interview history available.")

else:

    scores = [item["score"] for item in history]

    total_interviews = len(scores)
    best_score = max(scores)
    average_score = sum(scores) / len(scores)
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
            f"{average_score:.2f}/10"
        )

        st.metric(
            "Latest Score",
            f"{latest_score}/10"
        )

    st.subheader("📜 Interview History")

    df = pd.DataFrame(history)

    st.dataframe(
        df,
        use_container_width=True
    )