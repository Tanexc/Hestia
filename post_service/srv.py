import os
import smtplib
import mimetypes
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv


mail_sender = 'hestnetreg@gmail.com'
mail_receiver = 'shdhdchel@mail.ru'
username = 'hestnetreg@gmail.com'
password = '12348AY785L'
server = smtplib.SMTP('smtp.gmail.com:587')

# Формируем тело письма
subject = u'Тестовый email от ' + mail_sender
body = u'Это тестовое письмо оптправлено с помощью smtplib'
msg = MIMEText(body, 'plain', 'utf-8')
msg['Subject'] = Header(subject, 'utf-8')

# Отпавляем письмо
server.starttls()
server.ehlo()
server.login(username, password)
server.sendmail(mail_sender, mail_receiver, msg.as_string())
server.quit()