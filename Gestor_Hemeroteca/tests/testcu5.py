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

print 'Prueba simple de Caso de uso 5'

driver.find_element_by_id("RSS").click()
assert "Web Scrapping - TFG" in driver.title
select = Select(driver.find_element_by_id("media-select"))
options = select.options
#elegimos uno de los medios al azar
index = randint(0,len(options)-1)
select.select_by_index(index)
driver.find_element_by_id("readnews").click()
#Courtesy of https://stackoverflow.com/questions/14831041/how-to-count-no-of-rows-in-table-from-web-apllication-using-selenium-python-webd
row_count = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID,'newstable')))
#len(driver.find_elements_by_xpath("//table[@id='newstable']/tbody/tr"))
#Comprobamos que ha devuelto filas
assert row_count > 1
driver.close()
print 'Caso de uso 5 probado'



