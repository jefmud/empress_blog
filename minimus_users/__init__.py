############## Simple user model for applications
# uses SHA256 which is generally robust for producing encrypted/hashed passwords
#
# The only requirements for the user model are a username and a password
#
# exposes:
#
# function { authenticate(username, password) } - looks for an existing username
#          and checks if the password matches the hashed version in the database
#          if it does, it returns True, not, it returns False
# function {initialize(datadir)} - initializes the JSON database in a directory
# function {get_user(username, uid)} - returns a user record from a username
#  or id.  On failure returns None
# function {get_users()} - returns a list of all users
# function {delete_user(username, uid)} - returns a user if it deleted a user
#     identified by username or uid
# function {create_user(username, password, **kwargs)} - creates a user record
#      username, password required -- the only validation is that username does not
#      currently exist.  **kwargs are optional keyword arguments to include in the
#      user record... for example is_active=True, display_name=John Doe
# function { update_user(username, **kwargs) } - add additional keyword arguments
#       to an existing record.  If a keyword argument value is EXPLICITLY set to None
#       the existing key/value will be removed.
#
# The programmer can easily extend this with an update_user
# EXAMPLE of Usage
#  -- see example.py

######## ENCRYPTION SECTION ###############
# establish a simple user model and authentication handling
# encryption inspired by Jose Salvatierra's excellent blog on encrypting password
# https://blog.tecladocode.com/learn-python-encrypting-passwords-python-flask-and-passlib/
#
# should provide a relatively independent user model stored in a JSON file
#
from passlib.context import CryptContext
from minimus import Session
import functools

pwd_context = CryptContext(
        schemes=["pbkdf2_sha256"],
        default="pbkdf2_sha256",
        pbkdf2_sha256__default_rounds=30000
)

def encrypt_password(password):
    return pwd_context.encrypt(password)

def check_encrypted_password(password, hashed):
    return pwd_context.verify(password, hashed)

import os

from .db_client import CLIENT

############ USER MODEL and OPERATIONS ##############
#
# we can fix this later, for now, put userdata JSON in local data dir

_db = None

def initialize(collection='userdata'):
    """initialize(collection='userdata') ==> initializes the database
    : param {collection} : (optional) the collection for users data.

    """
    global _db
    _db = CLIENT.userdata


def get_users():
    """get_users() - return a list of all users JSON records"""
    if _db is None:
        raise ValueError("Database not initialized!")
    return list(_db.users.find())

def get_user(username=None, uid=None):
    """get_user(username, uid) ==> find a user record by uid or username
    : param {username} : - a specific username (string)
    : param {uid} : - a specific user id (string) - note, this is actual '_id' in databse
    : return : a user record or None if not found
    """
    if _db is None:
        raise ValueError("Database not initialized!")
    # first try the username--
    user = None
    if username:
        user = _db.users.find_one({'username': username})
    if uid:
        user = _db.users.find_one({'_id':uid})
    return user

def create_user(username, password, **kwargs):
    """
    create_user(username, password, **kwargs) ==> create a user --
    : param {username} and param {password} : REQUIRED
    : param **kwargs : python style (keyword arguments, optional)
    : return : Boolean True if user successfully created, False if exisiting username
    example
    create_user('joe','secret',display_name='Joe Smith',is_editor=True)
    """
    user = get_user(username=username)
    if user:
        # user exists, return failure
        return False
    # build a user record from scratch
    user = {'username':username, 'password': encrypt_password(password)}
    for key, value in kwargs.items():
        user[key] = value

    _db.users.insert_one(user)
    return True

def update_user(username, **kwargs):
    """
    update_user(username, **kwargs) - update a user record with keyword arguments
    : param {username} : an existing username in the database
    : param **kwargs : Python style keyword arguments.
    : return : True if existing username modified, False if no username exists.
    update a user with keyword arguments
    return True for success, False if fails
    if a keyword argument is EXPLICITLY set to None,
    the argument will be deleted from the record.
    NOTE THAT TinyMongo doesn't implement $unset
    """
    user = get_user(username)
    if user:
        idx = {'_id': user['_id']}
        for key, value in kwargs.items():
            if value is None and key in user:
                # delete the key
                _db.users.update_one(idx, {'$unset': {key:""}} )
            else:
               # user[key] = value
               _db.users.update_one(idx, {'$set': {key:value}} )
        return True
    return False

def delete_user(username=None, uid=None):
    """delete_user(username, uid) deletes a user record by username or uid
    : param {username} : string username on None
    : param {uid} : string database id or None
    : return : returns user record upon success, None if fails
    """
    user = None
    if username:
        user = get_user(username=username)
    if uid:
        user = get_user(uid=uid)
    if user:
        _db.users.remove(user)
    return user

def authenticate(username, password):
    """
    authenticate(username, password) ==> authenticate username, password against datastore
    : param {username} : string username
    : param {password} : string password in plain-text
    : return : Boolean True if match, False if no match
    """
    user = get_user(username)
    if user:
        if check_encrypted_password(password, user['password']):
            return True
    return False

def render_login(login_filename=None):
    """render_login(login_filename=None) returns a login page as a string contained
    login_file if None, then if loads module level file login.html
    : param {login_filename} : string of filename of login page HTML document or None.
    If None, then the package level standard login.html is loaded.
    : return : string HTML of login page
    NOTE: this is an experimental feature
    """
    # use module level 'login.html''
    if login_filename is None:
        moduledir = os.path.dirname(__file__)
        login_filename = os.path.join(moduledir, 'login.html')
    if not isinstance(login_filename, str):
        raise TypeError("ERROR: minmus_users.login_page() - login_filename must be a string")
    with open(login_filename) as fp:
        data = fp.read()
    return data

def user_services_cli(args):
    """command line interface for user services"""
    if '--createuser' in args:
        username = input('Username (required): ')
        realname = input('Real Name: ')
        email = input('Email: ')
        password = input('Password (required):')
        create_user(username, password, realname=realname, email=email)
        return True
        
    if '--deleteuser' in args:
        username = input('Username (required): ')
        delete_user(username)
        return True
        
    if '--listusers' in args:
        users = get_users()
        for user in users:
            print(user)
        return True
    
    if '--updateuser' in args:
        username = input('Username (required): ')
        realname = input('Real Name: ')
        email = input('Email: ')
        password = input('Password (required):')
        update_user(username, password, realname=realname, email=email)
        return True
    
    if len(args) > 1:
        print('user services:')
        print('  --createuser')
        print('  --deleteuser')
        print('  --listusers')
        print('  --updateuser')
        return True
        
    return False