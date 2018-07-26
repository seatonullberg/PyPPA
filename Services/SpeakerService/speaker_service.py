from base_service import BaseService
from gtts import gTTS
from pydub import AudioSegment
from pyaudio import PyAudio
import wave
import os


class SpeakerService(BaseService):
    # there is no default behavior and no output file
    # output is through the speakers

    # TODO: figure out new naming scheme for the service files
    def __init__(self):
        self.name = 'SpeakerService'
        self.input_filename = ''
        self.output_filename = ''
        self.delay = 0.1
        super().__init__(name=self.name,
                         input_filename=self.input_filename,
                         output_filename=self.output_filename,
                         delay=self.delay)

    def active(self):
        with open(self.input_filename, 'r') as f:
            text = f.read()
        tts = gTTS(text=text,
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
