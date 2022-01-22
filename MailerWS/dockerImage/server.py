import os
from tornado.ioloop import IOLoop
from tornado.web import Application, RequestHandler
from tornado.escape import json_decode
import datetime
import jwt
from dateutil import parser
import mailer

app_secret = os.getenv('app_secret')
allowed_app_name = os.getenv('allowed_app_name')
web_url = os.getenv('web_url')
smtp_server = os.getenv('smtp_server')
smtp_port = os.getenv('smtp_port')
smtp_tls = os.getenv('smtp_tls')
smtp_user = os.getenv('smtp_user')
smtp_password = os.getenv('smtp_password')

class DefaultHandler(RequestHandler):
    def set_default_headers(self):
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Allow-Headers', '*')
        self.set_header('Access-Control-Allow-Methods', '*')

    def get(self):
        self.write({'response':'Servicio de Envío de Correos Operativo','status':200})


class ActionHandler(RequestHandler):
    def set_default_headers(self):
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Allow-Headers', '*')
        self.set_header('Access-Control-Allow-Methods', '*')
    
    def options(self, action):
        pass

    def post(self, action):
        content = json_decode(self.request.body)
        headers = self.request.headers
        token = headers['token']
        auth = validate_token(token)
        if auth == False:
            self.write({'response':'Acceso Denegado', 'status':'500'})
            return
        if (action == 'send'):
            email = content['email']
            subject = content['subject']
            params = content['params']
            template_name = content['template_name']
            attachments = content['attachments']
            respuesta = send(email, subject, params, template_name, attachments)
        self.write(respuesta)
        return

def send(email, subject, params_in, template_name, attachments):
    params = params_in
    params['app_name']=allowed_app_name
    params['web_url']=web_url
    to = email
    mailer.send_mail(
        smtp_server,
        smtp_port,
        int(smtp_tls),
        smtp_user,
        smtp_password,
        allowed_app_name,
        to,
        subject,
        template_name,
        params,
        attachments)
    return {'response': 'Correo electrónico enviado satisfactoriamente', 'status':200}

def validate_token(token):
    try:
        response = jwt.decode(token, app_secret, algorithms=['HS256'])
        exp_time = parser.parse(response['valid_until'])
        app_name = response['app_name']
        if (app_name == allowed_app_name and datetime.datetime.now() < exp_time):
            return True
        else:
            return False
    except:
        return False

def make_app():
    urls = [
        ("/", DefaultHandler),
        ("/([^/]+)", ActionHandler)
    ]
    return Application(urls, debug=True)

if __name__ == '__main__':
    app = make_app()
    app.listen(5050)
    IOLoop.instance().start()