from selenium import webdriver
from selenium.webdriver.common.by import By
import xlsxwriter
import time

options = webdriver.ChromeOptions()
options.add_argument("--disable-infobars")

browser = webdriver.Chrome()
browser.get("https://iotvega.com/product")
time.sleep(10)

product = browser.find_element(By.CLASS_NAME, "main-container")
product.click()
time.sleep(10)
workbook = xlsxwriter.Workbook("alabame.xlsx")
worksheet = workbook.add_worksheet()

for numba in range(1, 40, 2):
    name = browser.find_elevent(By.XPATH, f'html/body/section/div/div/div/table/tbody/tr[{numba}]/td[1]').text
    charac = browser.find_element(By.XPATH, f'html/body/section/div/div/div/table/tbody/tr[{numba}]/td[2]').text

    worksheet.write(f"A{numba}", name)
    worksheet.write(f"B{numba}", charac)
    print(name, charac)

workbook.close()