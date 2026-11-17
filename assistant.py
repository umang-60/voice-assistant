import speech_recognition as sr
import pyttsx3
import os
import webbrowser
import datetime
import time
import logging
import keyboard  # run: pip install keyboard
import keyboard as kb
logging.basicConfig(
    filename="assistant.log",
    level=logging.INFO,
    format="%(asctime)s — %(message)s"
)

# --- Setup ---
r = sr.Recognizer()
with sr.Microphone() as source:
    r.adjust_for_ambient_noise(source, duration=0.5)
r.energy_threshold = 100
r.dynamic_energy_threshold = True
r.pause_threshold = 0.5

WAKE_WORD = "siri"
CONVERSATION_TIMEOUT = 30

YES_WORDS = {"yes", "yeah", "yep", "yas", "yess", "yaas",
             "sure", "confirm", "ok", "okay", "haan", "ha"}

def is_yes(text):
    words = text.replace(",", " ").replace(".", " ").split()
    return any(w in words for w in YES_WORDS)

def speak(text):
    logging.info(f"🤖 {text}")
    try:
        temp_engine = pyttsx3.init('sapi5')
        temp_engine.setProperty("rate", 175)
        
        # Select female voice
        voices = temp_engine.getProperty('voices')
        for voice in voices:
            # Look for keywords in the name to determine female voice (Zira is Windows' built-in female voice)
            if any(k in voice.name.lower() for k in ['zira', 'female', 'woman', 'girl']):
                temp_engine.setProperty('voice', voice.id)
                break
        
        temp_engine.say(text)
        temp_engine.runAndWait()
        del temp_engine
    except Exception as e:
        logging.error(f"TTS error: {e}")
    time.sleep(1.0)

def listen(timeout=5, phrase_time_limit=5):
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source, duration=0.2)
        logging.info("🎤 Listening...")
        try:
            audio = r.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
            data = r.recognize_google(audio, show_all=True)
            if data and data.get('alternative'):
                text = data['alternative'][0]['transcript'].strip().lower()
                if text:
                    logging.info(f"👤 {text}")
                    return text
            logging.info("👤 (empty result)")
            return ""
        except sr.WaitTimeoutError:
            logging.info("⏱️ no speech detected")
            return ""
        except sr.UnknownValueError:
            logging.info("❓ could not understand")
            return ""
        except sr.RequestError:
            speak("Sorry, my speech service is down.")
            return ""

def confirm_shutdown():
    """Voice confirmation with keyboard fallback. Returns True to confirm."""
    speak("Are you sure you want to shut down? Say yes, or press Y to confirm. Press N to cancel.")
    time.sleep(1.5)

    # Voice window first
    spoken = listen(timeout=4, phrase_time_limit=3)
    logging.info(f"DEBUG confirm = {repr(spoken)}")
    if is_yes(spoken):
        return True
    if any(w in spoken for w in ["no", "cancel", "nope"]):
        return False

    # Keyboard fallback
    logging.info("⌨️ waiting for Y/N key...")
    start = time.time()
    while time.time() - start < 6:
        if keyboard.is_pressed('y'):
            logging.info("⌨️ Y pressed -> confirm")
            return True
        if keyboard.is_pressed('n'):
            logging.info("⌨️ N pressed -> cancel")
            return False
        time.sleep(0.1)

    logging.info("⌨️ no key pressed -> cancel")
    return False

def wait_for_wake_word():
    while True:
        text = listen(timeout=5)
        if WAKE_WORD in text:
            speak("Yes? I'm listening.")
            return True
        logging.info(f"🔍 wake check, text={repr(text)}")
        if any(w in text for w in ["stop", "exit", "quit", "goodbye"]):
            speak("Goodbye!")
            return "STOP"

def handle_command(command):
    if "hello" in command:
        speak("Hello! How can I help you?")
    elif "time" in command:
        speak("The time is " + datetime.datetime.now().strftime("%I:%M %p"))
    elif "date" in command:
        speak("Today is " + datetime.datetime.now().strftime("%A, %d %B %Y"))
    elif "cancel" in command:
        os.system("shutdown /a")
        speak("Shutdown cancelled.")
    elif "sleep" in command or "stop listening" in command:
        speak("Going to sleep. Say siri to wake me.")
        return "SLEEP"
    elif "stop" in command or "exit" in command or "quit" in command:
        speak("Goodbye!")
        return "EXIT"
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
        if confirm_shutdown():
            speak("Shutting down in 10 seconds. Say cancel to abort.")
            os.system("shutdown /s /t 10")
            time.sleep(1.0)
            cancel_cmd = listen(timeout=8)
            if "cancel" in cancel_cmd:
                os.system("shutdown /a")
                speak("Shutdown cancelled.")
            else:
                speak("Shutting down now.")
        else:
            speak("Shutdown cancelled.")
    elif "volume up" in command:
        for _ in range(5):
            kb.send('volume up')
        speak("Volume increased.")

    elif "volume down" in command:
        for _ in range(5):
            kb.send('volume down')
        speak("Volume decreased.")

    elif "mute" in command:
        kb.send('volume mute')
        speak("Muted.")

    elif "screenshot" in command:
        import pyautogui
        path = os.path.join(os.path.expanduser("~"), "Pictures", f"screenshot_{int(time.time())}.png")
        pyautogui.screenshot(path)
        speak("Screenshot saved.")

    elif "battery" in command:
        import psutil
        b = psutil.sensors_battery()
        speak(f"Battery is at {int(b.percent)} percent.")
    else:
        speak("I heard you say: " + command)
    return "OK"

# --- Main loop ---
speak("Assistant ready. Say siri to wake me.")

try:
    while True:
        wake = wait_for_wake_word()
        if wake == "STOP":
            break

        last_activity = time.time()
        while time.time() - last_activity < CONVERSATION_TIMEOUT:
            command = listen(timeout=5)
            if not command:
                if time.time() - last_activity >= CONVERSATION_TIMEOUT:
                    speak("Going back to sleep. Say siri to wake me.")
                    break
                continue
            last_activity = time.time()
            result = handle_command(command)
            if result == "EXIT":
                raise KeyboardInterrupt
            if result == "SLEEP":
                break

except KeyboardInterrupt:
    speak("Goodbye!")
    print("\n👋 Exited cleanly.")