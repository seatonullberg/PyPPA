# TODO: split large incoming text up into smaller bits and multithread for improved response time

import speech_recognition as sr
import pyaudio
import struct
import wave
import os
import numpy as np


class FloatingListener(object):

    def __init__(self):
        self.CHUNK = 4000
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 2
        self.RATE = 44100
        self.WAVE_OUTPUT_FILENAME = "user_input.wav"
        self.threshold = 0.2
        self.pre_buffer = None
        self.post_buffer = 1
        self.max_dialogue = 10

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
        wf = wave.open(self.WAVE_OUTPUT_FILENAME, 'wb')
        wf.setnchannels(self.CHANNELS)
        wf.setsampwidth(p.get_sample_size(self.FORMAT))
        wf.setframerate(self.RATE)
        wf.writeframes(b''.join(frames))
        wf.close()

    def recognize(self, fname):
        r = sr.Recognizer()
        file = sr.AudioFile(fname)
        with file as source:
            audio = r.record(source)
        try:
            command = r.recognize_google(audio_data=audio)
        except sr.UnknownValueError:
            print('unknown value error')
            command = None
        os.remove(self.WAVE_OUTPUT_FILENAME)
        return command

    def listen_and_convert(self):

        if self.pre_buffer is None:
            self.pre_buffer = np.inf
        else:
            self.pre_buffer *= self.RATE / self.CHUNK
        self.post_buffer *= self.RATE / self.CHUNK
        self.max_dialogue *= self.RATE / self.CHUNK

        p = pyaudio.PyAudio()
        stream = p.open(format=self.FORMAT,
                        channels=self.CHANNELS,
                        rate=self.RATE,
                        input=True,
                        frames_per_buffer=self.CHUNK)

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
                if len(dialogue_frames) > self.max_dialogue:
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
                    # print('pre buffer timeout')
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
                    # print('post buffer timeout')
                    stream.stop_stream()
                    stream.close()
                    p.terminate()
                    self.write_wav(dialogue_frames)
                    break
                elif len(post_frames) < self.post_buffer:
                    # otherwise continue waiting
                    post_frames.append(data)

        command = self.recognize(self.WAVE_OUTPUT_FILENAME)
        return command

    def reset_threshold(self, chunks=20):
        '''
        Listen briefly and reset noise threshold to reasonable value
        - redefines self.threshold
        :param chunks: number of chunks to listen to
        :return: dict() old and new threshold values
        '''
        old_threshold = self.threshold
        p = pyaudio.PyAudio()
        stream = p.open(format=self.FORMAT,
                        channels=self.CHANNELS,
                        rate=self.RATE,
                        input=True,
                        frames_per_buffer=self.CHUNK)
        print('Setting noise threshold...')
        c = 0
        values = []
        while c < chunks:
            data = stream.read(self.CHUNK)
            amplitude = self.get_rms(data)
            values.append(amplitude)
            c += 1
        _mean = np.mean(values)
        _stdev = np.std(values)
        print(_mean)
        print(_stdev)
        new_threshold = _mean+(4*_stdev)
        self.threshold = new_threshold

        return {'old': old_threshold, 'new': new_threshold}
