from flask import render_template, flash, redirect, request
from pymongo import MongoClient
from app import app
from flask.ext.pymongo import PyMongo
from .forms import LoginForm, ScanPDF, RssScrapping, Query
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from cStringIO import StringIO
from bs4 import BeautifulSoup
import os
import feedparser

mongo = PyMongo(app)
cliente = MongoClient()
db = cliente.test_database

ruta = '/home/miguel/Escritorio/Prototype_flask/pdf'
ficheros = []
nombres = []

def lookForPdf(path):
	for filename in os.listdir(path):
		if filename.endswith(".pdf"):
			ficheros.append(path + '/' + filename)
			nombres.append(filename.replace(".pdf",""))
			#print filename
		elif "." not in filename:
			lookForPdf(path+'/'+filename)

@app.route('/')
@app.route('/index', methods=['GET','POST'])
def index():
	query = Query()
	noticiasSample = []
	if request.method == 'POST':
		result = request.form.get('search')
		for sample in db.noticias.find({'text':{'$regex': ".*"+result+".*"}}).limit(20):
			noticiasSample.append({'titular':sample['title'], 'autor':sample['author'], 'fecha':sample['publishDate'], 'fuente':sample['source']})
		
	return render_template("index.html",
						   title='Home',
						   query=query,
						   noticiasSample=noticiasSample)


@app.route('/scanpdf', methods=['GET','POST'])
def scanpdf():
	scan = ScanPDF()
	if request.method == 'POST':
		del scan.noticias[:]
		mostrar = 'Si'
		lookForPdf(ruta)
		textos = [None]*len(ficheros)
		autores =[None]*len(ficheros)
		fechas = [None]*len(ficheros)
		for registro in ficheros:
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
			interpreter = PDFPageInterpreter(rsrcmgr, device)
			password = ""
			maxpages = 0
			caching = True
			pagenos=set()
			for page in PDFPage.get_pages(fp, pagenos, maxpages=maxpages, password=password,caching=caching, check_extractable=True):
				interpreter.process_page(page)
			text = retstr.getvalue()
			textos[ficheros.index(registro)] = text
			scan.noticias.append({'autor':autores[ficheros.index(registro)].decode('utf-16'), 'fecha':fechas[ficheros.index(registro)]})
			fp.close()
			device.close()
			retstr.close()
		return render_template("scanpdf.html",
						   scan=scan,
						   mostrar=mostrar)
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
	select = request.form.get('media-select')
	global textRSS
	etiqueta = None
	fuente = None
	noticias = []
	if(select == u'ElDiario'):
		textRSS = feedparser.parse('http://www.eldiario.es/rss/')
		etiqueta = 'summary'
		fuente = 'ElDiario'
	elif (select == u'ElPais'):
		textRSS = feedparser.parse('http://ep00.epimg.net/rss/sociedad/portada.xml')
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
			noticia = { 'author': autor, 'title':titular,
						'publishDate':fecha, 'text':texto, 'source':'RSS'}
			noticias.append(noticia)
		return render_template('websearch.html', 
							   title='Web Scrapping',
							   rssWS = rssWS,
							   options=options,
							   etiqueta=etiqueta,
							   fuente=fuente,
							   noticias=noticias,
							   errorText=errorText)
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