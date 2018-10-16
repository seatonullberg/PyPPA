from gtts import gTTS
from pydub import AudioSegment
from pyaudio import PyAudio
import wave
import os
import subprocess
from Plugins import base


class SpeakerPlugin(base.Plugin):
    # there is no default behavior and no output file
    # output is through the speakers

    def __init__(self):
        self.name = 'SpeakerPlugin'
        super().__init__(name=self.name, command_hooks={}, modifiers={})  # ok for plugins to not have commands

    def process_data_link(self, link):
        tts_engine = self.request_environment_variable('TTS_ENGINE')
        if tts_engine == "mimic":
            self._mimic_tts(link.fields['input_data'])
        elif tts_engine == "gtts":
            self._gtts_tts(link.fields['input_data'])
        else:
            raise NotImplementedError()
        return link

    def _mimic_tts(self, text):
        mimic_path = os.path.join(os.getcwd(), 'bin', 'mimic', 'mimic')
        subprocess.call([mimic_path, "-t", text])

    def _gtts_tts(self, text):
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
