import speech_recognition as sr
import pyttsx3
import os
import webbrowser
import datetime
import time

# --- Setup ---
r = sr.Recognizer()
r.energy_threshold = 300
r.dynamic_energy_threshold = True

engine = pyttsx3.init()
engine.setProperty("rate", 175)

YES_WORDS = {"yes", "yeah", "yep", "yas", "yess", "yaas",
             "sure", "confirm", "ok", "okay", "haan", "ha"}

def is_yes(text):
    words = text.replace(",", " ").replace(".", " ").split()
    return any(w in YES_WORDS for w in words)

def speak(text):
    print("🤖", text)
    engine.say(text)
    engine.runAndWait()
    time.sleep(0.8)

def listen(timeout=5):
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source, duration=0.2)
        print("🎤 Listening...")
        try:
            audio = r.listen(source, timeout=timeout, phrase_time_limit=8)
            text = r.recognize_google(audio).lower()
            print("👤 You said:", text)
            return text
        except sr.WaitTimeoutError:
            print("⏱️  no speech detected")
            return ""
        except sr.UnknownValueError:
            print("❓ could not understand")
            return ""
        except sr.RequestError:
            speak("Sorry, my speech service is down.")
            return ""

# --- Main loop ---
speak("Assistant is ready. Say something.")

try:
    while True:
        command = listen()
        if not command:
            continue

        if "hello" in command:
            speak("Hello! How can I help you?")
        elif "time" in command:
            speak("The time is " + datetime.datetime.now().strftime("%I:%M %p"))
        elif "date" in command:
            speak("Today is " + datetime.datetime.now().strftime("%A, %d %B %Y"))
        elif "cancel" in command:
            os.system("shutdown /a")
            speak("Shutdown cancelled.")
        elif "stop" in command or "exit" in command or "quit" in command:
            speak("Goodbye!")
            break
        elif "open chrome" in command:
            speak("Opening Chrome")
            os.system("start chrome")
        elif "open notepad" in command:
            speak("Opening Notepad")
            os.system("start notepad")
        elif "search" in command:
            query = command.replace("search", "").strip()
            if query:
                speak("Searching for " + query)
                webbrowser.open("https://www.google.com/search?q=" + query)
            else:
                speak("What should I search for?")
        elif "shut down" in command or "shutdown" in command:
            speak("Are you sure you want to shut down? Say yes to confirm.")
            confirm = listen(timeout=8)
            print("DEBUG confirm =", repr(confirm))

            if not is_yes(confirm):
                speak("I didn't catch that. Please say yes or no.")
                confirm = listen(timeout=8)
                print("DEBUG confirm (retry) =", repr(confirm))

            if is_yes(confirm):
                speak("Shutting down in 10 seconds. Say cancel to abort.")
                os.system("shutdown /s /t 10")
                cancel_cmd = listen(timeout=8)
                if "cancel" in cancel_cmd:
                    os.system("shutdown /a")
                    speak("Shutdown cancelled.")
                else:
                    speak("Shutting down now.")
            else:
                speak("Shutdown cancelled.")
        else:
            speak("I heard you say: " + command)

except KeyboardInterrupt:
    speak("Goodbye!")
    print("\n👋 Exited cleanly.")