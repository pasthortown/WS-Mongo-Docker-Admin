from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.utils import COMMASPACE, formatdate
from email import encoders
import smtplib
import jinja2

def send_mail(server, port, tls, username, password, send_from, send_to, subject, template_name, params, files=[]):
    env = jinja2.Environment(loader=jinja2.FileSystemLoader('Templates'))
    with smtplib.SMTP(server,port) as smtp:
        msg = MIMEMultipart('alternative')
        msg['From'] = send_from
        msg['To'] = COMMASPACE.join(send_to)
        msg['Date'] = formatdate(localtime=True)
        msg['Subject'] = subject
        template = env.get_template(template_name)
        msg.attach(MIMEText(template.render(params), 'html'))
        for file in files:
            part = MIMEBase('application', "octet-stream")
            part.set_payload(file['file'])
            part.add_header('Content-Transfer-Encoding', 'base64')
            part['Content-Disposition'] = 'attachment; filename="%s"' % file['name']
            msg.attach(part)
        smtp.ehlo()
        if (tls == 1):
            smtp.starttls()
        smtp.login(username, password)
        smtp.sendmail(send_from, send_to, msg.as_string())
        smtp.quit()