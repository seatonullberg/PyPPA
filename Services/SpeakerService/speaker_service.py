from base_service import BaseService
from gtts import gTTS
from pydub import AudioSegment
from pyaudio import PyAudio
import wave
import os
import subprocess


class SpeakerService(BaseService):
    # there is no default behavior and no output file
    # output is through the speakers

    def __init__(self):
        self.name = 'SpeakerService'
        self.input_filename = 'vocalize.txt'
        self.output_filename = ''   # there is no output file
        self.delay = 0.1
        super().__init__(name=self.name,
                         input_filename=self.input_filename,
                         output_filename=self.output_filename,
                         delay=self.delay)

    def active(self):
        # mimic is default
        try:
            tts_engine = self.config_obj.environment_variables[self.name]['TTS_ENGINE']
        except KeyError:
            self._mimic_tts()
            return

        if tts_engine == "mimic":
            self._mimic_tts()
        elif tts_engine == "gtts":
            self._gtts_tts()
        else:
            self._mimic_tts()

    def _mimic_tts(self):
        mimic_path = os.path.join(os.getcwd(), 'bin', 'mimic', 'mimic')
        subprocess.call([mimic_path, self.input_filename])

    def _gtts_tts(self):
        with open(self.input_filename, 'r') as f:
            text = f.read()
        tts = gTTS(text=text,
                   lang='en',
                   slow=False,
                   lang_check=False)
        tmp_mp3_path = [os.getcwd(), 'tmp', 'tmp_vocal.mp3']
        tmp_mp3_path = os.path.join('', *tmp_mp3_path)
        tmp_wav_path = tmp_mp3_path.replace('.mp3', '.wav')
        tts.save(tmp_mp3_path)
        mp3 = AudioSegment.from_mp3(tmp_mp3_path)
        mp3.export(tmp_wav_path, format='wav')
        p = PyAudio()
        with wave.open(tmp_wav_path, 'rb') as wav:
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
        os.remove(tmp_mp3_path)
        os.remove(tmp_wav_path)
        p.terminate()
