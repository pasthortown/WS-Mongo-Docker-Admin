import os
from tornado.ioloop import IOLoop
from tornado.web import Application, RequestHandler
from tornado.escape import json_decode
from tornado.httpserver import HTTPServer
from pymongo import MongoClient
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
        self.write({'response':'Administrador de Archivos Operativo','status':200})


class ActionHandler(RequestHandler):
    def set_default_headers(self):
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Allow-Headers', '*')
        self.set_header('Access-Control-Allow-Methods', '*')
    
    def options(self, folder, action):
        pass

    def post(self, folder, action):
        content = json_decode(self.request.body)
        headers = self.request.headers
        token = headers['token']
        auth = validate_token(token)
        if auth == False:
            self.write({'response':'Acceso Denegado', 'status':'500'})
            return
        if (action == 'upload_files'):
            files = content['files']
            respuesta = upload_files(folder, files)
        if (action == 'get_file'):
            file_id = content['file_id']
            respuesta = get_file(folder, file_id)
        if (action == 'get_files'):
            respuesta = get_files(folder)
        if (action == 'update_file'):
            file_id = content['file_id']
            file = content['file']
            respuesta = update_file(folder, file_id, file)
        if (action == 'delete_file'):
            file_id = content['file_id']
            deleted = delete_file(folder, file_id)
            respuesta = {'response':'Elemento no encontrado', 'status':500}
            if (deleted == True):
                respuesta = {'response':'Elemento eliminado', 'status':200}
        self.write(respuesta)
        return

def upload_files(folder, files):
    collection = db[folder]
    toReturn = []
    for file in files:
        file_id = str(uuid.uuid4())
        collection.insert_one({
            "file_id": file_id,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "name": file['name'],
            "type": file['type'],
            "size": file['size'],
            "file_base64": file['file_base64']})
        toReturn.append(
            {"file_id": file_id, "name": file['name'], 'type': file['type']}
        )
    return {'response':toReturn, 'status':200}

def get_file(folder, file_id):
    collection = db[folder]
    files = collection.find({"file_id":file_id},{
        "file_id": True, 
        "timestamp": True,
        "name": True, 
        "type": True, 
        "size": True, 
        "file_base64": True,
        "_id": False})
    files_to_return = json.loads(json_util.dumps(files))
    if (len(files_to_return)>0):
        toReturn = files_to_return[0]
        status = 200
    else:
        toReturn = 'Archivo no encontrado'
        status = 500
    return {'response':toReturn, 'status':status}

def get_files(folder):
    collection = db[folder]
    files = collection.find({}, {
        "file_id": True, 
        "timestamp": True,
        "name": True, 
        "type": True, 
        "size": True, 
        "_id": False})
    files_to_return = json.loads(json_util.dumps(files))
    return {'response':files_to_return, 'status':200}

def update_file(catalog, file_id, file):
    collection = db[catalog]
    filter = {"file_id":file_id}
    prev_items = collection.find(filter)
    previous_items = json.loads(json_util.dumps(prev_items))
    if (len(previous_items) == 0):
        return {'response': 'Elemento no encontrado', 'status':500}
    else:
        file['timestamp'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        collection.update_one(filter, {'$set':file})
        files = collection.find(filter,{
            "file_id": True, 
            "timestamp": True,
            "name": True, 
            "type": True, 
            "size": True, 
            "_id": False})
        files_to_return = json.loads(json_util.dumps(files))
        return {'response':files_to_return, 'status':200}

def delete_file(folder, file_id):
    collection = db[folder]
    filter = {"file_id":file_id}
    files = collection.find(filter, {
        "file_id": True, 
        "_id": False})
    files_to_return = json.loads(json_util.dumps(files))
    if (len(files_to_return)>0):
        collection.delete_one(filter)
        toReturn = True
    else:
        toReturn = False
    return toReturn

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