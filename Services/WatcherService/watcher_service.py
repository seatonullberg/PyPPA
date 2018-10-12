import multiprocessing
import cv2

from Services import base
from FacialRecognition.model import FacialRecognitionModel
from utils import parallelization


# TODO: allow frame_data offloading
class WatcherService(base.Service):

    def __init__(self):
        self.name = 'WatcherService'
        super().__init__(name=self.name,
                         target=self.active)

    def start(self, queue):
        self._process_video()

    def active(self):
        pass
        '''
        frame_data = self.data_return_queue.pop()
        self.data_return_queue.clear()
        self.respond(frame_data)
        '''

    def _process_video(self):
        data_processing_queue = parallelization.TwoWayProcessQueue()
        model = FacialRecognitionModel()
        process = multiprocessing.Process(target=self._process_faces,
                                          args=(data_processing_queue,
                                                model))
        process.start()
        video_capture = cv2.VideoCapture(0)
        last_frame_data = None
        while True:
            ret, frame = video_capture.read()
            data_processing_queue.server_put(frame)

            if data_processing_queue.client_empty():
                frame_data = last_frame_data
            else:
                frame_data = data_processing_queue.client_get()

            if frame_data is not None:
                for d in frame_data:
                    left = d['location']['left']
                    right = d['location']['right']
                    top = d['location']['top']
                    bottom = d['location']['bottom']
                    cv2.rectangle(img=frame,
                                  pt1=(left, top),
                                  pt2=(right, bottom),
                                  color=self._color_matcher(d['distance']),
                                  thickness=2)
                    cv2.putText(frame,
                                d['name'],
                                (left, int(bottom + (15 * (bottom - top) / 100))),
                                cv2.FONT_HERSHEY_DUPLEX,
                                (bottom - top) / 200,
                                (255, 255, 255),
                                lineType=cv2.LINE_AA)
            last_frame_data = frame_data

            # Display the resulting frame
            cv2.imshow('Video', frame)
            cv2.waitKey(1)

    @staticmethod
    def _process_faces(video_queue, model):
        while True:
            if not video_queue.server_empty():
                frame = video_queue.server_get()
                frame_data = model.process(frame)
                video_queue.client_put(frame_data)  # return data to be displayed

    @staticmethod
    def _color_matcher(dist):
        cmap = {6: (229, 181, 0),
                5: (222, 216, 0),
                4: (183, 216, 0),
                3: (139, 210, 0),
                2: (98, 203, 0),
                1: (59, 197, 0),
                0: (22, 191, 0)}
        dist = str(dist)
        dec = dist.split('.')[-1]
        for k, v in cmap.items():
            if int(dec[0]) == k:
                return v[::-1]  # opencv works in BGR
        return 0, 0, 0  # if there is some error in the mapping just use black
