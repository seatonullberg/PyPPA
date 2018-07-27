from base_service import BaseService
import praw


class RedditService(BaseService):

    def __init__(self):
        self.name = 'RedditService'
        self.input_filename = 'reddit_service.in'
        self.output_filename = 'reddit_service.out'
        self.delay = 0
        super().__init__(name=self.name,
                         input_filename=self.input_filename,
                         output_filename=self.output_filename,
                         delay=self.delay)
