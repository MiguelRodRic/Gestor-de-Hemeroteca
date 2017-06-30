from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from pymongo import MongoClient

cliente = MongoClient()
db = cliente.test_database

driver = webdriver.Firefox()
driver.get("http://127.0.0.1:5000/")

print 'Prueba simple de Caso de uso 6'

driver.find_element_by_id("XML").click()
assert "Nuevo Corpus - TFG" in driver.title
driver.find_element_by_id("readcorpus").click()
#Courtesy of https://stackoverflow.com/questions/14831041/how-to-count-no-of-rows-in-table-from-web-apllication-using-selenium-python-webd
row_count = len(driver.find_elements_by_xpath("//table[@id='corpustable']/tbody/tr"))
assert row_count > 1
driver.close()
print 'Caso de uso 6 probado'



