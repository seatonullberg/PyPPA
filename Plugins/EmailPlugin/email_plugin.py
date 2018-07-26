import smtplib
import time
import imaplib
import email
from base_plugin import BasePlugin
import base64


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
        typ, data = server.search(None, 'ALL')
        for num in data[0].split():
            typ, data = server.fetch(num, '(RFC822)')
            print('Message %s\n%s\n' % (num, data[0][1]))
        server.close()
        server.logout()

