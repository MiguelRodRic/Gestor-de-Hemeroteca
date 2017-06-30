from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from pymongo import MongoClient

cliente = MongoClient()
db = cliente.test_database

driver = webdriver.Firefox()
driver.get("http://127.0.0.1:5000/")

print 'Prueba simple de Caso de uso 7'

driver.find_element_by_id("createnewdataset").click()
assert "Nuevo Dataset - TFG" in driver.title
driver.find_element_by_id("saveds").click()
assert driver.find_element_by_id("mensaje").text == 'No se han rellenado los campos correctamente'
driver.close()
print 'Caso de uso 7 probado'



