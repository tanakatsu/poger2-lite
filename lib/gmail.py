import smtplib
from email.message import EmailMessage


class Gmail:
    def __init__(self, login_addr: str, app_password: str):
        self.__login_addr = login_addr
        self.__app_password = app_password

    def send(self, to_addr: str, subject: str, body: str):
        # Build a message
        msg = EmailMessage()
        msg.set_content(body)
        msg['Subject'] = subject
        msg['From'] = self.__login_addr
        msg['To'] = to_addr

        connection = smtplib.SMTP("smtp.gmail.com", 587)
        # connection.set_debuglevel(True)  # enable debug output
        connection.starttls()
        connection.login(self.__login_addr, self.__app_password)
        connection.send_message(msg)
        connection.close()
