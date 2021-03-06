import speech_recognition as sr
import pyaudio
import struct
import wave
import os
import numpy as np
import copy

from Plugins import base


class ListenerPlugin(base.Plugin):

    def __init__(self):
        self.CHUNK = 2048
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 2
        self.RATE = 44100
        self.TMP_WAV_FILENAME = "tmp_user_input.wav"
        tmp_wav_path = [os.getcwd(), 'tmp', self.TMP_WAV_FILENAME]
        self.TMP_WAV_FILENAME = os.path.join('', *tmp_wav_path)
        self.threshold = 0.1
        self.pre_buffer = None
        self.post_buffer = 1
        self.maximum = 10

        self.name = 'ListenerPlugin'
        self.data_link_map = {'input_data': self.process_data_link}
        super().__init__(name=self.name,
                         command_hooks={},
                         modifiers={},
                         data_link_map=self.data_link_map)  # it is ok for plugins to not have comands

    def process_data_link(self, link):
        params_dict = link.fields['input_data']
        if params_dict['reset_threshold']:
            link.fields['output_data'] = self.reset_threshold()
        else:
            self.pre_buffer = params_dict['pre_buffer']
            self.post_buffer = params_dict['post_buffer']
            self.maximum = params_dict['maximum']
            link.fields['output_data'] = self.listen_and_convert()
        return link

    def get_rms(self, block):
        SHORT_NORMALIZE = (1.0 / 32768.0)
        count = len(block) / 2
        format = "%dh" % (count)
        shorts = struct.unpack(format, block)

        # iterate over the block.
        sum_squares = 0.0
        for sample in shorts:
            # sample is a signed short in +/- 32768.
            # normalize it to 1.0
            n = sample * SHORT_NORMALIZE
            sum_squares += n * n

        return np.sqrt(sum_squares / count)

    def write_wav(self, frames):
        p = pyaudio.PyAudio()
        wf = wave.open(self.TMP_WAV_FILENAME, 'wb')
        wf.setnchannels(self.CHANNELS)
        wf.setsampwidth(p.get_sample_size(self.FORMAT))
        wf.setframerate(self.RATE)
        wf.writeframes(b''.join(frames))
        wf.close()

    def recognize(self):
        r = sr.Recognizer()

        try:
            with sr.AudioFile(self.TMP_WAV_FILENAME) as source:
                audio = r.record(source)
        except FileNotFoundError:
            print('recognize was unable to find: {}'.format(self.TMP_WAV_FILENAME))
            raise
        try:
            command = r.recognize_google(audio_data=audio)
        except sr.UnknownValueError:
            print('unknown value error')
            command = ''

        os.remove(self.TMP_WAV_FILENAME)
        return command

    def listen_and_convert(self, input_device_name='default'):

        if self.pre_buffer is None:
            self.pre_buffer = np.inf
        else:
            self.pre_buffer *= self.RATE / self.CHUNK
        self.post_buffer *= self.RATE / self.CHUNK
        self.maximum *= self.RATE / self.CHUNK

        p = pyaudio.PyAudio()
        # make sure to use the specified input device always
        input_index = 0
        for index in range(p.get_device_count()):
            if p.get_device_info_by_index(index).get('name') == input_device_name:
                input_index = index
                break
        stream = p.open(format=self.FORMAT,
                        channels=self.CHANNELS,
                        rate=self.RATE,
                        input=True,
                        output=False,
                        frames_per_buffer=self.CHUNK,
                        input_device_index=input_index)

        pre_frames = []
        dialogue_frames = []
        post_frames = []

        print('Speak:')
        while True:
            data = stream.read(self.CHUNK)
            amplitude = self.get_rms(data)
            # print(amplitude)
            if amplitude > self.threshold:
                # noisy frame
                dialogue_frames.append(data)
                # if noise exceeds max dialogue timeout
                if len(dialogue_frames) > self.maximum:
                    # print('max dialogue timeout')
                    stream.stop_stream()
                    stream.close()
                    p.terminate()
                    self.write_wav(dialogue_frames)
                    break
                # any noise cancels out the post noise shutdown
                post_frames = []
            elif amplitude < self.threshold and len(dialogue_frames) == 0:
                # quiet frame before any noise 'pre_frame'
                pre_frames.append(data)
                # timeout if nothing is said in certain amount of time
                if len(pre_frames) > self.pre_buffer:
                    stream.stop_stream()
                    stream.close()
                    p.terminate()
                    break
            elif amplitude < self.threshold and len(dialogue_frames) > 0:
                # add to dialogue frames for smoother file even though it is silence
                dialogue_frames.append(data)
                # check to see if the post_buffer is surpassed
                if len(post_frames) > self.post_buffer:
                    # after enough silent frames, close the mic and process noise
                    stream.stop_stream()
                    stream.close()
                    p.terminate()
                    self.write_wav(dialogue_frames)
                    break
                elif len(post_frames) < self.post_buffer:
                    # otherwise continue waiting
                    post_frames.append(data)
        # Reset the constants so the object can be used again
        if self.pre_buffer is np.inf:
            self.pre_buffer = None
        else:
            self.pre_buffer /= self.RATE / self.CHUNK
        self.post_buffer /= self.RATE / self.CHUNK
        self.maximum /= self.RATE / self.CHUNK

        command = self.recognize()
        try:
            command = command.lower()
        except AttributeError:
            raise

        return command

    def reset_threshold(self, chunks=20, input_device_name='default'):
        '''
        Listen briefly and reset noise threshold to reasonable value
        - redefines self.threshold
        :param chunks: number of chunks to listen to
        :param input_device_name: str name of audio input device to record with
        :return: dict() old and new threshold values
        '''
        old_threshold = copy.deepcopy(self.threshold)
        p = pyaudio.PyAudio()
        # make sure to use the specified input device always
        input_index = 0
        for index in range(p.get_device_count()):
            if p.get_device_info_by_index(index).get('name') == input_device_name:
                input_index = index
                break
        stream = p.open(format=self.FORMAT,
                        channels=self.CHANNELS,
                        rate=self.RATE,
                        input=True,
                        output=False,
                        frames_per_buffer=self.CHUNK,
                        input_device_index=input_index)

        print('Setting noise threshold...')
        c = 0
        values = []
        while c < chunks:
            data = stream.read(self.CHUNK)
            amplitude = self.get_rms(data)
            values.append(amplitude)
            c += 1

        # kill stream
        stream.stop_stream()
        stream.close()
        p.terminate()

        # set new threshold to be 4 standard deviations above the ambient noise level
        _mean = np.mean(values)
        _stdev = np.std(values)
        new_threshold = _mean + (4 * _stdev)
        self.threshold = new_threshold
        return {'old': old_threshold, 'new': new_threshold}
