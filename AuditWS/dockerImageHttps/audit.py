import os
from tornado.ioloop import IOLoop
from tornado.web import Application, RequestHandler
from tornado.escape import json_decode
from tornado.httpserver import HTTPServer
from pymongo import MongoClient, ASCENDING
import datetime
from bson import json_util
import json
import uuid
import jwt
from dateutil import parser

mongo_bdd = os.getenv('mongo_bdd')
mongo_bdd_server = os.getenv('mongo_bdd_server')
mongo_user = os.getenv('mongo_user')
mongo_password = os.getenv('mongo_password')
app_secret = os.getenv('app_secret')
allowed_app_name = os.getenv('allowed_app_name')

database_uri='mongodb://'+mongo_user+':'+mongo_password+'@'+ mongo_bdd_server +'/'
client = MongoClient(database_uri)
db = client[mongo_bdd]

class DefaultHandler(RequestHandler):
    def set_default_headers(self):
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Allow-Headers', '*')
        self.set_header('Access-Control-Allow-Methods', '*')

    def get(self):
        self.write({'response':'Administrador de Auditoría Operativo','status':200})

class ActionHandler(RequestHandler):
    def set_default_headers(self):
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Allow-Headers', '*')
        self.set_header('Access-Control-Allow-Methods', '*')
    
    def options(self, invoice, action):
        pass

    def post(self, invoice, action):
        content = json_decode(self.request.body)
        headers = self.request.headers
        token = headers['token']
        auth = validate_token(token)
        if auth == False:
            self.write({'response':'Acceso Denegado', 'status':'500'})
            return
        if (action == 'write'):
            log = content['log']
            respuesta = write(invoice, log)
        if (action == 'read'):
            respuesta = read(invoice)
        if (action == 'search'):
            attribute = content['attribute']
            value = content['value']
            output_model = content['output_model']
            respuesta = search(invoice, attribute, value, output_model)
        self.write(respuesta)
        return

def write(invoice, log):
    collection = db[invoice]
    log_id = str(uuid.uuid4())
    log['log_id'] = log_id
    log['timestamp'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    collection.insert_one(log)
    return {'response':'Registro de Auditoría Almacenado Correctamente', 'status':200}

def read(invoice):
    collection = db[invoice]
    logs = collection.find({},{"_id": False}).sort('timestamp', ASCENDING)
    logs_to_return = json.loads(json_util.dumps(logs))
    status = 200
    return {'response':logs_to_return, 'status':status}

def search(invoice, attribute, value, output_model):
    collection = db[invoice]
    output_model['_id'] = False
    output_model['log_id'] = True
    output_model['timestamp'] = True
    filter = {}
    filter[attribute] = value
    items = collection.find(filter, output_model)
    items_to_return = json.loads(json_util.dumps(items))
    if (len(items_to_return)>0):
        toReturn = items_to_return
        status = 200
    else:
        toReturn = 'Registro de Auditoría no encontrado'
        status = 500
    return {'response':toReturn, 'status':status}

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
        ("/([^/]+)/([^/]+)", ActionHandler)
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