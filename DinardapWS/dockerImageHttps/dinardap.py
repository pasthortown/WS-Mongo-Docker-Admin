from tornado.httpserver import HTTPServer
import os
from turtle import update
from tornado.ioloop import IOLoop
from tornado.web import Application, RequestHandler
from tornado.escape import json_decode
from pymongo import MongoClient
import datetime
from bson import json_util
import json
import uuid
from dateutil import parser
import random
import string
from zeep import Client
from zeep.transports import Transport
from zeep import helpers
from requests.auth import HTTPBasicAuth
from requests import Session
import redis

mongo_bdd = os.getenv('mongo_bdd')
mongo_bdd_server = os.getenv('mongo_bdd_server')
mongo_user = os.getenv('mongo_user')
mongo_password = os.getenv('mongo_password')
soap_user = os.getenv('soap_user')
soap_password = os.getenv('soap_password')
soap_wsdl = os.getenv('soap_wsdl')
redis_live = os.getenv('redis_live')
redis_live_error = os.getenv('redis_live_error')

database_uri='mongodb://'+mongo_user+':'+mongo_password+'@'+ mongo_bdd_server +'/'
client = MongoClient(database_uri)
db = client[mongo_bdd]
cache = redis.Redis(host='redis', port=6379)

class DefaultHandler(RequestHandler):
    def set_default_headers(self):
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Allow-Headers', '*')
        self.set_header('Access-Control-Allow-Methods', '*')

    def get(self):
        self.write({'response':'Servicio Transaccional con DINARDAP Operativo', 'status':200})

class ActionHandler(RequestHandler):
    def set_default_headers(self):
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Allow-Headers', '*')
        self.set_header('Access-Control-Allow-Methods', '*')

    def options(self, action):
        pass
    
    def post(self, action):
        content = json_decode(self.request.body)
        if (action == 'ruc'):
            number = content['RUC']
            respuesta = get_ruc(number)
        if (action == 'cedula'):
            number = content['identificacion']
            respuesta = get_cedula(number)
        if (action == 'supercias'):
            number = content['identificacion']
            respuesta = get_supercias(number)
        self.write(respuesta)
        return

def prepare_mongo_data(items):
    return json.loads(json_util.dumps(items))

def get_ruc(number):
    cache_data = cache.get('ruc_data_' + number)
    if (cache_data != None):
        return json.loads(cache_data)
    collection = db['RUC']
    filter = {"number": number}
    bdd_info = collection.find(filter)
    ruc = prepare_mongo_data(bdd_info)
    toReturn = {}
    toReturn['timestamp'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    toReturn['number'] = number
    info_dinardap_sri_razon_social = get_sri_razon_social(number)
    info_dinardap_sri_actividad_economica = get_sri_actividad_economica(number)
    info_dinardap_sri_establecimientos = get_sri_establecimientos(number)
    info_dinardap_sri_ruc_completo = get_sri_ruc_completo(number)
    info_dinardap_sri_ruc = get_sri_ruc(number)
    info_dinardap_sri_ubicaciones_geograficas = get_sri_ubicaciones_geograficas(number)
    info_dinardap_sri_ruc_contactos = get_sri_ruc_contactos(number)
    info_dinardap_sri_ruc_datos = get_sri_ruc_datos(number)
    update_obj = False
    if (info_dinardap_sri_razon_social != 'error'):
        update_obj = True
        toReturn['sri_razon_social'] = info_dinardap_sri_razon_social
    if (info_dinardap_sri_actividad_economica != 'error'):
        update_obj = True
        toReturn['sri_actividad_economica'] = info_dinardap_sri_actividad_economica
    if (info_dinardap_sri_establecimientos != 'error'):
        update_obj = True
        toReturn['sri_establecimientos'] = info_dinardap_sri_establecimientos
    if (info_dinardap_sri_ruc_completo != 'error'):
        update_obj = True
        toReturn['sri_ruc_completo'] = info_dinardap_sri_ruc_completo
    if (info_dinardap_sri_ruc != 'error'):
        update_obj = True
        toReturn['sri_ruc'] = info_dinardap_sri_ruc
    if (info_dinardap_sri_ubicaciones_geograficas != 'error'):
        update_obj = True
        toReturn['sri_ubicaciones_geograficas'] = info_dinardap_sri_ubicaciones_geograficas
    if (info_dinardap_sri_ruc_contactos != 'error'):
        update_obj = True
        toReturn['sri_ruc_contactos'] = info_dinardap_sri_ruc_contactos
    if (info_dinardap_sri_ruc_datos != 'error'):
        update_obj = True
        toReturn['sri_ruc_datos'] = info_dinardap_sri_ruc_datos
    if (update_obj):
        if (len(ruc)>0):
            collection.update_one(filter, {'$set': toReturn})
        else:
            collection.insert_one(toReturn)
        toSend = {
            "sri_ruc_completo": info_dinardap_sri_ruc_completo,
            "sri_ruc": info_dinardap_sri_ruc,
            "sri_establecimientos": info_dinardap_sri_establecimientos,
            "sri_razon_social": info_dinardap_sri_razon_social,
            "sri_actividad_economica": info_dinardap_sri_actividad_economica,
            "sri_ruc_datos": info_dinardap_sri_ruc_datos,
            "sri_ruc_contactos": info_dinardap_sri_ruc_contactos,
            "sri_ubicaciones_geograficas": info_dinardap_sri_ubicaciones_geograficas
        }
        cache.set('ruc_data_' + number, json.dumps(toSend), ex=int(redis_live))
        return toSend
    if (len(ruc)>0):
        toSend = {
            "sri_ruc_completo": ruc[0]['sri_ruc_completo'],
            "sri_ruc": ruc[0]['sri_ruc'],
            "sri_establecimientos": ruc[0]['sri_establecimientos'],
            "sri_razon_social": ruc[0]['sri_razon_social'],
            "sri_actividad_economica": ruc[0]['sri_actividad_economica'],
            "sri_ruc_datos": ruc[0]['sri_ruc_datos'],
            "sri_ruc_contactos": ruc[0]['sri_ruc_contactos'],
            "sri_ubicaciones_geograficas": ruc[0]['sri_ubicaciones_geograficas']
        }
        cache.set('ruc_data_' + number, json.dumps(toSend), ex=int(redis_live))
        return toSend
    cache.set('ruc_data_' + number, 'error', ex=int(redis_live_error))
    return 'error'

def get_cedula(number):
    cache_data = cache.get('cedula_data_' + number)
    if (cache_data != None):
        return json.loads(cache_data)
    collection = db['Cedulas']
    filter = {"number": number}
    bdd_info = collection.find(filter)
    cedulas = prepare_mongo_data(bdd_info)
    toReturn = {}
    toReturn['timestamp'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    toReturn['number'] = number
    info_dinardap = get_cedula_data(number)
    if (info_dinardap != 'error'):
        toReturn['data'] = info_dinardap
        if (len(cedulas)>0):
            collection.update_one(filter, {'$set': toReturn})
        else:
            collection.insert_one(toReturn)
        cache.set('cedula_data_' + number, json.dumps(info_dinardap), ex=int(redis_live))
        return info_dinardap
    if (len(cedulas)>0):
        cache.set('cedula_data_' + number, json.dumps(cedulas[0]['data']), ex=int(redis_live))
        return cedulas[0]['data']
    cache.set('cedula_data_' + number, 'error', ex=int(redis_live_error))
    return 'error'

def get_supercias(number):
    cache_data = cache.get('supercias_data_' + number)
    if (cache_data != None):
        return json.loads(cache_data)
    collection = db['Superintendencia_Companias']
    filter = {"ruc": number}
    bdd_info = collection.find(filter)
    supercias = prepare_mongo_data(bdd_info)
    toReturn = {}
    toReturn['timestamp'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    toReturn['ruc'] = number
    info_dinardap_administrador = get_admin_data(number)
    info_dinardap_compania = get_companias_data(number)
    update_obj = False
    if (info_dinardap_compania != 'error'):
        update_obj = True
        toReturn['data_company'] = info_dinardap_compania
    if (info_dinardap_administrador != 'error'):
        update_obj = True
        toReturn['data_admin'] = info_dinardap_administrador
    if (update_obj):
        if (len(supercias)>0):
            collection.update_one(filter, {'$set': toReturn})
        else:
            collection.insert_one(toReturn)
        toSend = {"companias": info_dinardap_compania, "administrador": info_dinardap_administrador}
        cache.set('supercias_data_' + number, json.dumps(toSend), ex=int(redis_live))
        return toSend
    if (len(supercias)>0):
        toSend = {"companias": supercias[0]['data_company'], "administrador": supercias[0]['data_admin']}
        cache.set('supercias_data_' + number, json.dumps(toSend), ex=int(redis_live))
        return toSend
    cache.set('supercias_data_' + number, 'error', ex=int(redis_live_error))
    return 'error'
    
def get_sri_ubicaciones_geograficas(number):
    parameters = [
        {
            "nombre": 'codigoPaquete',
            "valor": '2113'
        },
        {
            "nombre": 'ruc',
            "valor": number
        }
    ]
    return consultar(parameters)
    
def get_sri_ruc(number):
    parameters = [
        {
            "nombre": 'codigoPaquete',
            "valor": '2114'
        },
        {
            "nombre": 'identificacion',
            "valor": number
        },
        {
            "nombre": 'fuenteDatos',
            "valor": ' '
        }
    ]
    return consultar(parameters)
    
def get_sri_ruc_completo(number):
    parameters = [
        {
            "nombre": 'codigoPaquete',
            "valor": '2116'
        },
        {
            "nombre": 'identificacion',
            "valor": number
        },
        {
            "nombre": 'fuenteDatos',
            "valor": ' '
        }
    ]
    return consultar(parameters)
    
def get_sri_establecimientos(number):
    parameters = [
        {
            "nombre": 'codigoPaquete',
            "valor": '2115'
        },
        {
            "nombre": 'identificacion',
            "valor": number
        }
    ]
    return consultar(parameters)
    
def get_sri_actividad_economica(number):
    parameters = [
        {
            "nombre": 'codigoPaquete',
            "valor": '2224'
        },
        {
            "nombre": 'identificacion',
            "valor": number
        }
    ]
    return consultar(parameters)
    
def get_sri_razon_social(number):
    parameters = [
        {
            "nombre": 'codigoPaquete',
            "valor": '2225'
        },
        {
            "nombre": 'identificacion',
            "valor": number
        }
    ]
    return consultar(parameters)
    
def get_sri_ruc_datos(number):
    parameters = [
        {
            "nombre": 'codigoPaquete',
            "valor": '2117'
        },
        {
            "nombre": 'identificacion',
            "valor": number
        }
    ]
    return consultar(parameters)
    
def get_sri_ruc_contactos(number):
    parameters = [
        {
            "nombre": 'codigoPaquete',
            "valor": '2118'
        },
        {
            "nombre": 'identificacion',
            "valor": number
        }
    ]
    return consultar(parameters)

def get_cedula_data(number):
    parameters = [
        {
            "nombre": 'codigoPaquete',
            "valor": '2112'
        },
        {
            "nombre": 'identificacion',
            "valor": number
        }
    ]
    return consultar(parameters)

def get_admin_data(number):
    parameters = [
        {
            "nombre": 'codigoPaquete',
            "valor": '2120'
        },
        {
            "nombre": 'identificacion',
            "valor": number
        }
    ]
    return consultar(parameters)
    
def get_companias_data(number):
    parameters = [
        {
            "nombre": 'codigoPaquete',
            "valor": '2119'
        },
        {
            "nombre": 'identificacion',
            "valor": number
        }
    ]
    return consultar(parameters)
    
def consultar(parameters):
    try:
        session = Session()
        session.auth = HTTPBasicAuth(soap_user, soap_password)
        expireTime = 5
        client = Client(soap_wsdl, transport=Transport(session=session, timeout=expireTime))
        factory = client.type_factory('ns0')
        params = []
        for param in parameters:
            new_param = factory.parametro(nombre=param["nombre"], valor=param["valor"])
            params.append(new_param)
        params = factory.parametros(parametro=params)
        respuesta = client.service.consultar(parametros=params)
        output = helpers.serialize_object(respuesta,dict)
        return output
    except:
        return 'error'

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