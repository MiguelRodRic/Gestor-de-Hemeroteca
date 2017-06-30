from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pymongo import MongoClient
from random import randint

cliente = MongoClient()
db = cliente.test_database

driver = webdriver.Firefox()
driver.get("http://127.0.0.1:5000/")

print 'Prueba simple de Caso de uso 2'

assert "Consulta de Noticias - TFG" in driver.title
input_text = driver.find_element_by_id("search")

input_text.send_keys("vientre")
driver.find_element_by_id('buscarbutton').click()
#Courtesy of https://stackoverflow.com/questions/14831041/how-to-count-no-of-rows-in-table-from-web-apllication-using-selenium-python-webd
row_count = WebDriverWait(driver, 25).until(EC.presence_of_element_located((By.ID,'resultTable')))
#len(driver.find_elements_by_xpath("//table[@id='newstable']/tbody/tr"))
#Comprobamos que ha devuelto filas
assert row_count > 1
#guardamos cambios sin actualizar ninguna fila
driver.find_element_by_id("savechanges").click()
assert driver.find_element_by_id("mensaje") == "No se ha actualizado ninguna noticia"
driver.close()

print 'Caso de uso 2 probado'



