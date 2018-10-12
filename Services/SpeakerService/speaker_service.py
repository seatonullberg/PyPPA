from gtts import gTTS
from pydub import AudioSegment
from pyaudio import PyAudio
import wave
import os
import subprocess
from Services import base


class SpeakerService(base.Service):
    # there is no default behavior and no output file
    # output is through the speakers

    def __init__(self):
        self.name = 'SpeakerService'
        super().__init__(name=self.name,
                         target=self.active)

    def active(self):
        # mimic is default
        try:
            tts_engine = self.environment_variable('TTS_ENGINE')
        except KeyError:
            self._mimic_tts()
            return

        if tts_engine == "mimic":
            self._mimic_tts()
        elif tts_engine == "gtts":
            self._gtts_tts()
        else:
            raise NotImplementedError()

    def _mimic_tts(self):
        mimic_path = os.path.join(os.getcwd(), 'bin', 'mimic', 'mimic')
        subprocess.call([mimic_path, "-t", self.input_data])
        self.respond(output_data=None)

    def _gtts_tts(self):
        tts = gTTS(text=self.input_data,
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
