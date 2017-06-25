from pymongo import MongoClient

cliente = MongoClient()
db = cliente.test_database

result = db.noticias.update_many({'tag.Dataset':{'$exists':True}},{'$unset': {'tag.Dataset':''}})

if result.modified_count > 0:
	print 'Borrado dataset de las noticias'

resultds = db.datasets.delete_one({'dataset':'Dataset'})

if resultds.deleted_count > 0:
	print 'Borrado dataset del resto de datasets'