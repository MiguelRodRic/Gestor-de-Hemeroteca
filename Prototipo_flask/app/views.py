# -*- coding: utf-8 -*-
from flask import render_template, flash, redirect, request, Markup
from pymongo import MongoClient
from bson.objectid import ObjectId
from app import app
from flask_pymongo import PyMongo
from .forms import LoginForm, ScanPDF, RssScrapping, Query, NewDataSet
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

mongo = PyMongo(app)
cliente = MongoClient()
db = cliente.test_database

rutapdf = ConfigVars.pdfpath
rutadataset = ConfigVars.datasetpath

ficheros = []
nombres = []
listaNoticias = []

def lookForFile(path, extension):
	for filename in os.listdir(path):
		if filename.endswith(extension):
			ficheros.append(os.path.join(path,filename))
			nombres.append(filename)
			#print filename
		elif "." not in filename:
			newPath = os.path.join(path,filename)
			lookForFile(newPath)



@app.route('/')
@app.route('/index', methods=['GET','POST'])
def index():
	query = Query()
	ejemplo = ''
	if request.method == 'POST':
		if request.form['submit'] == 'Buscar':
			del query.noticiasSample[:]
			result = request.form.get('search')
			for sample in db.noticias.find({'text':{'$regex': ".*"+result+".*"}}).limit(8):
				if 'tag' in sample.keys():
					etiqueta = sample['tag']
					etiquetaValores = sample['tag'].values()
				else:
					etiqueta = ''
					etiquetaValores = ''
				prediction = query.classification(sample['_id'])
				query.noticiasSample.append({'id':str(sample['_id']), 'titular':sample['title'], 'autor':sample['author'],
				 'fecha':sample['publishDate'], 'fuente':sample['source'], 'tag':etiqueta, 'tagValue':etiquetaValores,
				  'predict': prediction, 'link':sample['link']})
			return render_template("index.html",
						   title='Home',
						   query=query,
						   noticiasSample=query.noticiasSample,
						   etiqueta=etiqueta)

		if request.form['submit'] == 'Guardar Cambios':
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
	return render_template("index.html",
						   title='Home',
						   query=query)

@app.route('/queryresult/<string:word>', methods=['GET','POST'])
def queryResult(word):
	query = Query()
	ejemplo = ''
	noticiasSample = []
	return render_template("queryresult.html",
						   title='Home',
						   query=query,
						   noticiasSample=noticiasSample,
						   ejemplo=ejemplo)



@app.route('/explanation/<string:arguments>', methods=['GET','POST'])
def explanation(arguments):
	query = Query()
	auxid = arguments.split('-')[0]
	dataset = arguments.split('-')[1]
	results = query.explanation(auxid)
	resultHTML = Markup(results['html'])
	labels = []
	relevances = []
	for result in results['list']:
	 	labels.append(result[0])
	 	relevances.append(result[1])
	resultsList = { 'etiquetas': labels, 'importancias': relevances}
	return render_template("explanation.html",
						   title='Explanation',
						   query=query,
						   dataset=dataset,
						   resultHTML=resultHTML,
						   resultsList = resultsList)

@app.route('/scanpdf', methods=['GET','POST'])
def scanpdf():
	scan = ScanPDF()
	return render_template("scanpdf.html",
						   scan=scan)

@app.route('/savepdfnews', methods=['GET', 'POST'])
def savepdfnews():
	scan = ScanPDF()
	mostrar = 'Si'
	del ficheros[:]
	del nombres[:]
	del scan.noticias[:]
	del nombres[:]
	lookForFile(rutapdf, '.pdf')
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
	return render_template("savepdfnews.html",
					   scan=scan,
					   mostrar=mostrar)
	if request.method == 'POST':
		if request.form['submit'] == "Guardar Nuevas":
			for noticia in scan.noticias:
					db.noticias.update_one( {'title':noticia['titular']},{ '$set': {'author': noticia['autor'], 'title':noticia['titular'],
					'publishDate':noticia['fecha'], 'text':noticia['texto'], 'source':'PDF', 'tag':''}}, upsert=True)
			return render_template("savepdfnews.html", scan=scan, mostrar=mostrar)

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
						'publishDate':noti['publishDate'], 'text':noti['text'], 'source':noti['source'], 'tag':''}}, upsert=True)
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
def newdataset():
	return render_template('newdataset.html')

@app.route('/savenewdataset', methods=['GET', 'POST'])
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
			for topic in root.find_all('topic'):
				for noticiasxml in topic.find_all('noticias'):
					for noticiaxml in noticiasxml.find_all('noticia'):
						try:
							noticia = {
								'fecha':noticiaxml.fecha.text,
								'autor':noticiaxml.autor.text,
								'titular':noticiaxml.titular.text,
								'texto':noticiaxml.cuerpo.text,
								'link':noticiaxml.link.text,
								'tag':topic['id'] + noticiasxml['id']
							}
							nds.noticias.append(noticia)
						except Exception as e:
							pass
	mostrar = True
	return render_template('savenewdataset.html',mostrar = mostrar, nds = nds)
	if request.form['submit'] == 'Guardar Nuevas':
		for noticia in nds.noticias:
			db.noticias.update_one( {'title':noti['title']},{ '$set': {'author': noti['author'], 'title':noti['title'],
					'publishDate':noti['publishDate'], 'text':noti['text'], 'source':noti['source'], 'tag': ''}}, upsert=True)
		return render_template('savenewdataset.html',mostrar = mostrar, nds = nds)

# index view function suppressed for brevity

@app.route('/login', methods=['GET', 'POST'])
def login():
	form = LoginForm()
	return render_template('login.html', 
						   title='Sign In',
						   form=form)


FAKE_DATABASE = [
    {"id": 0,
     "msg":  """Miré los muros de la patria mía,
        si un tiempo fuertes, ya desmoronados,
        de la carrera de la edad cansados,
        por quien caduca ya su valentía."""
    },
    {"id": 1,
     "msg":  """Salíme al campo, vi que el sol bebía
        los arroyos del hielo desatados;
        y del monte quejosos los ganados,
        que con sombras hurtó la luz al día."""
    },
    {"id": 2,
     "msg":  """Entré en mi casa: vi que amancillada
        de anciana habitación era despojos;
        mi báculo más corvo, y menos fuerte."""
    },
    {"id": 3,
     "msg":  """Vencida de la edad sentí mi espada,
        y no hallé cosa en qué poner los ojos
        que no fuese recuerdo de la muerte."""
    },
    {"id": 4,
     "msg":  """¡Cómo de entre mis manos te resbalas!
        ¡Oh, cómo te deslizas, edad mía!
        ¡Qué mudos pasos traes, oh muerte fría,
        pues con callado pie todo lo igualas!"""
    },
    {"id": 5,
     "msg":  """Feroz de tierra el débil muro escalas,
        en quien lozana juventud se fía;
        mas ya mi corazón del postrer día
        atiende el vuelo, sin mirar las alas."""
    },
    {"id": 6,
     "msg":  """¡Oh condición mortal! ¡Oh dura suerte!
        ¡Que no puedo querer vivir mañana,
        sin la pensión de procurar mi muerte!"""
    },
    {"id": 7,
     "msg":      """Cualquier instante de la vida humana
        es nueva ejecución, con que me advierte
        cuán frágil es, cuán mísera, cuán vana."""
    },
]



@app.route('/example')
def example():
    # Some silly pre-processing
    summaries = []
    for entry in FAKE_DATABASE:
        summaries.append({"id": entry["id"], 
                     "summary": entry["msg"].splitlines()[0].upper().decode("utf-8") })
    return render_template('example.html', summaries=summaries)


@app.route('/showFull/<int:id>')
def showFull(id):
    msg = FAKE_DATABASE[id]["msg"]
    msg = msg.replace("\n", "<br />").decode("utf-8")
    return render_template('showFull.html', msg=msg)

if __name__ == '__main__':
    app.run(host = '0.0.0.0', port = 5000)