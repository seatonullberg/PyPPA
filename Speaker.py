# TODO: Implement Tacotron voice synthesis!
import pyttsx3
from gtts import gTTS
from pydub import AudioSegment
from pyaudio import PyAudio
import wave
import os

'''
def vocalize(input_string):
    engine = pyttsx3.init()
    engine.setProperty('rate', 140)
    engine.setProperty('voice', 'english-north')
    engine.say(str(input_string))
    engine.runAndWait()
    engine.stop()
'''


def vocalize(input_string):
    tts = gTTS(text=input_string, lang='en-us', slow=False)
    tts.save('tempVocal.mp3')
    mp3 = AudioSegment.from_mp3('tempVocal.mp3')
    mp3.export('tempVocal.wav', format='wav')
    p = PyAudio()
    with wave.open('tempVocal.wav', 'rb') as wav:
        wav_data = wav.readframes(wav.getnframes())
        stream = p.open(format=p.get_format_from_width(wav.getsampwidth()),
                        channels=wav.getnchannels(),
                        rate=wav.getframerate(),
                        input=False,
                        output=True)
        stream.start_stream()
        stream.write(wav_data)
        stream.stop_stream()
        stream.close()
    os.remove('tempVocal.mp3')
    os.remove('tempVocal.wav')
    p.terminate()
