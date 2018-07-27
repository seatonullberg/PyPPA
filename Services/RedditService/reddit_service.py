from base_service import BaseService
import praw


class RedditService(BaseService):

    def __init__(self):
        CLIENT_ID = self.config_obj.environment_variables['RedditService']['CLIENT_ID']
        SECRET = self.config_obj.environment_variables['RedditService']['SECRET']
        USER_AGENT = self.config_obj.environment_variables['RedditService']['USER_AGENT']
        USERNAME = self.config_obj.environment_variables['RedditService']['USERNAME']
        self.BOT = praw.Reddit(client_id=CLIENT_ID,
                               client_secret=SECRET,
                               user_agent=USER_AGENT)
        self.USER = self.BOT.redditor(USERNAME)

        self.name = 'RedditService'
        self.input_filename = 'reddit_service.in'
        self.output_filename = 'reddit_service.out'
        self.delay = 0
        super().__init__(name=self.name,
                         input_filename=self.input_filename,
                         output_filename=self.output_filename,
                         delay=self.delay)
