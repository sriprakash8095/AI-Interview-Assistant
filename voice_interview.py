import json
import asyncio
import edge_tts
import pygame
import speech_recognition as sr
import uuid
import os
from groq import Groq
from dotenv import load_dotenv
load_dotenv()

client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)
# ==========================
# LOAD QUESTIONS
# ==========================

with open("questions.json", "r") as f:
    questions = json.load(f)

answers = []

print("Questions Loaded Successfully")
print("Total Questions:", len(questions))

# ==========================
# SPEAK FUNCTION
# ==========================

async def speak(text):

    filename = f"{uuid.uuid4()}.mp3"

    communicate = edge_tts.Communicate(
        text=text,
        voice="en-US-AriaNeural"
    )

    await communicate.save(filename)

    if not pygame.mixer.get_init():
        pygame.mixer.init()

    pygame.mixer.music.load(filename)

    pygame.mixer.music.play()

    while pygame.mixer.music.get_busy():
        await asyncio.sleep(0.1)

    pygame.mixer.music.unload()

    os.remove(filename)
def generate_followup(question, answer):
        prompt = f"""
You are an experienced technical interviewer.

Original Question:
{question}

Candidate Answer:
{answer}

Ask ONE short and specific follow-up question.

Rules:
- Maximum 20 words
- Directly related to the answer
- Sound like a real interviewer
- Ask only one question

Return ONLY the question.
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

        followup=response.choices[0].message.content
        return followup
# ==========================
# LISTEN FUNCTION
# ==========================

def listen():

    recognizer = sr.Recognizer()
    recognizer.pause_threshold = 3
    recognizer.non_speaking_duration = 1

    with sr.Microphone() as source:

        print("🎤 Listening...")

        recognizer.adjust_for_ambient_noise(
            source,
            duration=1
        )

        try:

            audio = recognizer.listen(
                source,
                timeout=None,
                phrase_time_limit=60
            )

        except Exception as e:

            print("Listen Error:", e)

            return "No response"

    try:

        text = recognizer.recognize_google(audio)

        print("You:", text)

        return text

    except Exception as e:

        print("Recognition Error:", e)

        return "No response"

# ==========================
# MAIN INTERVIEW
# ==========================

async def run_interview():

    print("\n======================")
    print("AI INTERVIEW STARTED")
    print("======================\n")

    await speak(
        "Welcome to the AI Interview Assistant. Let's begin."
    )

    for i, q in enumerate(questions, start=1):

        print(f"\nQuestion {i}")
        print(q)

        await speak(q)

        answer = listen()

# Generate follow-up
        followup = generate_followup(
        q,
        answer
     )

        print("\nFollow-up Question:")
        print(followup)

        await speak(followup)

        followup_answer = listen()

        answers.append(
            {
                "question": q,
                "answer": answer,
                "followup_question": followup,
                "followup_answer": followup_answer
            }
        )

    # Save answers

    with open("answers.json", "w") as f:

        json.dump(
            answers,
            f,
            indent=4
        )

    await speak(
        "Interview completed. Thank you for participating."
    )

    print("\nInterview Completed")

    print("\nAnswers Saved To answers.json")

# ==========================
# START PROGRAM
# ==========================

asyncio.run(run_interview())