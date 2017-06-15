# -*- coding: utf-8 -*-
from flask import render_template, flash, redirect, request, Markup
from flask_breadcrumbs import Breadcrumbs, register_breadcrumb
from pymongo import MongoClient
from bson.objectid import ObjectId
from app import app
from flask_pymongo import PyMongo
from .forms import ScanPDF, RssScrapping, Query, NewDataSet, CreateDataset
from config import ConfigVars
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from cStringIO import StringIO
from bs4 import BeautifulSoup
from wtforms import SubmitField
import os
import feedparser
import sys
import urllib2
import collections

mongo = PyMongo(app)
cliente = MongoClient()
db = cliente.test_database

rutapdf = ConfigVars.pdfpath
rutadataset = ConfigVars.datasetpath

ficheros = []
nombres = []
listaNoticias = []
amountNoticias = 0


def lookForFile(path, extension):
	for filename in os.listdir(path):
		if filename.endswith(extension):
			ficheros.append(os.path.join(path,filename))
			nombres.append(filename)
			#print filename
		elif os.path.isdir(filename):
				newPath = os.path.join(path,filename)
				lookForFile(newPath, extension)




@app.route('/')
@app.route('/index/', methods=['GET','POST'])
@register_breadcrumb(app, '.', 'Inicio')
def index():
	query = Query()
	ejemplo = ''
	etiquetas = []
	clases = {}
	for dataset in db.datasets.find({}):
			etiquetas.append(dataset['dataset'])
			clases[dataset['dataset']] = [dataset['clases']['clase1'], dataset['clases']['clase2']]
	if request.method == 'POST':
		if request.form['submit'] == 'Buscar':
			del query.noticiasSample[:]
			result = query.search.data
			resultNoticias = db.noticias.find({'text':{'$regex': ".*"+result+".*"}})
			amountNoticias = resultNoticias.count()/5
			for sample in db.noticias.find({'text':{'$regex': ".*"+result+".*"}}).limit(5):
				prediction = []
				predictTag = {}
				savedTag = {}
				mensaje = ''
				for tag in etiquetas:
					if sample['tag'][tag] != '':
						savedTag[tag] = sample['tag'][tag]
					else:
						savedTag[tag] = None
					pred = query.classification(sample['_id'], tag)
					if type(pred) is not str:
						prediction.append(pred)
						if pred['aFavor'] > 0.5:
							predictTag[tag] = 'aFavor'
						else:
							predictTag[tag] = 'enContra'
					else:
						mensajeError = pred
						prediction.append(None)
						predictTag[tag] = None
				try:
					link = sample['link']
				except:
					link = ''
				query.noticiasSample.append({'id':str(sample['_id']), 'titular':sample['title'], 'autor':sample['author'],
				 'fecha':sample['publishDate'], 'fuente':sample['source'], 'predict': prediction, 'predictTag':predictTag, 'savedTag':savedTag, 'link':link, 'mensaje':mensaje})
			return render_template("index.html",
						   title='Home',
						   query=query,
						   noticiasSample=query.noticiasSample,
						   etiquetas=etiquetas,
						   clases = clases,
						   amountNoticias=amountNoticias)
		elif request.form['submit'] == 'Guardar Cambios':
			tag = request.form.get('datasetSelect')
			tagToUpdate = "tag."+str(tag)
			mensaje = ''
			for noticiatoUpdate in query.noticiasSample:
				if request.form.get(str(noticiatoUpdate['id'])) != None:
					update_result = db.noticias.update_one({"_id":ObjectId(noticiatoUpdate['id'])},{'$set':{tagToUpdate:request.form.get(noticiatoUpdate['id'])}})
					if update_result.modified_count > 0:
						mensaje = 'Noticias Actualizadas'
			if mensaje == '':
				mensaje = 'No se ha actualizado ninguna noticia'
			return render_template("index.html",
						   title='Home',
						   mensaje=mensaje)
		else:
			del query.noticiasSample[:]
			result = query.search.data
			resultNoticias = db.noticias.find({'text':{'$regex': ".*"+result+".*"}})
			amountNoticias = resultNoticias.count()/5
			page = int(request.form['submit'])
			for sample in db.noticias.find({'text':{'$regex': ".*"+result+".*"}}).skip(page*5).limit(5):
				prediction = []
				predictTag = {}
				savedTag = {}
				mensaje = ''
				for tag in etiquetas:
					if sample['tag'][tag] != '':
						savedTag[tag] = sample['tag'][tag]
					else:
						savedTag[tag] = None
					pred = query.classification(sample['_id'], tag)
					if type(pred) is not str:
						prediction.append(pred)
						if pred['aFavor'] > 0.5:
							predictTag[tag] = 'aFavor'
						else:
							predictTag[tag] = 'enContra'
					else:
						mensajeError = pred
						prediction.append(None)
						predictTag[tag] = None
				try:
					link = sample['link']
				except:
					link = ''
				query.noticiasSample.append({'id':str(sample['_id']), 'titular':sample['title'], 'autor':sample['author'],
				 'fecha':sample['publishDate'], 'fuente':sample['source'], 'predict': prediction, 'predictTag':predictTag, 'savedTag':savedTag, 'link':link, 'mensaje':mensaje})
			return render_template("index.html",
						   title='Home',
						   query=query,
						   noticiasSample=query.noticiasSample,
						   etiquetas=etiquetas,
						   clases = clases,
						   amountNoticias=amountNoticias,
						   page=page)
	return render_template("index.html",
						   title='Home',
						   query=query)

@app.route('/statistics/', methods=['GET','POST'])
def statistics():
	resultNoticias = db.noticias.find({})
	autores = []
	fechas = []
	fuentes = []
	for noticia in resultNoticias:
		autores.append(noticia['author'])
		fechas.append(noticia['publishDate'])
		fuentes.append(noticia['source'])
	autores = collections.Counter(autores)
	fechas = collections.Counter(fechas)
	fuentes = collections.Counter(fuentes)
	return render_template("statistics.html",
						   title='Statistics',
						   autores=autores,
						   fechas=fechas,
						   fuentes=fuentes)


@app.route('/explanation/<string:arguments>', methods=['GET','POST'])
@register_breadcrumb(app, '.Explicacion', 'Explicacion')
def explanation(arguments):
	query = Query()
	arguments_splitted = arguments.split('-')
	auxid = arguments_splitted[0]
	dataset = arguments_splitted[1]
	prediction = arguments_splitted[2]
	mensaje = None
	resultHTML = None
	resultsList = None
	if prediction == 'aFavor':
		prediction = 'A Favor'
	if prediction == 'enContra':
		prediction = 'En Contra'
	if (len(arguments_splitted) == 4):
		tagToUpdate = "tag."+dataset
		update_result = db.noticias.update_one({"_id":ObjectId(auxid)},{'$set':{tagToUpdate:prediction}})
		mensaje = ''
		if update_result.modified_count > 0:
					mensaje = 'Noticia Actualizada'
		if mensaje == '':
			mensaje = 'No se ha actualizado la noticia'

	else:
		results = query.explanation(auxid, dataset)
		resultHTML = Markup(results['html'])
		resultsList = results['list']
	return render_template("explanation.html",
						   title='Explanation',
						   auxid=auxid,
						   query=query,
						   prediction=prediction,
						   dataset=dataset,
						   resultHTML=resultHTML,
						   mensaje=mensaje,
						   resultsList = resultsList)

	
	if request.method == 'POST':
		if request.form['submit'] == 'Guardar Resultado':
			
			return render_template("explanation.html",
						   title='Explanation',
						   query=query,
						   dataset=dataset,
						   mensaje=mensaje)
	# labels = []
	# relevances = []
	# for result in results['list']:
	#  	labels.append(result[0])
	#  	relevances.append(result[1])
	# resultsList = { 'etiquetas': labels, 'importancias': relevances}
	

@app.route('/createdataset', methods=['GET','POST'])
@register_breadcrumb(app, '.Nuevo Dataset', 'Nuevo Dataset')
def createdataset():
	createDS = CreateDataset()
	if request.method == 'POST':
		if request.form['submit'] == "Guardar Dataset":
			db.datasets.insert_one({'dataset':createDS.nombredataset.data,'clases':{'clase1':createDS.clase1.data,'clase2':createDS.clase2.data}})
			for noticia in db.noticias.find({}):
				db.noticias.update_one({'_id':noticia.get('_id')}, {'$set':{'tag.'+createDS.nombredataset.data:''}})
			mensaje = 'Dataset Incluido'
			return render_template("createdataset.html",
									createDS=createDS,
									mensaje=mensaje)
	return render_template("createdataset.html",
							createDS=createDS)


@app.route('/scanpdf', methods=['GET','POST'])
@register_breadcrumb(app, '.Lectura PDF', 'Lectura PDF')
def scanpdf():
	scan = ScanPDF()
	return render_template("scanpdf.html",
						   scan=scan)

@app.route('/savepdfnews', methods=['GET', 'POST'])
@register_breadcrumb(app, '.Resultados PDF', 'Resultados PDF')
def savepdfnews():
	scan = ScanPDF()
	mostrar = 'Si'
	del ficheros[:]
	del nombres[:]
	del scan.noticias[:]
	del nombres[:]
	lookForFile(rutapdf, '.pdf')
	textos = [None]*len(ficheros)
	autores = [None]*len(ficheros)
	fechas = [None]*len(ficheros)
	mensaje = None
	if(len(ficheros)) > 0:
		for registro in ficheros:
			consulta = db.noticias.find_one({'title':{'$regex': nombres[ficheros.index(registro)]}})
			YaAlmacenada = ''
			if consulta == None:
				rsrcmgr = PDFResourceManager()
				retstr = StringIO()
				codec = 'utf-8'
				laparams = LAParams()
				device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)
				pdfLocal = registro
				fp = open(pdfLocal, 'rb')
				parser = PDFParser(fp)
				doc = PDFDocument(parser)
				#print str(doc.info).decode().encode('utf-8')
				YaAlmacenada = 'No'
				interpreter = PDFPageInterpreter(rsrcmgr, device)
				password = ""
				maxpages = 0
				caching = True
				pagenos=set()
				for page in PDFPage.get_pages(fp, pagenos, maxpages=maxpages, password=password,caching=caching, check_extractable=True):
					interpreter.process_page(page)
				text = retstr.getvalue()
				try:
					textos[ficheros.index(registro)] = text.split("(Cuerpo)")[1].decode('utf-8','ignore')
				except:
					mensaje.append('\n No se ha encontado el texto de la noticia')
				try:
					autores[ficheros.index(registro)] = text.split("(Autor)")[1].decode('utf-8','ignore')
				except:
					mensaje.append('\n No se ha encontado el autor de la noticia')
				try:
					fechas[ficheros.index(registro)] = text.split("(Fecha)")[1].decode('utf-8','ignore')
				except:
					mensaje.append('\n No se ha encontado la fecha de la noticia')
				try:
					nombres[ficheros.index(registro)] = text.split("(Titular)")[1].decode('utf-8','ignore')
				except:
					mensaje.append('\n No se ha encontado el titular de la noticia')

				fp.close()
				device.close()
				retstr.close()
			else:
				fechas[ficheros.index(registro)] = consulta['publishDate']
				autores[ficheros.index(registro)] = consulta['author']
				nombres[ficheros.index(registro)] = consulta['title']
				textos[ficheros.index(registro)] = consulta['text']
				YaAlmacenada = 'Si'
			try:
				autoraux = autores[ficheros.index(registro)]
			except:
				autoraux = autores[ficheros.index(registro)].decode('utf-16')
			scan.noticias.append({'texto':textos[ficheros.index(registro)],
			 'autor':autoraux,
			 'fecha':fechas[ficheros.index(registro)],
			 'titular':nombres[ficheros.index(registro)],
			 'almacenada':YaAlmacenada,
			 'link':ficheros[ficheros.index(registro)]})
	else:
		mensaje = 'No se han encontrado archivos'
	if request.method == 'POST':
		if request.form['submit'] == "Guardar Nuevas":
			mensaje = "Noticias insertadas"
			for noticia in scan.noticias:
					db.noticias.update_one( {'title':noticia['titular']},{ '$set': {'author': noticia['autor'],
					 'title':noticia['titular'], 'publishDate':noticia['fecha'], 'text':noticia['texto'],
					  'link':noticia['link'], 'source':'PDF', 'tag':{'Machismo':'', 'VientreAlquiler':''} }}, upsert=True)
			return render_template("savepdfnews.html", scan=scan, mostrar=mostrar, mensaje=mensaje)
	return render_template("savepdfnews.html",
					   scan=scan,
					   mostrar=mostrar,
					   mensaje=mensaje)
	

@app.route('/websearch', methods=['GET', 'POST'])
@register_breadcrumb(app, '.Busqueda RSS', 'Busqueda RSS')
def websearch():
	errorText = 'Todo Bien'
	rssWS = RssScrapping()
	options = [
		{ 
			'name': 'El Pais',
			'value': 'ElPais'
		},
		{ 
			'name': 'El Mundo', 
			'value': 'ElMundo'
		},
		{ 
			'name': 'ElDiario',
			'value': 'ElDiario' 
		},
		{ 
			'name': 'Publico',
			'value': 'Publico'
		}
	]
	etiqueta = None
	fuente = None
	if request.method == 'POST':
		if request.form['submit'] == "Aceptar":
			del rssWS.noticias[:]
			select = request.form.get('media-select')
			global textRSS
			if(select == u'ElDiario'):
				textRSS = feedparser.parse('http://www.eldiario.es/rss/')
				etiqueta = 'summary'
				fuente = 'ElDiario'
			elif (select == u'ElPais'):
				textRSS = feedparser.parse('http://ep00.epimg.net/rss/elpais/portada.xml')
				etiqueta = 'summary'
				fuente = 'El Pais'
			elif (select == u'Publico'):
				textRSS = feedparser.parse('http://www.publico.es/rss/')
				#print textRSS['entries'][1]['summary_detail']['value']
				etiqueta = 'description'
				fuente = 'Publico'
			elif(select == u'ElMundo'):
				textRSS = feedparser.parse('http://www.elmundo.es/rss/portada.xml')
				etiqueta = 'summary'
				fuente ='El Mundo'
			titulares = []
			textos = []
			fechas = []
			autores = []
			links = []
			if(etiqueta != None):
				if textRSS['entries'] > 15:
					top = 15
				else:
					top = len(textRSS['entries'])	
				for entry in textRSS['entries'][0:top]:
					try:
						soup = BeautifulSoup(entry[etiqueta], "lxml")
						titulares.append(entry['title'])
						fechas.append(entry['published'])
						autores.append(entry['author'])
						links.append(entry['links'][0]['href'])
						requestURL = urllib2.Request(entry['links'][0]['href'])
						handle = urllib2.urlopen(requestURL)
						html = handle.read()
						noticiaSoup = BeautifulSoup(html, 'html.parser')
						for expendable in noticiaSoup(['style', 'script', '[document]', 'head', 'title']):
							expendable.extract()
						if noticiaSoup.find("article"):
							textos.append(noticiaSoup.find("article").text)
						else:
							textos.append(noticiaSoup.getText())
					except Exception as e:
						errorText = str(e)
						pass
				for titular in titulares:
					try:
						indice = titulares.index(titular)
						autor = autores[indice]
						fecha = fechas[indice]
						link = links[indice]
						texto = textos[indice].encode('utf-8').decode('utf-8')
						incluida = db.noticias.find_one({'title':{'$regex': titular}})
						almacenada = ''
						if incluida == None:
							almacenada = 'No'
						else:
							almacenada = 'Si'
						noticia = { 'author': autor, 'title':titular, 'link':link,
									'publishDate':fecha, 'text':texto, 'source':fuente, 'almacenada':almacenada}
						rssWS.noticias.append(noticia)
					except Exception as e:
						errorText = str(e)
						pass					
				return render_template('websearch.html', 
									   title='Web Scrapping',
									   rssWS = rssWS,
									   options=options,
									   etiqueta=etiqueta,
									   fuente=fuente,
									   errorText=errorText)
		if request.form['submit'] == "Guardar Nuevas":
			for noti in rssWS.noticias:
				db.noticias.update_one( {'title':noti['title']},{ '$set': {'author': noti['author'], 'title':noti['title'],
						'publishDate':noti['publishDate'], 'text':noti['text'],'link':noti['link'], 'source':noti['source'], 'tag':{'Machismo':'','VientreAlquiler':''}}}, upsert=True)
			mensaje = 'Se han incluido en base de datos'
			return render_template('websearch.html', 
								   title='Web Scrapping',
								   rssWS = rssWS,
								   options=options,
								   etiqueta=etiqueta,
								   fuente=fuente,
								   mensaje=mensaje)
	return render_template('websearch.html', 
						   title='Web Scrapping',
						   rssWS = rssWS,
						   options=options)


@app.route('/newdataset', methods=['GET', 'POST'])
@register_breadcrumb(app, '.Lectura Dataset', 'Lectura Dataset')
def newdataset():
	return render_template('newdataset.html')

@app.route('/savenewdataset', methods=['GET', 'POST'])
@register_breadcrumb(app, '.Resultados Dataset', 'Resultados Dataset')
def savenewdataset():
	nds = NewDataSet()
	del nombres[:]
	del nds.noticias[:]
	titulares = []
	textos = []
	fechas = []
	autores = []
	links = []
	lookForFile(rutadataset,'.xml')
	#get all the links from the xml
	for nombre in nombres:
		soup = BeautifulSoup(open(rutadataset + '/' + nombre,'r'),'xml')
		for root in soup.find_all('root'):
			for topic in root.find_all('dataset'):
				for noticiasxml in topic.find_all('noticias'):
					for noticiaxml in noticiasxml.find_all('noticia'):
						try:
							requestURL = urllib2.Request(noticiaxml.link.text)
							handle = urllib2.urlopen(requestURL)
							html = handle.read()
							noticiaSoup = BeautifulSoup(html, 'html.parser')
							for expendable in noticiaSoup(['style', 'script', '[document]', 'head', 'title']):
								expendable.extract()
							if noticiaSoup.find("article"):
								textos.append(noticiaSoup.find("article").text)
							else:
								textos.append(noticiaSoup.getText())
							noticia = {
								'fecha':noticiaxml.fecha.text,
								'autor':noticiaxml.autor.text,
								'titular':noticiaxml.titular.text,
								'link':noticiaxml.link.text,
								'texto':noticiaSoup.getText(),
								'tag':topic['topic']+ ' - ' + noticiasxml['clase']
							}
							nds.noticias.append(noticia)
						except Exception as e:
							pass
	mostrar = True
	return render_template('savenewdataset.html',mostrar = mostrar, nds = nds)
	if request.form['submit'] == 'Guardar Nuevas':
		for noticia in nds.noticias:
			db.noticias.update_one( {'title':noti['title']},{ '$set': {'author': noti['author'], 'title':noti['title'],
					'publishDate':noti['publishDate'], 'text':noti['text'], 'source':noti['source'], 'tag': {'Machismo':'','VientreAlquiler':''}}}, upsert=True)
		return render_template('savenewdataset.html',mostrar = mostrar, nds = nds)

# index view function suppressed for brevity



if __name__ == '__main__':
	app.run(host = '0.0.0.0', port = 5000)