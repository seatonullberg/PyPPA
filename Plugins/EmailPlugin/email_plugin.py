import imaplib
import email
from Plugins import base


class EmailPlugin(base.Plugin):

    def __init__(self):
        self.name = 'EmailPlugin'
        self.command_hooks = {'check_email': ['check my emails', 'check my email',
                                              'get my emails', 'get my email']}
        self.modifiers = {'check_email': {}}
        super().__init__(name=self.name,
                         command_hooks=self.command_hooks,
                         modifiers=self.modifiers)

    def check_email(self):
        PASSWORD = self.get_environment_variable('PASSWORD')
        EMAIL = self.get_environment_variable('EMAIL')
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
