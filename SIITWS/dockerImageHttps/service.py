from tornado.httpserver import HTTPServer
import os
from tornado.ioloop import IOLoop
from tornado.web import Application, RequestHandler
from tornado.escape import json_decode
import json
from requests.auth import HTTPBasicAuth
from requests import Session
import requests

siit_url = os.getenv('siit_url')

class DefaultHandler(RequestHandler):
    def set_default_headers(self):
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Allow-Headers', '*')
        self.set_header('Access-Control-Allow-Methods', '*')

    def get(self):
        self.write({'response':'Servicio Transaccional con SIIT Operativo', 'status':200})

class ActionHandler(RequestHandler):
    def set_default_headers(self):
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Allow-Headers', '*')
        self.set_header('Access-Control-Allow-Methods', '*')

    def options(self, action):
        pass
    
    def post(self, action):
        content = json_decode(self.request.body)
        if (action == 'get_transport_companies_info'):
            rucs = content['rucs']
            respuesta = get_transport_companies_info(rucs)
        if (action == 'get_guias_info'):
            identifications = content['identifications']
            respuesta = get_guias_info(identifications)
        self.write(respuesta)
        return

def get_transport_companies_info(rucs):
    try:
        response = requests.post(siit_url + 'establecimientos', data = json.dumps(rucs), headers= {"Content-type":"application/json"})
        return {"transport_companies":response.json(), "status":200}
    except:
        return {"transport_companies":[], "status":200}

def get_guias_info(identifications):
    try:
        response = requests.post(siit_url + 'guias', data = json.dumps(identifications), headers= {"Content-type":"application/json"})
        return {"guias":response.json(), "status":200}
    except:
        return {"guias":[], "status":200}

def make_app():
    urls = [
        ("/", DefaultHandler),
        ("/([^/]+)", ActionHandler)
    ]
    return Application(urls, debug=True)

def make_app():
    urls = [
        ("/", DefaultHandler),
        ("/([^/]+)", ActionHandler)
    ]
    return Application(urls, debug=True)
  
if __name__ == '__main__':
    app = make_app()
    http_server = HTTPServer(app, ssl_options={
        "certfile": "/ssl/wildcard.chained.crt",
        "keyfile": "/ssl/privatekey.key",
    })
    http_server.listen(5050)    
    IOLoop.current().start()