import os
from tornado.ioloop import IOLoop
from tornado.web import Application, RequestHandler
from tornado.escape import json_decode
from pymongo import MongoClient
import datetime
from bson import json_util
import json
import uuid
import jwt
from dateutil import parser
import random
import string
import mailer
import ldap
from argon2 import PasswordHasher

mongo_bdd = os.getenv('mongo_bdd')
mongo_bdd_server = os.getenv('mongo_bdd_server')
mongo_user = os.getenv('mongo_user')
mongo_password = os.getenv('mongo_password')
app_secret = os.getenv('app_secret')
allowed_app_name = os.getenv('allowed_app_name')
web_url = os.getenv('web_url')
recovery_url = os.getenv('recovery_url')
token_live = os.getenv('token_live')
recovery_token_live = os.getenv('recovery_token_live')
password_length = os.getenv('password_length')
max_login_tries = os.getenv('max_login_tries')
smtp_server = os.getenv('smtp_server')
smtp_port = os.getenv('smtp_port')
smtp_tls = os.getenv('smtp_tls')
smtp_user = os.getenv('smtp_user')
smtp_password = os.getenv('smtp_password')

database_uri='mongodb://'+mongo_user+':'+mongo_password+'@'+ mongo_bdd_server +'/'
client = MongoClient(database_uri)
db = client[mongo_bdd]

catalog = 'users'

class DefaultHandler(RequestHandler):
    def set_default_headers(self):
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Allow-Headers', '*')
        self.set_header('Access-Control-Allow-Methods', '*')

    def get(self):
        self.write({'response':'Servicio de Autenticación Operativo', 'status':200})

class ActionHandler(RequestHandler):
    def set_default_headers(self):
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Allow-Headers', '*')
        self.set_header('Access-Control-Allow-Methods', '*')

    def options(self, action):
        pass
    
    def post(self, action):
        content = json_decode(self.request.body)
        if (action == 'update_user'):
            attribute = content['attribute']
            value = content['value']
            email = content['email']
            userdata = content['userdata']
            respuesta = update_user(attribute, value, email, userdata)
        if (action == 'login'):
            email = content['email']
            password = content['password']
            respuesta = login(email, password)
        if (action == 'register'):
            email = content['email']
            userdata = content['userdata']
            respuesta = register(email, userdata)
        if (action == 'recovery'):
            email = content['email']
            respuesta = recovery(email)
        if (action == 'ldap_auth'):
            email = content['email']
            password = content['password']
            respuesta = ldap_auth(email,password)
        if (action == 'check_by_attribute'):
            attribute = content['attribute']
            value = content['value']
            respuesta = check_by_attribute(attribute, value)
        self.write(respuesta)
        return

class ActionTokenHandler(RequestHandler):
    def set_default_headers(self):
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Allow-Headers', '*')
        self.set_header('Access-Control-Allow-Methods', '*')

    def options(self, action, token):
        pass

    def get(self, action, token):
        if (action == 'reset_password'):
            respuesta = reset_password(token)
        self.write(respuesta)

class AdminUsersActionHandler(RequestHandler):
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
        if (action == 'upload_users'):
            users = content['users']
            respuesta = upload_users(catalog, users)
        if (action == 'upload_users_migration'):
            users = content['users']
            respuesta = upload_users_migration(catalog, users)
        if (action == 'get_user'):
            item_id = content['item_id']
            output_model = content['output_model']
            respuesta = get_user(catalog, item_id, output_model)
        if (action == 'get_users'):
            output_model = content['output_model']
            respuesta = get_users(catalog, output_model)
        if (action == 'update_user_data'):
            item_id = content['item_id']
            userdata = content['userdata']
            respuesta = update_user_data(catalog, item_id, userdata)
        if (action == 'lock_user'):
            item_id = content['item_id']
            respuesta = lock_user(catalog, item_id)
        if (action == 'unlock_user'):
            item_id = content['item_id']
            respuesta = unlock_user(catalog, item_id)
        if (action == 'reset_password_user'):
            item_id = content['item_id']
            respuesta = reset_password_user(catalog, item_id)
        self.write(respuesta)
        return

def update_user(attribute, value, email, userdata):
    collection = db[catalog]
    filter = {}
    filter[attribute] = value
    prev_users = collection.find(filter)
    previous_users = json.loads(json_util.dumps(prev_users))
    if (len(previous_users) == 0):
        return {'response': 'Los datos proporcionados no se encuentran asociado a cuenta alguna', 'status':500}
    else:
        userdata['timestamp'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        password = gen_password()
        userdata['password'] = encrypt_password(password)
        userdata['login_tries'] = 0
        userdata['active'] = True
        userdata['disabled'] = False
        collection.update_one(filter, {'$set':userdata})
        userdata['password'] = password
        send_email_register('Actualización o Recuperación de Cuenta', userdata)
    return {'response': 'Usuario actualizado satisfactoriamente', 'status':200}

def ldap_auth(email,password):
    try:
        ldap_server = os.getenv('ldap_server')
        ldap_protocol = int(os.getenv('ldap_protocol'))
        ldap_port =  os.getenv('ldap_port')
        ldap_email_domain =  os.getenv('ldap_email_domain')
        ldap_base_dn =  os.getenv('ldap_base_dn')
    except:
        return 'Es necesario configurar ldap_server, ldap_protocol, ldap_email_domain, ldap_base_dn y ldap_port'
    try:
        connect = ldap.initialize('ldap://' + ldap_server + ':' + str(ldap_port))    
    except ldap.SERVER_DOWN:
        return 'No se puede conectar al LDAP'
    try:
        user = 'uid=' + email.split(str(ldap_email_domain))[0] + ',' + ldap_base_dn
        connect.set_option(ldap.OPT_REFERRALS, 0)
        connect.set_option(ldap.OPT_PROTOCOL_VERSION, ldap_protocol)
        connect.simple_bind_s(user, password)
        return do_login(email)
    except Exception:
        return {'response': 'Usuario no Autorizado', 'userdata': '', 'token':'', 'status':500}

def do_login(email):
    collection = db[catalog]
    filter = {"email":email}
    users = collection.find(filter)
    for user in users:
        disabled = user['disabled']
        if (disabled == True):
            return {'response': 'La cuenta ha sido bloqueada por el administrador', 'userdata':'', 'token':'', 'status':500}
        update_query = { "$set": { 'login_tries': 0 } }
        collection.update_one(filter, update_query)
        user.pop('password',None)
        user_to_return = json.loads(json_util.dumps(user))
        return {'response':'Usuario Autorizado', 'userdata': user_to_return, 'token':generate_token(), 'status':200}        
    return {'response': 'Usuario no Autorizado', 'userdata': '', 'token':'', 'status':500}

def check_by_attribute(attribute, value):
    collection = db[catalog]
    filter = {}
    filter[attribute] = value
    users = collection.find(filter)
    for user in users:
        return {'response': 'Usuario Encontrado', 'status':200}
    return {'response': 'Usuario No Encontrado', 'status':200}

def login(email, password):
    collection = db[catalog]
    filter = {"email":email}
    users = collection.find(filter)
    for user in users:
        disabled = user['disabled']
        if (disabled == True):
            return {'response': 'La cuenta ha sido bloqueada por el administrador', 'userdata':'', 'token':'', 'status':500}
        active = user['active']
        if (active == False):
            return {'response': 'Ha excedido el número de intentos, la cuenta ha sido bloqueada', 'userdata':'', 'token':'', 'status':500}
        if (verify_password(password, user['password'])):
            update_query = { "$set": { 'login_tries': 0 } }
            collection.update_one(filter, update_query)
            user.pop('password',None)
            user_to_return = json.loads(json_util.dumps(user))
            return {'response':'Usuario Autorizado', 'userdata': user_to_return, 'token':generate_token(), 'status':200}
        else:
            login_tries = int(user['login_tries']) + 1
            if (int(login_tries) < int(max_login_tries)):
                update_query = { "$set": { 'login_tries': login_tries, 'active': True } }
                collection.update_one(filter, update_query)
                return {'response': 'Usuario no Autorizado, Intentos: ' + str(login_tries), 'userdata':'', 'token':'', 'status':500}
            else:
                update_query = { "$set": { 'login_tries': int(max_login_tries), 'active': False } }
                collection.update_one(filter, update_query)
                return {'response': 'Ha excedido el número de intentos, la cuenta ha sido bloqueada', 'userdata':'', 'token':'', 'status':500}            
    return {'response': 'Usuario no Autorizado', 'userdata': '', 'token':'', 'status':500}

def register(email, userdata):
    collection = db[catalog]
    filter = {"email":email}
    prev_users = collection.find(filter)
    previous_users = json.loads(json_util.dumps(prev_users))
    if (len(previous_users)>0):
        return {'response': 'El Correo Electrónico se encuentra asociado a otra cuenta', 'status':500}
    else:
        item_id = str(uuid.uuid4())
        password = gen_password()
        userdata['item_id'] = item_id
        userdata['timestamp'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        userdata['email'] = email
        userdata['password'] = encrypt_password(password)
        userdata['login_tries'] = 0
        userdata['active'] = True
        userdata['disabled'] = False
        collection.insert_one(userdata)
        userdata['password'] = password
        send_email_register('Creación de Cuenta', userdata)
    return {'response': 'Datos Registrados, la Constraseña ha sido enviada al Correo Electrónico', 'status':200}

def upload_users_migration(catalog, users):
    collection = db[catalog]
    log = []
    for user in users:
        item_id = str(uuid.uuid4())
        user['item_id'] = item_id
        user['timestamp'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        user['password'] = encrypt_password(user['password'])
        user['login_tries'] = 0,
        user['active'] = True,
        user['disabled'] = False
        collection.insert_one(user)
        log.append(user)
    toReturn = json.loads(json_util.dumps(log))
    return {'response':toReturn, 'status':200}

def upload_users(catalog, users):
    collection = db[catalog]
    log = []
    for user in users:
        item_id = str(uuid.uuid4())
        user['item_id'] = item_id
        user['timestamp'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        user['password'] = encrypt_password(user['email'])
        user['login_tries'] = 0,
        user['active'] = True,
        user['disabled'] = False
        collection.insert_one(user)
        log.append(user)
    toReturn = json.loads(json_util.dumps(log))
    return {'response':toReturn, 'status':200}

def get_user(catalog, item_id, output_model):
    collection = db[catalog]
    output_model['_id'] = False
    output_model['item_id'] = True
    output_model['timestamp'] = True
    if 'password' in output_model:
        output_model.pop('password',None)
    filter = {"item_id":item_id}
    items = collection.find(filter, output_model)
    items_to_return = json.loads(json_util.dumps(items))
    if (len(items_to_return)>0):
        toReturn = items_to_return[0]
        status = 200
    else:
        toReturn = 'Elemento no encontrado'
        status = 500
    return {'response':toReturn, 'status':status}

def get_users(catalog, output_model):
    collection = db[catalog]
    output_model['_id'] = False
    output_model['item_id'] = True
    output_model['timestamp'] = True
    if 'password' in output_model:
        output_model.pop('password',None)
    items = collection.find({}, output_model)
    items_to_return = json.loads(json_util.dumps(items))
    return {'response':items_to_return, 'status':200}

def update_user_data(catalog, item_id, userdata):
    collection = db[catalog]
    filter = {"item_id":item_id}
    prev_users = collection.find(filter)
    previous_users = json.loads(json_util.dumps(prev_users))
    if (len(previous_users) == 0):
        return {'response': 'Los datos proporcionados no se encuentran asociado a cuenta alguna', 'status':500}
    else:
        userdata['timestamp'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if ('password' in userdata):
            userdata['password'] = encrypt_password(userdata['password'])
        userdata['login_tries'] = 0
        userdata['active'] = True
        userdata['disabled'] = False
        collection.update_one(filter, {'$set':userdata})
    return {'response': 'Usuario actualizado satisfactoriamente', 'status':200}

def recovery(email):
    collection = db[catalog]
    filter = {"email":email}
    prev_users = collection.find(filter)
    previous_users = json.loads(json_util.dumps(prev_users))
    if (len(previous_users)==0):
        return {'response': 'El Correo Electrónico no se encuentra asociado a cuenta alguna', 'status':500}
    else:
        for user in previous_users:
            recovery_token = generate_recovery_token(email)
            send_email_recovery('Recuperación de Cuenta', recovery_token, user)
            return {'response': 'Solicitud de recuperación de cuenta enviada al Correo Electrónico', 'status':200}

def lock_user(catalog, item_id):
    collection = db[catalog]
    filter = {"item_id":item_id}
    prev_users = collection.find(filter)
    previous_users = json.loads(json_util.dumps(prev_users))
    if (len(previous_users) == 0):
        return {'response': 'Los datos proporcionados no se encuentran asociado a cuenta alguna', 'status':500}
    else:
        user = {}
        user['timestamp'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        user['disabled'] = True
        collection.update_one(filter, {'$set':user})
    return {'response': 'Usuario bloqueado satisfactoriamente', 'status':200}

def unlock_user(catalog, item_id):
    collection = db[catalog]
    filter = {"item_id":item_id}
    prev_users = collection.find(filter)
    previous_users = json.loads(json_util.dumps(prev_users))
    if (len(previous_users) == 0):
        return {'response': 'Los datos proporcionados no se encuentran asociado a cuenta alguna', 'status':500}
    else:
        user = {}
        user['timestamp'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        user['disabled'] = False
        collection.update_one(filter, {'$set':user})
    return {'response': 'Usuario desbloqueado satisfactoriamente', 'status':200}

def reset_password_user(catalog, item_id):
    collection = db[catalog]
    filter = {"item_id":item_id}
    prev_users = collection.find(filter)
    previous_users = json.loads(json_util.dumps(prev_users))
    if (len(previous_users) == 0):
        return {'response': 'Los datos proporcionados no se encuentran asociado a cuenta alguna', 'status':500}
    else:
        password = gen_password()
        user = {}
        user['timestamp'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        user['password'] = encrypt_password(password)
        user['active'] = True
        user['login_tries'] = 0
        user['disabled'] = False
        collection.update_one(filter, {'$set':user})
        for user in previous_users:
            user['password'] = password
            send_email_reset('Reseteo de Contraseña', user)
        return {'response': 'Contraseña enviada al Correo Electrónico', 'status':200} 

def reset_password(token):
    collection = db[catalog]
    validation = validate_token(token)
    if (validation['status'] == 500):
        return validation
    password = gen_password()
    data = validation['response']
    filter = {"email":data['email']}
    prev_users = collection.find(filter)
    previous_users = json.loads(json_util.dumps(prev_users))
    if (len(previous_users)==0):
        return {'response': 'El Correo Electrónico no se encuentra asociado cuenta alguna', 'status':500}
    else:
        update_query = { "$set": { 'password': encrypt_password(password), 'active': True, 'login_tries': 0 } }
        collection.update_one(filter, update_query)
        for user in previous_users:
            user['password'] = password
            send_email_reset('Reseteo de Contraseña', user)
            return {'response': 'Contraseña enviada al Correo Electrónico', 'status':200} 

def gen_password(chars = string.ascii_uppercase + string.digits + string.ascii_lowercase, N=password_length):
	return ''.join(random.choice(chars) for _ in range(int(N)))

def generate_token():
    exp_time = datetime.datetime.now() + datetime.timedelta(minutes=int(token_live))
    payload = { 'app_name':allowed_app_name, 'valid_until': str(exp_time) }
    return jwt.encode(payload, app_secret, algorithm='HS256')

def encrypt_password(password):
    ph = PasswordHasher()
    pswd = ph.hash(password)
    return jwt.encode({'password': pswd}, app_secret, algorithm='HS256')

def verify_password(password, password_bdd):
    ph = PasswordHasher()
    to_verify = jwt.decode(password_bdd, app_secret, algorithms=['HS256'])
    try:
        return ph.verify(to_verify['password'], password)
    except:
        return False
    
def generate_recovery_token(email):
    exp_time = datetime.datetime.now() + datetime.timedelta(minutes=int(recovery_token_live))
    payload = { 'app_name':allowed_app_name, 'valid_until': str(exp_time), 'email': email}
    return jwt.encode(payload, app_secret, algorithm='HS256')

def validate_token(token):
    try:
        data = jwt.decode(token, app_secret, algorithms=['HS256'])
        exp_time = parser.parse(data['valid_until'])
        app_name = data['app_name']
        if (app_name == allowed_app_name):
            if (datetime.datetime.now() < exp_time):
                return {'response':data, 'status':200}
            else:
                return {'response':'Token Expirado', 'status':500}
        else:
            return {'response':'Token Erroneo', 'status':500}
    except:
        return {'response':'Token Erroneo', 'status':500}

def send_email_register(subject, user):
    params = user
    params['app_name']=allowed_app_name
    params['web_url']=web_url
    to = [user['email']]
    template = 'register_account.html'
    if (subject == 'Actualización o Recuperación de Cuenta'):
        template = 'update_account.html'
    mailer.send_mail(
        smtp_server,
        smtp_port,
        int(smtp_tls),
        smtp_user,
        smtp_password,
        allowed_app_name,
        to,
        subject,
        template,
        params,
        [])

def send_email_recovery(subject, recovery_token, user):
    params = user
    params['token'] = recovery_token
    params['app_name']=allowed_app_name
    params['web_url']=web_url
    params['recovery_url']=recovery_url
    to = [user['email']]
    mailer.send_mail(
        smtp_server,
        smtp_port,
        int(smtp_tls),
        smtp_user,
        smtp_password,
        allowed_app_name,
        to,
        subject,
        'password_recovery.html',
        params,
        [])

def send_email_reset(subject, user):
    params = user
    params['app_name']=allowed_app_name
    params['web_url']=web_url
    to = [user['email']]
    mailer.send_mail(
        smtp_server,
        smtp_port,
        int(smtp_tls),
        smtp_user,
        smtp_password,
        allowed_app_name,
        to,
        subject,
        'reset_password.html',
        params,
        [])

def make_app():
    urls = [
        ("/", DefaultHandler),
        ("/([^/]+)", ActionHandler),
        ("/([^/]+)/([^/]+)", ActionTokenHandler),
        ("/admin/users/([^/]+)", AdminUsersActionHandler)
    ]
    return Application(urls, debug=True)
  
if __name__ == '__main__':
    app = make_app()
    app.listen(5050)
    IOLoop.instance().start()