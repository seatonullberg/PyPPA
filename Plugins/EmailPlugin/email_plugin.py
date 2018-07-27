import imaplib
import email
from base_plugin import BasePlugin


class EmailPlugin(BasePlugin):

    def __init__(self):
        self.name = 'EmailPlugin'
        self.COMMAND_HOOK_DICT = {'check_email': ['check my emails', 'check my email',
                                                  'get my emails', 'get my email']}
        self.MODIFIERS = {'check_email': {}}
        super().__init__(name=self.name,
                         command_hook_dict=self.COMMAND_HOOK_DICT,
                         modifiers=self.MODIFIERS)

    def check_email(self):
        PASSWORD = self.config_obj.environment_variables['EmailPlugin']['PASSWORD']
        EMAIL = self.config_obj.environment_variables['EmailPlugin']['EMAIL']
        SMTP_SERVER = EMAIL.split('@')[-1]
        SMTP_SERVER = "imap."+SMTP_SERVER

        # port 993
        server = imaplib.IMAP4_SSL(SMTP_SERVER, 993)
        server.login(EMAIL, PASSWORD)
        server.select('INBOX')
        typ, data = server.search(None, '(UNSEEN)')
        for num in data[0].split():
            typ, data = server.fetch(num, '(RFC822)')
            d = data[0][1].decode('utf-8')
            msg = email.message_from_string(d)
            print(msg['from'])
            print(msg['subject'])
        server.close()
        server.logout()
        # terminate after one use
        self.pass_and_terminate(name='SleepPlugin',
                                cmd='sleep')
