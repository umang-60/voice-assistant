import pyttsx3

engine = pyttsx3.init()
engine.setProperty("rate", 175)   # speed (default ~200)
engine.say("Hello, I am your assistant. I can speak now.")
engine.runAndWait()