# TODO: Implement Tacotron voice synthesis!
# import pyttsx3
from gtts import gTTS
from pydub import AudioSegment
from pyaudio import PyAudio
import wave
import os
import time

'''
def vocalize(input_string):
    engine = pyttsx3.init()
    engine.setProperty('rate', 140)
    engine.setProperty('voice', 'english-north')
    engine.say(str(input_string))
    engine.runAndWait()
    engine.stop()
'''


class Speaker(object):

    def __init__(self):
        pass

    def mainloop(self):
        vocalize_path = [os.getcwd(), 'tmp', 'vocalize.txt']
        vocalize_path = os.path.join('', *vocalize_path)
        while True:
            if os.path.isfile(vocalize_path):
                # the file exists before its contents are ready
                time.sleep(0.1)
                with open(vocalize_path, 'r') as f:
                    text = f.read()
                self.vocalize(text)
                os.remove(vocalize_path)
            else:
                # no vocalization requested
                continue

    def vocalize(self, input_string):
        tts = gTTS(text=input_string,
                   lang='en',
                   slow=False,
                   lang_check=False)
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



