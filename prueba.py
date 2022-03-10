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

def try_ldap_bind(email, password):
    ldap_server = '192.168.20.10'
    user= 'cn=' + email + ',ou=people,dc=turismo,dc=gob,dc=ec'
    try:
        connect = ldap.initialize('ldap://' + ldap_server + ':389')
    except ldap.SERVER_DOWN:
        return 'No se puede conectar al LDAP'
    try:
        connect.set_option(ldap.OPT_REFERRALS, 0)
        connect.set_option(ldap.OPT_PROTOCOL_VERSION, 3)
        connect.simple_bind_s(user, password)
        return 'Validado'
    except Exception as e:
        return str(e)

print(try_ldap_bind('luis.salazar@turismo.gob.ec', '1509Charles*'))
