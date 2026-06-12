import asyncio
import edge_tts
import pygame

async def speak(text):

    communicate = edge_tts.Communicate(
        text,
        voice="en-US-AriaNeural"
    )

    await communicate.save("speech.mp3")

    pygame.mixer.init()

    pygame.mixer.music.load("speech.mp3")

    pygame.mixer.music.play()

    while pygame.mixer.music.get_busy():
        continue

asyncio.run(
    speak("Hello Sriprakash. Welcome to AI Interview Assistant")
)