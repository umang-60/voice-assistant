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
WEBSITES = {
    "youtube":   "https://www.youtube.com",
    "gmail":     "https://mail.google.com",
    "github":    "https://github.com",
    "whatsapp":  "https://web.whatsapp.com",
    "instagram": "https://www.instagram.com",
    "facebook":  "https://www.facebook.com",
    "twitter":   "https://twitter.com",
    "reddit":    "https://www.reddit.com",
    "stackoverflow": "https://stackoverflow.com",
    "chatgpt":   "https://chat.openai.com",
    "google":    "https://www.google.com",
    "maps":      "https://maps.google.com",
    "netflix":   "https://www.netflix.com",
    "spotify":   "https://open.spotify.com",
    "linkedin":  "https://www.linkedin.com",
}
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
    """Confirmation by repeating the word 'shutdown'. Returns True to confirm."""
    speak("Say shutdown again to confirm, or say cancel to abort.")
    time.sleep(1.5)

    spoken = listen(timeout=6, phrase_time_limit=4)
    logging.info(f"DEBUG confirm = {repr(spoken)}")

    # Confirm if "shutdown" / "shut down" is heard
    if "shutdown" in spoken or "shut down" in spoken:
        return True

    # Explicit cancel
    if any(w in spoken for w in ["cancel", "no", "stop", "abort", "nope"]):
        return False

    # Nothing heard or unclear → treat as cancel (safe default)
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
    elif "restart" in command or "reboot" in command:
            if confirm_shutdown():
                speak("Restarting in 10 seconds.")
                os.system("shutdown /r /t 10")
            else:
                speak("Restart cancelled.")
    
    elif "sleep pc" in command or "sleep computer" in command:
            if confirm_shutdown():
                speak("Putting PC to sleep.")
                os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
            else:
                speak("Sleep cancelled.")
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
            if any(w in cancel_cmd for w in ["cancel", "stop", "no", "abort"]):
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
    elif "play" in command and "youtube" in command:
        query = command.replace("play", "").replace("on youtube", "").replace("youtube", "").strip()
        if query:
            speak("Playing " + query + " on YouTube")
            webbrowser.open("https://www.youtube.com/results?search_query=" + query.replace(" ", "+"))
        else:
            speak("What should I play?")
    elif "weather" in command:
        import requests
        try:
            city = "auto"  # uses your IP location; or replace with "London" etc.
            r = requests.get(f"https://wttr.in/{city}?format=%C+%t", timeout=5)
            speak("The weather is " + r.text.strip())
        except Exception as e:
            logging.error(f"Weather error: {e}")
            speak("Sorry, I couldn't fetch the weather.")
    elif "lock" in command and ("pc" in command or "computer" in command or "screen" in command):
        speak("Locking your PC")
        os.system("rundll32.exe user32.dll,LockWorkStation")
    elif "empty recycle bin" in command or "clear recycle bin" in command:
        speak("Emptying recycle bin")
        os.system('PowerShell -Command "Clear-RecycleBin -Force"')
    elif "brightness up" in command:
        import screen_brightness_control as sbc
        current = sbc.get_brightness()[0]
        sbc.set_brightness(min(100, current + 20))
        speak("Brightness increased.")

    elif "brightness down" in command:
        import screen_brightness_control as sbc
        current = sbc.get_brightness()[0]
        sbc.set_brightness(max(0, current - 20))
        speak("Brightness decreased.")
    elif "what can you do" in command or "help" in command:
        speak("I can open websites, play music on YouTube, tell you the weather, "
              "lock your PC, empty the recycle bin, change brightness, tell jokes, "
              "take screenshots, check battery, control volume, and shut down your PC.")
    elif any(word in command for word in ["open", "launch", "go to"]) and any(site in command for site in WEBSITES):
        # Find which site the user mentioned
        matched = next((s for s in WEBSITES if s in command), None)
        if matched:
            # Vary the spoken response
            import random
            openers = [
                f"Opening {matched} for you.",
                f"Here's {matched}.",
                f"Launching {matched}.",
                f"On it — opening {matched}.",
                f"{matched} coming right up.",
            ]
            speak(random.choice(openers))
            webbrowser.open(WEBSITES[matched])
    elif "joke" in command:
        import requests
        try:
            # Free joke API — returns a random joke
            r = requests.get(
                "https://official-joke-api.appspot.com/random_joke",
                timeout=5
            )
            data = r.json()
            setup = data.get("setup", "")
            punchline = data.get("punchline", "")
            if setup and punchline:
                speak(setup)
                time.sleep(1.5)   # dramatic pause
                speak(punchline)
            else:
                speak("I couldn't find a good joke right now.")
        except Exception as e:
            logging.error(f"Joke API error: {e}")
            # Fallback: local jokes if API fails
            import random
            fallback_jokes = [
                "Why do programmers prefer dark mode? Because light attracts bugs.",
                "Why did the Python developer go broke? Because he used up all his cache.",
                "There are 10 types of people: those who understand binary and those who don't.",
                "A SQL query walks into a bar, walks up to two tables and asks: Can I join you?",
                "Why do Java developers wear glasses? Because they don't C sharp.",
            ]
            speak(random.choice(fallback_jokes))
    elif "play song" in command:
        query = command.replace("play song", "").replace("on youtube", "").strip()
        if query:
            speak(f"Playing {query} on YouTube")
            import pywhatkit
            pywhatkit.playonyt(query)
        else:
            speak("Which song should I play?")
    elif "send whatsapp" in command or "whatsapp message" in command:
        speak("Who should I message? Say the phone number with country code.")
        number = listen(timeout=8).replace(" ", "").replace("plus", "+")
        if number:
            speak("What should I say?")
            message = listen(timeout=8)
            if message:
                speak("Sending now.")
                import pywhatkit
                try:
                    pywhatkit.sendwhatmsg_instantly(number, message, wait_time=15)
                    speak("Message sent.")
                except Exception as e:
                    logging.error(f"WhatsApp error: {e}")
                    speak("Sorry, I couldn't send the message.")
            else:
                speak("Message cancelled.")
        else:
            speak("Number not recognized.")
    elif "news" in command:
        import requests
        try:
            r = requests.get(
                "https://newsapi.org/v2/top-headlines?country=in&pageSize=3&apiKey=8291d24813544c4291f3f260831d4129",
                timeout=5
            )
            articles = r.json().get("articles", [])
            if articles:
                speak("Here are the top headlines.")
                for a in articles[:3]:
                    speak(a["title"])
            else:
                speak("No news found right now.")
        except Exception as e:
            logging.error(f"News error: {e}")
            speak("Sorry, I couldn't fetch the news.")
    elif "wikipedia" in command or "who is" in command or "what is" in command:
        query = command.replace("wikipedia", "").replace("who is", "").replace("what is", "").strip()
        if query:
            import wikipedia
            try:
                summary = wikipedia.summary(query, sentences=2)
                speak(summary)
            except Exception as e:
                logging.error(f"Wikipedia error: {e}")
                speak("I couldn't find that on Wikipedia.")
        else:
            speak("What should I look up?")
    elif "set timer" in command or "set alarm" in command:
        import re
        match = re.search(r'(\d+)\s*(second|minute|hour)', command)
        if match:
            amount = int(match.group(1))
            unit = match.group(2)
            seconds = amount * {"second": 1, "minute": 60, "hour": 3600}[unit]
            speak(f"Timer set for {amount} {unit}s.")
            time.sleep(seconds)
            speak("Time's up!")
        else:
            speak("Say something like: set timer for 5 minutes.")
    elif "open folder" in command:
        speak("Which folder? Say downloads, documents, pictures, or desktop.")
        folder = listen(timeout=6)
        paths = {
            "downloads": os.path.join(os.path.expanduser("~"), "Downloads"),
            "documents": os.path.join(os.path.expanduser("~"), "Documents"),
            "pictures":  os.path.join(os.path.expanduser("~"), "Pictures"),
            "desktop":   os.path.join(os.path.expanduser("~"), "Desktop"),
        }
        if folder in paths:
            os.startfile(paths[folder])
            speak(f"Opening {folder}.")
        else:
            speak("I don't know that folder.")
    elif "type" in command:
        text = command.replace("type", "").strip()
        if text:
            speak(f"Typing: {text}")
            time.sleep(1)
            kb.write(text, delay=0.05)
        else:
            speak("What should I type?")
    elif "copy to clipboard" in command:
        speak("What should I copy?")
        text = listen(timeout=8)
        if text:
            import pyperclip
            pyperclip.copy(text)
            speak("Copied to clipboard.")
        else:
            speak("Nothing to copy.")
    elif "system info" in command or "cpu" in command or "ram" in command:
        import psutil
        cpu = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory().percent
        disk = psutil.disk_usage("/").percent
        speak(f"CPU at {cpu} percent, RAM at {ram} percent, disk at {disk} percent.")
    elif "password" in command and ("generate" in command or "make" in command or "random" in command):
        import secrets, string
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        pwd = "".join(secrets.choice(alphabet) for _ in range(16))
        speak(f"Here's your password: {pwd}")
        import pyperclip
        pyperclip.copy(pwd)
        speak("Also copied to clipboard.")
    elif "google" in command and "search" not in command:
        query = command.replace("google", "").strip()
        if query:
            speak(f"Searching Google for {query}")
            from googlesearch import search
            try:
                results = list(search(query, num_results=3))
                if results:
                    speak("Top result: " + results[0])
                    webbrowser.open(results[0])
                else:
                    speak("No results found.")
            except Exception as e:
                logging.error(f"Google search error: {e}")
                speak("Search failed.")
        else:
            speak("What should I search?")
    elif "pause" in command or "play music" in command or "resume" in command:
        kb.send('play/pause media')
        speak("Done.")

    elif "next song" in command or "next track" in command:
        kb.send('next track')
        speak("Next track.")

    elif "previous song" in command or "previous track" in command:
        kb.send('previous track')
        speak("Previous track.")
    elif "close window" in command or "close this" in command:
        kb.send('alt+f4')
        speak("Window closed.")
    elif "show desktop" in command or "minimize all" in command:
        kb.send('win+d')
        speak("Showing desktop.")
    elif "take photo" in command or "take picture" in command or "webcam" in command:
        import cv2
        speak("Taking a photo.")
        cam = cv2.VideoCapture(0)
        ret, frame = cam.read()
        if ret:
            path = os.path.join(os.path.expanduser("~"), "Pictures", f"photo_{int(time.time())}.jpg")
            cv2.imwrite(path, frame)
            speak("Photo saved to Pictures.")
        else:
            speak("Camera not available.")
        cam.release()
    elif "read clipboard" in command or "what's in clipboard" in command:
        import pyperclip
        content = pyperclip.paste()
        if content:
            speak("Clipboard says: " + content[:300])
        else:
            speak("Clipboard is empty.")
    elif "countdown" in command:
        import re
        match = re.search(r'(\d+)', command)
        if match:
            n = int(match.group(1))
            for i in range(n, 0, -1):
                speak(str(i))
                time.sleep(1)
            speak("Go!")
        else:
            speak("Say something like: countdown 5.")
    elif "motivate" in command or "motivation" in command or "quote" in command:
        import requests
        try:
            r = requests.get("https://zenquotes.io/api/random", timeout=5)
            data = r.json()
            if data:
                speak(data[0]["q"] + " — " + data[0]["a"])
            else:
                speak("Stay positive and keep going.")
        except Exception as e:
            logging.error(f"Quote error: {e}")
            speak("Stay positive and keep going.")
    elif "programming joke" in command or "coding joke" in command:
        import requests
        try:
            r = requests.get(
                "https://official-joke-api.appspot.com/jokes/programming/random",
                timeout=5
            )
            data = r.json()[0]
            speak(data["setup"])
            time.sleep(1.5)
            speak(data["punchline"])
        except Exception as e:
            logging.error(f"Prog joke error: {e}")
            speak("Why do programmers prefer dark mode? Because light attracts bugs.")
    
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