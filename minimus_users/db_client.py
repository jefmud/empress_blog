# db client
import pymongo

USE_MONTY_DB = False

if USE_MONTY_DB:
    import montydb
    client_str = 'montydb'
    montydb.set_storage(client_str, cache_modified=0)
    CLIENT = montydb.MontyClient(client_str)
else:
    client_str = 'mongodb://localhost:27017'
    
    CLIENT = pymongo.MongoClient(client_str)