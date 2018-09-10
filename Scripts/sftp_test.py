import paramiko
import shutil
import os
import requests

'''
ssh_client =paramiko.SSHClient()
ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh_client.connect(hostname="ssh.pythonanywhere.com",
                   username="PyPPA",
                   password="GingerPyPPA1031")

ftp_client = ssh_client.open_sftp()
ftp_client.get(remotepath="/home/PyPPA/external_resources/mimic.zip",
               localpath="/home/seaton/repos/PyPPA/Scripts/mimic.zip")
ftp_client.close()
'''


def test():
    r = requests.post(url='https://pyppa.pythonanywhere.com/generate_ssh_credentials',
                      data={'ip': '68.105.173.56'}
                      )
    print(r.content)


if __name__ == "__main__":
    test()
