import speech_recognition as sr
import pyttsx3
import os
import webbrowser
import datetime
import time
import logging
import keyboard as kb
import requests
import random 
import vosk
import json
import asyncio
import edge_tts
import os


def ask_ollama(prompt):
    logging.info(f"🧠 Asking Ollama Local: {prompt}")
    try:
        url = "http://127.0.0.1:11434/api/generate"
        payload = {
            "model": "llama3.2",
            "prompt": prompt,
            "stream": False
        }
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        
        data = response.json()
        answer = data.get("response", "").strip()
        return answer if answer else "I couldn't think of an answer."
        
    except Exception as e:
        logging.error(f"Ollama Cloud Error: {e}")
        return "Sorry, my cloud brain seems to be offline."
CURRENT_LANG = "en-IN"   # "en-IN" for English, "hi-IN" for Hindi
HINDI_MODE = False        # ← new flag
logging.basicConfig(
    filename="assistant.log",
    level=logging.INFO,
    format="%(asctime)s — %(message)s"
)
try:
    vosk_model_hi = vosk.Model("C:/voice-assistant/models/vosk-model-hi-0.22")
    logging.info("✅ Vosk Hindi model loaded")
except Exception as e:
    logging.error(f"❌ Vosk model failed to load: {e}")
    vosk_model_hi = None
# --- Chat personality ---
CHAT_SYSTEM_PROMPT = (
    "You are Siri, a friendly, witty, and warm female personal assistant. "
    "You talk like a real girl in her 20s—casual, natural, and playful. "
    "Use contractions (I'm, you're, let's). Keep replies SHORT (1-2 sentences) because they are spoken aloud. "
    "Never say you are an AI or a language model. Never break character. "
    "If the user seems sad, be comforting. If they joke, play along. "
    "Ask a follow-up question only when it feels natural, not every time."
)

chat_history = []   # list of {"role": "user"/"assistant", "content": "..."}

def chat_with_siri(user_message):
    global chat_history, CURRENT_LANG, HINDI_MODE
    chat_history.append({"role": "user", "content": user_message})
    chat_history = chat_history[-12:]

    if HINDI_MODE:
        lang_instruction = "Reply in Hindi..."
    else:
        lang_instruction = "Reply in English. Keep replies short (1-3 sentences). "

    prompt = CHAT_SYSTEM_PROMPT + "\n\n" + lang_instruction + "\n"
    for msg in chat_history:
        if msg["role"] == "user":
            prompt += f"User: {msg['content']}\n"
        else:
            prompt += f"Siri: {msg['content']}\n"
    prompt += "Siri:"

    logging.info(f"💬 Chat prompt sent ({len(chat_history)} msgs, lang={CURRENT_LANG})")
    try:
        resp = requests.post(
            "http://127.0.0.1:11434/api/generate",
            json={"model": "llama3.2", "prompt": prompt, "stream": False},
            timeout=60
        )
        resp.raise_for_status()
        reply = resp.json().get("response", "").strip()
        chat_history.append({"role": "assistant", "content": reply})
        return reply if reply else "Hmm, I lost my train of thought."
    except Exception as e:
        logging.error(f"Chat error: {e}")
        return "Sorry, my brain glitched for a second. Say that again?"
    
    
# --- Setup ---
r = sr.Recognizer()
with sr.Microphone() as source:
    r.adjust_for_ambient_noise(source, duration=0.5)
r.energy_threshold = 100
r.dynamic_energy_threshold = True
r.pause_threshold = 0.5

WAKE_WORDS = ["siri", "सिरी", "सिरि", "शिरी", "seeree", "siri"]
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
APPS = {
    "calculator":   "calc",
    "paint":        "mspaint",
    "word":         "winword",
    "excel":        "excel",
    "powerpoint":   "powerpnt",
    "task manager": "taskmgr",
    "control panel": "control",
    "settings":     "ms-settings:",
    "cmd":          "cmd",
    "terminal":     "wt",
    "vscode":       "code",
    "spotify":      "spotify",
}
YES_WORDS = {"yes", "yeah", "yep", "yas", "yess", "yaas",
             "sure", "confirm", "ok", "okay", "haan", "ha"}

def is_yes(text):
    words = text.replace(",", " ").replace(".", " ").split()
    return any(w in words for w in YES_WORDS)

import win32com.client

_sapi = win32com.client.Dispatch("SAPI.SpVoice")
_sapi.Volume = 100         
_sapi.Rate = 0              

_voices = _sapi.GetVoices()
for i in range(_voices.Count):
    logging.info(f"🎙️ Voice {i}: {_voices.Item(i).GetDescription()}")
for i in range(_voices.Count):
    desc = _voices.Item(i).GetDescription().lower()
    if "zira" in desc or "female" in desc:
        _sapi.Voice = _voices.Item(i)
        logging.info(f"🗣️ Using SAPI voice: {_voices.Item(i).GetDescription()}")
        break

# Put this near your other setup code, at the top
import io
from pygame import mixer
mixer.init()
def speak(text):
    logging.info(f"🤖 {text}")
    
    if HINDI_MODE:
        voice = "hi-IN-SwaraNeural"
        
        async def _collect_tts():
            communicate = edge_tts.Communicate(text, voice)
            audio_buffer = io.BytesIO()
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_buffer.write(chunk["data"])
            audio_buffer.seek(0)
            return audio_buffer
        
        try:
            audio_buffer = asyncio.run(_collect_tts())
        except Exception as e:
            logging.error(f"Edge TTS collect error: {e}")
            try:
                _sapi.Speak(text)
            except:
                pass
            time.sleep(0.5)
            return
        
        try:
            mixer.music.load(audio_buffer)
            mixer.music.play()
            while mixer.music.get_busy():
                time.sleep(0.1)
            mixer.music.unload()
        except Exception as e:
            logging.error(f"pygame playback error: {e}")
            try:
                _sapi.Speak(text)
            except:
                pass
    else:
        try:
            _sapi.Speak(text)
        except Exception as e:
            logging.error(f"TTS error: {e}")
    
    time.sleep(0.5)  

def listen(timeout=5, phrase_time_limit=5):
    global CURRENT_LANG
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source, duration=0.2)
        logging.info(f"🎤 Listening... (lang={CURRENT_LANG})")
        try:
            audio = r.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)

            if CURRENT_LANG == "hi-IN" and vosk_model_hi is not None:
                raw_data = audio.get_raw_data(convert_rate=16000, convert_width=2)
                rec = vosk.KaldiRecognizer(vosk_model_hi, 16000)
                chunk_size = 4000
                for i in range(0, len(raw_data), chunk_size):
                    rec.AcceptWaveform(raw_data[i:i+chunk_size])
                result = json.loads(rec.FinalResult())
                text = result.get("text", "").strip().lower()
                if text:
                    logging.info(f"👤 {text}")
                    return text
                logging.info("👤 (Vosk empty result)")
                return ""
            else:
                # English → Google
                data = r.recognize_google(audio, language=CURRENT_LANG, show_all=True)
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
    global CURRENT_LANG, HINDI_MODE
    while True:
        text = listen(timeout=5)
        if any(w in text for w in WAKE_WORDS):
            if HINDI_MODE:
                speak("हाँ, मैं सुन रही हूँ।")
            else:
                speak("Yes? I'm listening.")
            return True
        logging.info(f"🔍 wake check, text={repr(text)}")
        # stop/exit in both languages
        if any(w in text for w in ["stop", "exit", "quit", "goodbye",
                                    "रुको", "बंद", "अलविदा", "बाय"]):
            if CURRENT_LANG == "hi-IN":
                speak("अलविदा!")
            else:
                speak("Goodbye!")
            return "STOP"   

def handle_command(command):
    global CURRENT_LANG,HINDI_MODE
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
    elif "stop" in command or "exit" in command or "quit" in command or "bye" in command:
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
        
        jokes = [
            "Why do programmers prefer dark mode? Because light attracts bugs.",
            "Why did the Python developer go broke? Because he used up all his cache.",
            "There are 10 types of people: those who understand binary and those who don't.",
            "A SQL query walks into a bar, walks up to two tables and asks: Can I join you?",
            "Why do Java developers wear glasses? Because they don't C sharp.",
            "I told my computer I needed a break, and it said: No problem, I'll go to sleep.",
            "Why was the developer unhappy at their job? They wanted arrays.",
            "How many programmers does it take to change a light bulb? None — it's a hardware problem.",
            "Debugging: being the detective in a crime movie where you are also the murderer.",
        ]
        speak(random.choice(jokes))
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
    elif "ask ai" in command or "think about" in command:
        # Extract the actual question from the command
        query = command.replace("ask ai", "").replace("think about", "").strip()
        if query:
            speak("Let me think...")
            ai_answer = ask_ollama(query)
            speak(ai_answer)
        else:
            speak("What should I ask the AI?")
    elif any(word in command for word in ["open", "launch", "start"]) and any(app in command for app in APPS):
        matched = next((a for a in APPS if a in command), None)
        if matched:
            speak(f"Opening {matched}")
            os.system(f"start {APPS[matched]}")
    elif "youtube search" in command:
        query = command.replace("youtube search", "").strip()
        if query:
            speak(f"Searching YouTube for {query}")
            webbrowser.open("https://www.youtube.com/results?search_query=" + query.replace(" ", "+"))
        else:
            speak("What should I search on YouTube?")
    elif "translate" in command:
        speak("What should I translate?")
        text = listen(timeout=6)
        if text:
            speak("To which language? Say hindi, spanish, french, etc.")
            lang = listen(timeout=5)
            lang_map = {"hindi": "hi", "spanish": "es", "french": "fr",
                        "german": "de", "japanese": "ja", "chinese": "zh"}
            code = lang_map.get(lang, "en")
            try:
                r = requests.get(
                    "https://api.mymemory.translated.net/get",
                    params={"q": text, "langpair": f"en|{code}"},
                    timeout=5
                )
                translated = r.json()["responseData"]["translatedText"]
                speak(translated)
            except Exception as e:
                logging.error(f"Translate error: {e}")
                speak("Translation failed.")
    elif "currency" in command or "convert" in command:
        speak("Say something like: convert 100 usd to inr")
        text = listen(timeout=6)
        import re
        m = re.search(r'(\d+)\s*([a-z]{3})\s*to\s*([a-z]{3})', text)
        if m:
            amount, frm, to = m.group(1), m.group(2).upper(), m.group(3).upper()
            try:
                r = requests.get(f"https://api.exchangerate-api.com/v4/latest/{frm}", timeout=5)
                rate = r.json()["rates"].get(to)
                if rate:
                    speak(f"{amount} {frm} is {float(amount) * rate:.2f} {to}.")
                else:
                    speak("Currency not found.")
            except Exception as e:
                logging.error(f"Currency error: {e}")
                speak("Conversion failed.")
        else:
            speak("I didn't catch the amount and currencies.")
    elif "spell" in command:
        word = command.replace("spell", "").strip()
        if word:
            speak(" ".join(word))
        else:
            speak("What should I spell?")
    elif "flip a coin" in command or "toss a coin" in command:
        
        speak(random.choice(["Heads", "Tails"]))

    elif "roll a dice" in command or "roll a die" in command:
        
        speak(f"You rolled a {random.randint(1, 6)}.")
    elif "random number" in command:
        import re
        m = re.search(r'between\s*(\d+)\s*and\s*(\d+)', command)
        if m:
            a, b = int(m.group(1)), int(m.group(2))
            speak(f"Your random number is {random.randint(a, b)}.")
        else:
            speak(f"Your random number is {random.randint(1, 100)}.")
    elif "day" in command and "what" in command:
        speak("Today is " + datetime.datetime.now().strftime("%A") + ".")

    elif "week number" in command:
        speak(f"We are in week {datetime.datetime.now().isocalendar()[1]} of the year.")
    elif "sleep timer" in command or "shutdown timer" in command:
        import re
        m = re.search(r'(\d+)\s*(minute|min)', command)
        if m:
            mins = int(m.group(1))
            speak(f"PC will shut down in {mins} minutes.")
            os.system(f"shutdown /s /t {mins * 60}")
        else:
            speak("Say something like: sleep timer 30 minutes.")
    elif "cancel shutdown timer" in command or "cancel timer" in command:
        os.system("shutdown /a")
        speak("Timer cancelled.")
    elif "internet speed" in command or "speed test" in command:
        speak("Testing your internet speed, please wait.")
        try:
            import speedtest
            st = speedtest.Speedtest()
            st.get_best_server()
            down = st.download() / 1_000_000
            up = st.upload() / 1_000_000
            speak(f"Download {down:.1f} Mbps, upload {up:.1f} Mbps.")
        except Exception as e:
            logging.error(f"Speedtest error: {e}")
            speak("Speed test failed.")
    elif "ip address" in command or "my ip" in command:
        try:
            r = requests.get("https://api.ipify.org?format=json", timeout=5)
            speak("Your public IP is " + r.json()["ip"])
        except Exception as e:
            logging.error(f"IP error: {e}")
            speak("Couldn't fetch IP.")
    elif "clean temp" in command or "clear temp" in command:
        speak("Cleaning temp folder.")
        os.system('del /q /f /s %TEMP%\\* >nul 2>&1')
        speak("Temp folder cleaned.")
    elif "remind me" in command:
        import re
        m = re.search(r'remind me to (.+?) (?:in|after) (\d+)\s*(second|minute|hour)', command)
        if m:
            task = m.group(1)
            amount = int(m.group(2))
            unit = m.group(3)
            seconds = amount * {"second": 1, "minute": 60, "hour": 3600}[unit]
            speak(f"Okay, I'll remind you to {task} in {amount} {unit}s.")
            time.sleep(seconds)
            speak(f"Reminder: {task}")
        else:
            speak("Say something like: remind me to drink water in 10 minutes.")
    elif ("let's talk" in command or "chat with me" in command or "talk to me" in command
          or "बात करो" in command or "बात करें" in command or "चैट करो" in command):
        if HINDI_MODE:
                speak(random.choice([
                "ज़रूर! क्या बात करें?",
                "मुझे बात करना अच्छा लगेगा! आपका दिन कैसा रहा?",
                "हाँ, मैं सुन रही हूँ। क्या बात करनी है?",
            ]))
        else:
            speak(random.choice([
            "Sure! What's on your mind?",
            "I'd love to chat! How's your day going?",
            "Hey, I'm all ears. What do you wanna talk about?",
            ]))
        # Enter chat loop
        while True:
            user_msg = listen(timeout=10, phrase_time_limit=8)
            if not user_msg:
                continue
            if any(w in user_msg for w in ["stop chatting", "stop chat", "end chat", "that's all", "bye"]):
                speak(random.choice([
                    "Aww, okay! Talk to you later.",
                    "Alright, I'll be here whenever you want to chat again.",
                    "Bye for now — this was fun!",
                ]))
                break
            reply = chat_with_siri(user_msg)
            speak(reply)
        return "OK"
    elif "hindi" in command or "हिंदी" in command:
        HINDI_MODE = True
        CURRENT_LANG = "hi-IN"   # ← actual Hindi recognition
        speak("ठीक है, अब मैं हिंदी में बात करूँगी।")
        # switch TTS voice to Hindi
        for i in range(_voices.Count):
            desc = _voices.Item(i).GetDescription().lower()
            if "hindi" in desc or "hemant" in desc or "kalpana" in desc:
                _sapi.Voice = _voices.Item(i)
                logging.info(f"🗣️ Switched to Hindi voice: {_voices.Item(i).GetDescription()}")
                break
        return "OK"

    elif "english" in command or "अंग्रेज़ी" in command:
        HINDI_MODE = False
        CURRENT_LANG = "en-IN"
        speak("Okay, switching back to English.")
        for i in range(_voices.Count):
            desc = _voices.Item(i).GetDescription().lower()
            if "zira" in desc or "female" in desc:
                _sapi.Voice = _voices.Item(i)
                logging.info(f"🗣️ Switched to English voice: {_voices.Item(i).GetDescription()}")
                break
        return "OK"
    else:
        # Casual remark → let Siri reply naturally
        reply = chat_with_siri(command)
        speak(reply)

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