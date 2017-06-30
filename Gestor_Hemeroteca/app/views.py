# -*- coding: utf-8 -*-
"""Parte de la implementación dedicada a las operaciones back-end de las pestañas"""
import os
import urllib2
import collections
from cStringIO import StringIO
import feedparser
from flask import render_template, request, Markup
from flask_breadcrumbs import register_breadcrumb
from pymongo import MongoClient
from bson.objectid import ObjectId
from flask_pymongo import PyMongo
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from bs4 import BeautifulSoup
from config import ConfigVars
from app import app
from .forms import NewsPDF, NewsRSS, Query, Corpus, Dataset

#Arrancar base de datos
MONGO = PyMongo(app)
CLIENT = MongoClient()
DB = CLIENT.test_database

#Rutas necesarias obtenidas del fichero de configuración
PATHPDF = ConfigVars.pdfpath
PATHDATASET = ConfigVars.datasetpath

#Variables
FICHEROS = []
NOMBRES_ARCHIVOS = []

def lookForFile(path, extension):
    """Función auxiliar para buscar ficheros de una extensión determinada dentro de un directorio"""
    for filename in os.listdir(path):
        if filename.endswith(extension):
            FICHEROS.append(os.path.join(path, filename))
            NOMBRES_ARCHIVOS.append(filename)
            #print filename
        elif os.path.isdir(filename):
            new_path = os.path.join(path, filename)
            lookForFile(new_path, extension)

def scanNewsXML(fichero):
    """Función auxiliar que realiza todo el escaneo de los datasets incluidos en documentos XML"""
    textos = []
    noticias_retorno = []
    soup = BeautifulSoup(open(PATHDATASET + '/' + fichero, 'r'), 'xml')
    for root in soup.find_all('root'):
        for topic in root.find_all('dataset'):
            for noticiasxml in topic.find_all('noticias'):
                for noticiaxml in noticiasxml.find_all('noticia'):
                    try:
                        request_url = urllib2.Request(noticiaxml.link.text)
                        handle = urllib2.urlopen(request_url)
                        html = handle.read()
                        noticia_soup = BeautifulSoup(html, 'html.parser')
                        for expendable in noticia_soup(['style', 'script', '[document]', 'head', 'title']):
                            expendable.extract()
                        if noticia_soup.find("article"):
                            textos.append(noticia_soup.find("article").text)
                        else:
                            textos.append(noticia_soup.getText())
                        noticia = {
                            'fecha':noticiaxml.fecha.text, 'autor':noticiaxml.autor.text,
                            'titular':noticiaxml.titular.text, 'link':noticiaxml.link.text,
                            'texto':noticia_soup.getText(), 'tag':topic['topic']+ ' - ' + noticiasxml['clase']
                        }
                        noticias_retorno.append(noticia)
                    except Exception as ex:
                        error_text = str(ex)
                        noticias_retorno.append(error_text)
    return noticias_retorno


@app.route('/')
@app.route('/index/', methods=['GET', 'POST'])
@register_breadcrumb(app, '.', 'Inicio')
def index():
    """Back-end para la pestaña de inicio y búsqueda de resultados"""
    query = Query()
    etiquetas = []
    clases = {}
    for dataset in DB.datasets.find({}):
        etiquetas.append(dataset['dataset'])
        clases[dataset['dataset']] = [dataset['clases']['clase1'], dataset['clases']['clase2']]
    if request.method == 'POST':
        if request.form['submit'] == 'Buscar':
            del query.noticiasSample[:]
            result = query.search.data
            result_noticias = DB.noticias.find({'text':{'$regex': ".*"+result+".*"}})
            amount_noticias = result_noticias.count()/5
            for sample in DB.noticias.find({'text':{'$regex': ".*"+result+".*"}}).limit(5):
                prediction = []
                predict_tag = {}
                saved_tag = {}
                mensaje = ''
                for tag in etiquetas:
                    if sample['tag'][tag] != '':
                        saved_tag[tag] = sample['tag'][tag]
                    else:
                        saved_tag[tag] = None
                    pred = query.classification(sample['_id'], tag)
                    if not isinstance(pred, basestring):
                        prediction.append(pred)
                        if pred['aFavor'] > 0.5:
                            predict_tag[tag] = 'aFavor'
                        else:
                            predict_tag[tag] = 'enContra'
                    else:
                        prediction.append(None)
                        predict_tag[tag] = None
                try:
                    link = sample['link']
                except:
                    link = ''
                query.noticiasSample.append({'id':str(sample['_id']),
                    'titular':sample['title'], 'autor':sample['author'],
                    'fecha':sample['publishDate'], 'fuente':sample['source'],
                    'predict': prediction, 'predictTag':predict_tag, 'savedTag':saved_tag,
                    'link':link, 'mensaje':mensaje})
            return render_template("index.html", title='Consulta de Noticias', query=query,
                noticiasSample=query.noticiasSample, etiquetas=etiquetas, clases=clases,
                amount_noticias=amount_noticias)
        elif request.form['submit'] == 'Guardar Cambios':
            tag = request.form.get('datasetSelect')
            tag_to_update = "tag."+str(tag)
            mensaje = ''
            for noticia_to_update in query.noticiasSample:
                if request.form.get(str(noticia_to_update['id'])) is not None:
                    update_result = DB.noticias.update_one(
                        {"_id":ObjectId(noticia_to_update['id'])},
                        {'$set':{tag_to_update:request.form.get(noticia_to_update['id'])}})
                    if update_result.modified_count > 0:
                        mensaje = 'Noticias Actualizadas'
            if mensaje == '':
                mensaje = 'No se ha actualizado ninguna noticia'
            return render_template("index.html", title='Consulta de Noticias', mensaje=mensaje)
        else:
            del query.noticiasSample[:]
            result = query.search.data
            result_noticias = DB.noticias.find({'text':{'$regex': ".*"+result+".*"}})
            amount_noticias = result_noticias.count()/5
            page = int(request.form['submit'])
            for sample in DB.noticias.find({'text':{'$regex': ".*"+result+".*"}}).skip(page*5).limit(5):
                prediction = []
                predict_tag = {}
                saved_tag = {}
                mensaje = ''
                for tag in etiquetas:
                    if sample['tag'][tag] != '':
                        saved_tag[tag] = sample['tag'][tag]
                    else:
                        saved_tag[tag] = None
                    pred = query.classification(sample['_id'], tag)
                    if not isinstance(pred, basestring):
                        prediction.append(pred)
                        if pred['aFavor'] > 0.5:
                            predict_tag[tag] = 'aFavor'
                        else:
                            predict_tag[tag] = 'enContra'
                    else:
                        prediction.append(None)
                        predict_tag[tag] = None
                try:
                    link = sample['link']
                except:
                    link = ''
                query.noticiasSample.append({'id':str(sample['_id']), 'titular':sample['title'],
                    'autor':sample['author'], 'fecha':sample['publishDate'],
                    'fuente':sample['source'], 'predict': prediction, 'predictTag':predict_tag,
                    'savedTag':saved_tag, 'link':link, 'mensaje':mensaje})
            return render_template("index.html", title='Home', query=query,
                           noticiasSample=query.noticiasSample, etiquetas=etiquetas,
                           clases=clases, amount_noticias=amount_noticias, page=page)
    return render_template("index.html", title='Consulta de Noticias', query=query)


@app.route('/statistics/', methods=['GET', 'POST'])
def statistics():
    """Back-end para la pestaña de gráficos de las noticias"""
    result_noticias = DB.noticias.find({})
    autores = []
    fechas = []
    fuentes = []
    for noticia in result_noticias:
        autores.append(noticia['author'])
        fechas.append(noticia['publishDate'])
        fuentes.append(noticia['source'])
    autores_counter = collections.Counter(autores)
    fechas_counter = collections.Counter(fechas)
    fuentes_counter = collections.Counter(fuentes)
    return render_template("statistics.html", title='Statistics', autores=autores_counter,
                           fechas=fechas_counter, fuentes=fuentes_counter)


@app.route('/explanation/<string:arguments>', methods=['GET', 'POST'])
@register_breadcrumb(app, '.Explicacion', 'Explicacion')
def explanation(arguments):
    """Back-end para la pestaña de explicación de predicciones"""
    query = Query()
    arguments_splitted = arguments.split('-')
    try:
        auxid = arguments_splitted[0]
        dataset = arguments_splitted[1]
        prediction = arguments_splitted[2]
        mensaje = None
        result_html = None
        result_list = None
        if prediction == 'aFavor':
            prediction = 'A Favor'
        if prediction == 'enContra':
            prediction = 'En Contra'
        if len(arguments_splitted) == 4:
            tag_to_update = "tag."+dataset
            update_result = DB.noticias.update_one({"_id":ObjectId(auxid)},
                {'$set':{tag_to_update:prediction}})
            mensaje = ''
            if update_result.modified_count > 0:
                mensaje = 'Noticia Actualizada'
            if mensaje == '':
                mensaje = 'No se ha actualizado la noticia'

        else:
            results = query.explanation(auxid, dataset)
            result_html = Markup(results['html'])
            result_list = results['list']
        return render_template("explanation.html", title='Explicacion', auxid=auxid, query=query,
                               prediction=prediction, dataset=dataset, resultHTML=result_html,
                               mensaje=mensaje, resultsList=result_list)
    except:
        mensaje = 'No se ha podido cargar la explicacion'
        return render_template("explanation.html",
                               title='Explicacion',
                               mensaje=mensaje)


@app.route('/createdataset', methods=['GET', 'POST'])
@register_breadcrumb(app, '.Nuevo Dataset', 'Nuevo Dataset')
def createdataset():
    """Back-end para la pestaña de creación de nuevos Dataset"""
    create_ds = Dataset()
    if request.method == 'POST':
        if request.form['submit'] == "Guardar Dataset":
            if create_ds.nombredataset.data != '' and \
            create_ds.clase1.data != '' and \
            create_ds.clase2.data != '':
                DB.datasets.insert_one({'dataset':create_ds.nombredataset.data,
                    'clases':{'clase1':create_ds.clase1.data, 'clase2':create_ds.clase2.data}})
                for noticia in DB.noticias.find({}):
                    DB.noticias.update_one({'_id':noticia.get('_id')},
                        {'$set':{'tag.'+create_ds.nombredataset.data:''}})
                mensaje = 'Dataset Incluido'
            else:
                mensaje = 'No se han rellenado los campos correctamente'
            return render_template("createdataset.html", title='Nuevo Dataset', createDS=create_ds, mensaje=mensaje)
    return render_template("createdataset.html", title='Nuevo Dataset', createDS=create_ds)


@app.route('/scanpdf', methods=['GET', 'POST'])
@register_breadcrumb(app, '.Lectura PDF', 'Lectura PDF')
def scanpdf():
    """Back-end para la pestaña de lectura de PDF"""
    scan = NewsPDF()
    return render_template("scanpdf.html", title='Lectura PDF', scan=scan)


@app.route('/savepdfnews', methods=['GET', 'POST'])
@register_breadcrumb(app, '.Resultados PDF', 'Resultados PDF')
def savepdfnews():
    """Back-end para la pestaña de resultados de la lectura de PDF"""
    scan = NewsPDF()
    mostrar = 'Si'
    del FICHEROS[:]
    del NOMBRES_ARCHIVOS[:]
    del scan.noticias[:]
    lookForFile(PATHPDF, '.pdf')
    textos = [None]*len(FICHEROS)
    autores = [None]*len(FICHEROS)
    fechas = [None]*len(FICHEROS)
    mensaje = None
    if(len(FICHEROS)) > 0:
        for registro in FICHEROS:
            consulta = DB.noticias.find_one({'title':{'$regex': NOMBRES_ARCHIVOS[FICHEROS.index(registro)]}})
            ya_almacenada = ''
            if consulta is None:
                rsrcmgr = PDFResourceManager()
                retstr = StringIO()
                codec = 'utf-8'
                laparams = LAParams()
                device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)
                pdf_local = registro
                file_open = open(pdf_local, 'rb')
                #print str(doc.info).decode().encode('utf-8')
                ya_almacenada = 'No'
                interpreter = PDFPageInterpreter(rsrcmgr, device)
                password = ""
                maxpages = 0
                caching = True
                pagenos = set()
                for page in PDFPage.get_pages(file_open, pagenos, maxpages=maxpages, password=password, caching=caching, check_extractable=True):
                    interpreter.process_page(page)
                text = retstr.getvalue()
                indice = FICHEROS.index(registro)
                try:
                    textos[indice] = text.split("(Cuerpo)")[1].decode('utf-8', 'ignore')
                except:
                    mensaje.append('\n No se ha encontado el texto de la noticia')
                try:
                    autores[indice] = text.split("(Autor)")[1].decode('utf-8', 'ignore')
                except:
                    mensaje.append('\n No se ha encontado el autor de la noticia')
                try:
                    fechas[indice] = text.split("(Fecha)")[1].decode('utf-8', 'ignore')
                except:
                    mensaje.append('\n No se ha encontado la fecha de la noticia')
                try:
                    NOMBRES_ARCHIVOS[indice] = text.split("(Titular)")[1].decode('utf-8', 'ignore')
                except:
                    mensaje.append('\n No se ha encontado el titular de la noticia')

                file_open.close()
                device.close()
                retstr.close()
            else:
                fechas[FICHEROS.index(registro)] = consulta['publishDate']
                autores[FICHEROS.index(registro)] = consulta['author']
                NOMBRES_ARCHIVOS[FICHEROS.index(registro)] = consulta['title']
                textos[FICHEROS.index(registro)] = consulta['text']
                ya_almacenada = 'Si'
            try:
                autoraux = autores[FICHEROS.index(registro)]
            except:
                autoraux = autores[FICHEROS.index(registro)].decode('utf-16')
            scan.noticias.append({'texto':textos[FICHEROS.index(registro)],
             'autor':autoraux, 'fecha':fechas[FICHEROS.index(registro)],
             'titular':NOMBRES_ARCHIVOS[FICHEROS.index(registro)], 'almacenada':ya_almacenada,
             'link':FICHEROS[FICHEROS.index(registro)]})
    else:
        mensaje = 'No se han encontrado archivos'
    if request.method == 'POST':
        if request.form['submit'] == "Guardar Nuevas":
            mensaje = "Noticias insertadas"
            for noticia in scan.noticias:
                if DB.noticias.find_one({'title':{'$regex': noticia['titular']}}) is None:
                    DB.noticias.insert_one({'author': noticia['autor'], 'title':noticia['titular'],
                        'publishDate':noticia['fecha'], 'text':noticia['texto'],
                        'link':noticia['link'], 'source':'PDF', 'tag':{'Machismo':'', 'VientreAlquiler':''}})
            return render_template("savepdfnews.html", title='Lectura PDF',
                scan=scan, mostrar=mostrar, mensaje=mensaje)
    return render_template("savepdfnews.html", title='Lectura PDF', scan=scan,
        mostrar=mostrar, mensaje=mensaje)

@app.route('/websearch', methods=['GET', 'POST'])
@register_breadcrumb(app, '.Busqueda RSS', 'Busqueda RSS')
def websearch():
    """Back-end para la pestaña de Web Scraping"""
    rss_ws = NewsRSS()
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
            del rss_ws.noticias[:]
            select = request.form.get('media-select')
            if select == u'ElDiario':
                text_rss = feedparser.parse('http://www.eldiario.es/rss/')
                etiqueta = 'summary'
                fuente = 'ElDiario'
            elif select == u'ElPais':
                text_rss = feedparser.parse('http://ep00.epimg.net/rss/elpais/portada.xml')
                etiqueta = 'summary'
                fuente = 'El Pais'
            elif select == u'Publico':
                text_rss = feedparser.parse('http://www.publico.es/rss/')
                etiqueta = 'description'
                fuente = 'Publico'
            elif select == u'ElMundo':
                text_rss = feedparser.parse('http://www.elmundo.es/rss/portada.xml')
                etiqueta = 'summary'
                fuente = 'El Mundo'
            titulares = []
            textos = []
            fechas = []
            autores = []
            links = []
            if etiqueta is not None:
                if text_rss['entries'] > 15:
                    top = 15
                else:
                    top = len(text_rss['entries'])
                for entry in text_rss['entries'][0:top]:
                    try:
                        titulares.append(entry['title'])
                        fechas.append(entry['published'])
                        autores.append(entry['author'])
                        links.append(entry['links'][0]['href'])
                        request_url = urllib2.Request(entry['links'][0]['href'])
                        handle = urllib2.urlopen(request_url)
                        html = handle.read()
                        noticia_soup = BeautifulSoup(html, 'html.parser')
                        for expendable in noticia_soup(['style', 'script', '[document]', 'head', 'title']):
                            expendable.extract()
                        if noticia_soup.find("article"):
                            textos.append(noticia_soup.find("article").text)
                        else:
                            textos.append(noticia_soup.getText())
                    except Exception as ex:
                        error_text = str(ex)
                for titular in titulares:
                    try:
                        indice = titulares.index(titular)
                        autor = autores[indice]
                        fecha = fechas[indice]
                        link = links[indice]
                        texto = textos[indice].encode('utf-8').decode('utf-8')
                        incluida = DB.noticias.find_one({'title':{'$regex': titular}})
                        almacenada = ''
                        if incluida is None:
                            almacenada = 'No'
                        else:
                            almacenada = 'Si'
                        noticia = {'author': autor, 'title':titular, 'link':link,
                                    'publishDate':fecha, 'text':texto,
                                    'source':fuente, 'almacenada':almacenada}
                        rss_ws.noticias.append(noticia)
                    except:
                        pass
                return render_template('websearch.html', title='Web Scraping', rssWS=rss_ws,
                                       options=options, fuente=fuente)
        if request.form['submit'] == "Guardar Nuevas":
            for noti in rss_ws.noticias:
                if DB.noticias.find_one({'title':{'$regex': noti['title']}}) is None:
                    DB.noticias.insert_one({'author': noti['author'], 'title':noti['title'],
                        'publishDate':noti['publishDate'], 'text':noti['text'],
                        'link':noti['link'], 'source':noti['source'],
                        'tag':{'Machismo':'', 'VientreAlquiler':''}})
            mensaje = 'Se han incluido en base de datos'
            return render_template('websearch.html', title='Web Scraping', rssWS=rss_ws,
                                   options=options, etiqueta=etiqueta, fuente=fuente,
                                   mensaje=mensaje)
    return render_template('websearch.html', title='Web Scraping', rssWS=rss_ws, options=options)


@app.route('/newdataset', methods=['GET', 'POST'])
@register_breadcrumb(app, '.Lectura Dataset', 'Lectura Dataset')
def newdataset():
    """Back-end para la pestaña de lectura de XML"""
    return render_template('newdataset.html', title='Nuevo Corpus')


@app.route('/savenewdataset', methods=['GET', 'POST'])
@register_breadcrumb(app, '.Resultados Dataset', 'Resultados Dataset')
def savenewdataset():
    """Back-end para la pestaña de resultados de lectura de PDF"""
    nds = Corpus()
    mostrar = True
    #get all the links from the xml
    if request.method == 'POST':
        if request.form['submit'] == 'Guardar Nuevas':
            insertadas = []
            for noticia in nds.noticias:
                if DB.noticias.find_one({'title':{'$regex': noticia['titular']}}) is None:
                    insertada = DB.noticias.insert_one({'author': noticia['autor'], 'title':noticia['titular'],
                        'publishDate':noticia['fecha'], 'text':noticia['texto'],
                        'link':noticia['link'], 'source':'XML',
                        'tag':{'Machismo':'', 'VientreAlquiler':''}})
                    tag_to_update = 'tag.' + noticia['tag'].split(' - ')[0]
                    etiquetada = DB.noticias.update_one({'_id':insertada.inserted_id},
                        {'$set':{tag_to_update:noticia['tag'].split(' - ')[1]}})
                    insertadas.append(insertada.inserted_id)
            if len(insertadas) == 0:
                mensaje = 'No se han introducido nuevas noticias'
            else:
                mensaje = 'Noticias insertadas'
            return render_template('savenewdataset.html', title='Nuevo Corpus',
                mensaje=mensaje, nds=nds)
    else:
        del NOMBRES_ARCHIVOS[:]
        del nds.noticias[:]
        lookForFile(PATHDATASET, '.xml')
        for nombre in NOMBRES_ARCHIVOS:
            noticias_fichero = scanNewsXML(nombre)
            for noticia in noticias_fichero:
                nds.noticias.append(noticia)
    return render_template('savenewdataset.html', title='Nuevo Corpus', mostrar=mostrar, nds=nds)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
