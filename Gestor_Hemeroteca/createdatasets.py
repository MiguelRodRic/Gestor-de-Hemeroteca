from pymongo import MongoClient

cliente = MongoClient()
db = cliente.test_database
datasets = db.datasets
datasets.insert_one({'dataset':'Machismo','clases':{'clase1':'aFavor','clase2':'enContra'}})
datasets.insert_one({'dataset':'VientreAlquiler','clases':{'clase1':'aFavor','clase2':'enContra'}})

print 'datasets iniciales incluidos'
