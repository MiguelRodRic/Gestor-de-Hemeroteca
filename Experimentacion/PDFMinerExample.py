from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from cStringIO import StringIO

#Some of the code is courtesy of:
#http://stackoverflow.com/questions/26494211/extracting-text-from-a-pdf-file-using-pdfminer-in-python

rsrcmgr = PDFResourceManager()
retstr = StringIO()
codec = 'utf-8'
laparams = LAParams()
device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)

#Here you have to write the name of the pdf file you want to read
#IMPORTANT: It has to be in the same directory of this code
pdfLocal = 'filename.pdf'
fp = file(pdfLocal, 'rb')
interpreter = PDFPageInterpreter(rsrcmgr, device)
password = ""
maxpages = 0
caching = True
pagenos=set()
for page in PDFPage.get_pages(fp, pagenos, maxpages=maxpages, password=password,caching=caching, check_extractable=True):
    interpreter.process_page(page)

text = retstr.getvalue()

fp.close()
device.close()
retstr.close()

#Now, we're trying to split the text into paragraphs (That's why the '.\n')
paragraphs = text.split(".\n")

#Print all the paragraphs with a loop
for paragraph in paragraphs:
    print paragraph