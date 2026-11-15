import speech_recognition as sr

r = sr.Recognizer()

with sr.Microphone() as source:
    print("Adjusting for background noise... please stay quiet 1 sec")
    r.adjust_for_ambient_noise(source, duration=1)
    print("🎤 Speak now!")
    audio = r.listen(source)

try:
    text = r.recognize_google(audio)
    print("You said:", text)
except sr.UnknownValueError:
    print("Could not understand audio")
except sr.RequestError as e:
    print("API error:", e)