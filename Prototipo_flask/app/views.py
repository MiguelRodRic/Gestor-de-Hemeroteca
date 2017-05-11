# -*- coding: utf-8 -*-
from flask import render_template, flash, redirect, request
from pymongo import MongoClient
from app import app
from flask_pymongo import PyMongo
from .forms import LoginForm, ScanPDF, RssScrapping, Query
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

mongo = PyMongo(app)
cliente = MongoClient()
db = cliente.test_database

ruta = ConfigVars.pdfpath
ficheros = []
nombres = []
listaNoticias = []

def lookForPdf(path):
	for filename in os.listdir(path):
		if filename.endswith(".pdf"):
			ficheros.append(os.path.join(path,filename))
			nombres.append(filename)
			#print filename
		elif "." not in filename:
			newPath = os.path.join(path,filename)
			lookForPdf(newPath)


@app.route('/')
@app.route('/index', methods=['GET','POST'])
def index():
	query = Query()
	ejemplo = ''
	noticiasSample = []
	if request.method == 'POST':
		result = request.form.get('search')
		for sample in db.noticias.find({'text':{'$regex': ".*"+result+".*"}}).limit(20):
			if 'tag' in sample.keys():
				etiqueta = sample['tag']
			else:
				etiqueta = ''
			noticiasSample.append({'titular':sample['title'], 'autor':sample['author'], 'fecha':sample['publishDate'], 'fuente':sample['source'], 'tag':etiqueta})
		for titular in db.noticias.find( {'title':1}):
			if request.form[titular] == "Clasificar":
				ejemplo = titular
		return render_template("index.html",
						   title='Home',
						   query=query,
						   noticiasSample=noticiasSample,
						   ejemplo=ejemplo)
	return render_template("index.html",
						   title='Home',
						   query=query,
						   noticiasSample=noticiasSample,
						   ejemplo=ejemplo)


@app.route('/scanpdf', methods=['GET','POST'])
def scanpdf():
	scan = ScanPDF()
	if request.method == 'POST':
		mostrar = 'Si'
		if request.form['submit'] == "Aceptar":
			del ficheros[:]
			del nombres[:]
			del scan.noticias[:]
			lookForPdf(ruta)
			textos = [None]*len(ficheros)
			autores =[None]*len(ficheros)
			fechas = [None]*len(ficheros)
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
					fp = file(pdfLocal, 'rb')
					parser = PDFParser(fp)
					doc = PDFDocument(parser)
					#print str(doc.info).decode().encode('utf-8')
					fechaAux = doc.info[0].get('CreationDate', None)
					fechas[ficheros.index(registro)] = fechaAux[2:6]+'-'+fechaAux[6:8]+'-'+fechaAux[8:10]+' '+fechaAux[10:12]+':'+fechaAux[12:14]+':'+fechaAux[14:16]
					autores[ficheros.index(registro)] = doc.info[0].get('Author', None)
					YaAlmacenada = 'No'
					interpreter = PDFPageInterpreter(rsrcmgr, device)
					password = ""
					maxpages = 0
					caching = True
					pagenos=set()
					for page in PDFPage.get_pages(fp, pagenos, maxpages=maxpages, password=password,caching=caching, check_extractable=True):
						interpreter.process_page(page)
					text = retstr.getvalue()
					textos[ficheros.index(registro)] = text
					
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
					autoraux = autores[ficheros.index(registro)].decode('utf-16')
				except:
					autoraux = autores[ficheros.index(registro)]
				scan.noticias.append({'texto':textos[ficheros.index(registro)],
				 'autor':autoraux,
				 'fecha':fechas[ficheros.index(registro)],
				 'titular':nombres[ficheros.index(registro)], 'almacenada':YaAlmacenada})
			return render_template("scanpdf.html",
							   scan=scan,
							   mostrar=mostrar)
		elif request.form['submit'] == "Guardar Nuevas":
			for noticia in scan.noticias:
					db.noticias.update_one( {'title':noticia['titular']},{ '$set': {'author': noticia['autor'], 'title':noticia['titular'],
					'publishDate':noticia['fecha'], 'text':noticia['texto'], 'source':'PDF'}}, upsert=True)
			return render_template("scanpdf.html", scan=scan, mostrar=mostrar)
	return render_template("scanpdf.html",
						   scan=scan)

@app.route('/websearch', methods=['GET', 'POST'])
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
				fuente ='ElMundo'
			titulares = []
			textos = []
			fechas = []
			autores = []
			if(etiqueta != None):
				for entry in textRSS['entries']:
					try:
						soup = BeautifulSoup(entry[etiqueta], "lxml")
						titulares.append(entry['title'])
						fechas.append(entry['published'])
						autores.append(entry['author'])
						if(fuente != 'ElMundo'):
							textos.append(soup.text)
						else:
							noticiaSoup = feedparser.parse(entry['links'][0]['href'])
							if(BeautifulSoup(noticiaSoup['feed']['summary'])):
								noticiaSoup = BeautifulSoup(noticiaSoup['feed']['summary'])
							if(noticiaSoup.find('article')):
								textos.append(noticiaSoup.find('article').text)
					except Exception as e:
						errorText = str(e)
						pass
				for titular in titulares:
					indice = titulares.index(titular)
					autor = autores[indice]
					fecha = fechas[indice]
					texto = textos[indice].encode('utf-8').decode('utf-8')
					incluida = db.noticias.find_one({'title':{'$regex': titular}})
					almacenada = ''
					if incluida == None:
						almacenada = 'No'
					else:
						almacenada = 'Si'
					noticia = { 'author': autor, 'title':titular,
								'publishDate':fecha, 'text':texto, 'source':'RSS', 'almacenada':almacenada}
					rssWS.noticias.append(noticia)
				return render_template('websearch.html', 
									   title='Web Scrapping',
									   rssWS = rssWS,
									   options=options,
									   etiqueta=etiqueta,
									   fuente=fuente)
		if request.form['submit'] == "Guardar Nuevas":
			for noti in rssWS.noticias:
				db.noticias.update_one( {'title':noti['title']},{ '$set': {'author': noti['author'], 'title':noti['title'],
						'publishDate':noti['publishDate'], 'text':noti['text'], 'source':noti['source']}}, upsert=True)
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



# index view function suppressed for brevity

@app.route('/login', methods=['GET', 'POST'])
def login():
	form = LoginForm()
	return render_template('login.html', 
						   title='Sign In',
						   form=form)