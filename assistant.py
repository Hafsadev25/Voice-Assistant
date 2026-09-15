import datetime
import json
import os
import re
import smtplib
import threading
import time
import urllib.parse
import webbrowser
from email.mime.text import MIMEText

import nltk
import numpy as np
import pyttsx3
import requests
import sounddevice as sd
import speech_recognition as sr
from nltk.tokenize import word_tokenize

# Download NLTK data for tokenization
nltk.download("punkt", quiet=True)
nltk.download("punkt_tab", quiet=True)

# ---------------- CONFIGURATION & SETUP ----------------
CONFIG_FILE = "custom_commands.json"
WEATHER_API_KEY = "YOUR_OPENWEATHERMAP_API_KEY"
SENDER_EMAIL = "your_test_email@gmail.com"
SENDER_PASSWORD = "your_app_password"

KNOWLEDGE_BASE = {
    "python": "Python is a high-level, interpreted programming language known for readability.",
    "ai": "Artificial intelligence is the simulation of human intelligence in machines.",
    "oasis infobyte": "Oasis Infobyte provides internship opportunities and software solutions.",
    "earth": "Earth is the third planet from the Sun and the only astronomical object known to harbor life.",
}


def load_custom_commands():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}


def save_custom_commands(commands):
    with open(CONFIG_FILE, "w") as f:
        json.dump(commands, f, indent=4)


class VoiceAssistant:

    def __init__(self):
        # Initialize Text-to-Speech Engine
        self.engine = pyttsx3.init()
        self.engine.setProperty("rate", 175)
        voices = self.engine.getProperty("voices")
        if voices:
            self.engine.setProperty("voice", voices[0].id)

        self.recognizer = sr.Recognizer()
        self.custom_commands = load_custom_commands()

    def speak(self, text):
        """Text-to-speech feedback using pyttsx3."""
        print(f"Assistant: {text}")
        self.engine.say(text)
        self.engine.runAndWait()

    def listen(self, duration=5, sample_rate=16000):
        """Capture microphone input using sounddevice (No PyAudio required)."""
        print("\nListening...")
        try:
            # Record audio using sounddevice
            recording = sd.rec(
                int(duration * sample_rate),
                samplerate=sample_rate,
                channels=1,
                dtype="int16",
            )
            sd.wait()

            # Convert numpy array to AudioData for SpeechRecognition
            raw_bytes = recording.tobytes()
            audio_data = sr.AudioData(raw_bytes, sample_rate, 2)

            print("Recognizing...")
            command = self.recognizer.recognize_google(audio_data)
            print(f"You said: {command}")
            return command.lower()
        except sr.UnknownValueError:
            self.speak("I didn't catch that. Could you please repeat yourself?")
            return ""
        except sr.RequestError:
            self.speak(
                "Speech recognition service is unreachable. Please check your connection."
            )
            return ""
        except Exception as e:
            print(f"Audio Recording Error: {e}")
            return ""

    # ---------------- ADVANCED NLP INTENT PARSER ----------------
    def parse_intent(self, text):
        if not text:
            return "unknown", None

        tokens = word_tokenize(text.lower())
        text_clean = " ".join(tokens)

        for trigger in self.custom_commands:
            if trigger in text_clean:
                return "custom", trigger

        if any(w in tokens for w in ["hello", "hi", "hey", "greetings"]):
            return "greeting", None

        if any(w in text_clean for w in ["time", "date", "clock", "today"]):
            return "time_date", None

        if any(w in tokens for w in ["search", "google", "find", "look"]):
            query = re.sub(
                r"^.*?(search|search for|google|find|look up)\s+",
                "",
                text_clean,
            )
            return "web_search", query

        if "weather" in tokens or "temperature" in tokens:
            match = re.search(r"weather (?:in|for|at)?\s*([a-zA-Z\s]+)", text)
            city = match.group(1).strip() if match else "London"
            return "weather", city

        if "email" in tokens or "mail" in tokens or "send" in tokens:
            return "send_email", None

        if "reminder" in tokens or "remind" in tokens or "timer" in tokens:
            match = re.search(r"(\d+)\s*(second|seconds|minute|minutes)", text)
            if match:
                amount = int(match.group(1))
                unit = match.group(2)
                seconds = amount * 60 if "minute" in unit else amount
                return "set_reminder", seconds
            return "set_reminder", 10

        if "add custom command" in text or "new command" in text:
            return "add_command", None

        if any(w in tokens for w in ["what", "who", "where", "tell"]):
            return "qa", text_clean

        if any(w in tokens for w in ["exit", "stop", "bye", "quit"]):
            return "exit", None

        return "unknown", None

    # ---------------- ACTIONS ----------------
    def get_weather(self, city):
        if WEATHER_API_KEY == "YOUR_OPENWEATHERMAP_API_KEY":
            self.speak(
                f"Please set an OpenWeatherMap API key to check weather for {city}."
            )
            return

        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
        try:
            res = requests.get(url, timeout=5).json()
            if res.get("cod") == 200:
                temp = res["main"]["temp"]
                desc = res["weather"][0]["description"]
                self.speak(
                    f"The weather in {city} is {desc} with {temp} degrees Celsius."
                )
            else:
                self.speak(f"Could not find weather data for {city}.")
        except Exception:
            self.speak("Unable to connect to the weather service.")

    def send_email_action(self):
        self.speak("Who is the recipient email address?")
        recipient = input("Enter recipient email: ")

        self.speak("What is the message content?")
        body = self.listen()

        if not body:
            self.speak("Email cancelled.")
            return

        try:
            msg = MIMEText(body)
            msg["Subject"] = "Voice Assistant Alert"
            msg["From"] = SENDER_EMAIL
            msg["To"] = recipient

            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
            server.quit()
            self.speak("Email sent successfully!")
        except Exception as e:
            self.speak(f"Failed to send email: {e}")

    def set_reminder_thread(self, seconds):
        time.sleep(seconds)
        self.speak("ALERT! Your timed reminder is up!")

    def answer_question(self, query):
        for key, answer in KNOWLEDGE_BASE.items():
            if key in query:
                self.speak(answer)
                return

        self.speak("Searching the web for an answer...")
        webbrowser.open(
            f"https://www.google.com/search?q={urllib.parse.quote(query)}"
        )

    def add_custom_command_action(self):
        self.speak("What phrase would you like to add?")
        trigger = self.listen()
        if not trigger:
            return

        self.speak(f"What should I respond when you say {trigger}?")
        response = self.listen()
        if not response:
            return

        self.custom_commands[trigger] = response
        save_custom_commands(self.custom_commands)
        self.speak(f"Custom command for {trigger} saved.")

    def run(self):
        self.speak("Voice Assistant active. How can I help you?")

        while True:
            text = self.listen()
            if not text:
                continue

            intent, payload = self.parse_intent(text)

            if intent == "greeting":
                self.speak("Hello! How can I assist you today?")

            elif intent == "time_date":
                now = datetime.datetime.now()
                dt_str = now.strftime("%A, %B %d, %Y at %I:%M %p")
                self.speak(f"Current date and time is {dt_str}")

            elif intent == "web_search":
                if payload:
                    self.speak(f"Searching for {payload}")
                    webbrowser.open(
                        f"https://www.google.com/search?q={urllib.parse.quote(payload)}"
                    )

            elif intent == "weather":
                self.get_weather(payload)

            elif intent == "send_email":
                self.send_email_action()

            elif intent == "set_reminder":
                self.speak(f"Setting reminder for {payload} seconds.")
                threading.Thread(
                    target=self.set_reminder_thread,
                    args=(payload,),
                    daemon=True,
                ).start()

            elif intent == "qa":
                self.answer_question(payload)

            elif intent == "custom":
                self.speak(self.custom_commands[payload])

            elif intent == "add_command":
                self.add_custom_command_action()

            elif intent == "exit":
                self.speak("Goodbye!")
                break


if __name__ == "__main__":
    assistant = VoiceAssistant()
    assistant.run()