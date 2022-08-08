#  установить перед использованием https://www.ghostscript.com/releases/gsdnld.html

import time
import os
import pymongo
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from pdf_compressor.pdf_compressor import compress

client = pymongo.MongoClient('localhost', 27017)
base = client['sts_db']
discharge = base['discharge']
user_login_password = base['user_login_password']


class Sts:
    def __init__(self):
        self.url = 'http://10.78.78.251/'
        options = webdriver.ChromeOptions()
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
                             ' AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.134 Safari/537.36')
        options.headless = True                 # Браузер откроется в фоновом режиме
        self.driver = webdriver.Chrome(options=options)
        self.driver.get(self.url)

    def auth(self, log, pswd):
        chrome = self.driver
        login = chrome.find_element('id', 'loginform-username')
        password = chrome.find_element('id', 'loginform-password')
        login.clear()
        password.clear()
        login.send_keys(log)
        password.send_keys(pswd)
        password.send_keys(Keys.ENTER)
        time.sleep(0.5)
        x = chrome.find_element(By.TAG_NAME, 'div')
        if x.text.split()[0] == 'Неверный':
            print(f"Неверный логин или пароль")
            self.close()
            return True
        time.sleep(0.5)
        y = chrome.find_element(By.TAG_NAME, 'div')
        if y.text.split('\n')[-3] == 'Закрытие активной сессии':
            chrome.find_element(By.XPATH, "//button[@class='btn btn-default btn-blue']").click()
            print(f'{log} успешно авторизован')
        time.sleep(1)
        return

    def load(self, id_sts, pdf):
        chrome = self.driver
        file_path = f'D:/{str(pdf)}'  # Путь к файлу
        chrome.get(f'{self.url}private/cards-issue/list?CardInfo%5Bcard_number%5D=&'
                   f'CardInfo%5Bapplicant%5D=&'
                   f'CardInfo%5Bcredential%5D=&'
                   f'CardInfo%5Bapp_identifer%5D={id_sts}&'
                   f'form=30')
        time.sleep(1)
        z = chrome.page_source.find('Ничего не найдено.')
        if z >= 1:
            print(f"Идентификатор {id_sts}, не найден")
            time.sleep(3)
            return
        chrome.find_element(By.XPATH, "//a[@class='btn btn-green btn-sm card-issue']").click()
        file_input = chrome.find_element(By.ID, 'receipt')
        file_input.send_keys(file_path)
        if os.path.getsize(file_path) > 1024 * 1024:
            new_name = f'{file_path}.tmp'
            compress(file_path, new_name, power=3)
            os.remove(file_path)
            os.rename(new_name, file_path)
        chrome.find_element(By.XPATH, "//button[@class='btn btn-default btn-blue send-issue']").click()    # отправка
        if os.path.isfile(file_path):     # Удаление файла
            os.remove(file_path)
            print(file_path, 'Файл удален')
        else:
            print(file_path, 'Файл отсутствует')
        time.sleep(3)
        return

    def close(self):
        self.driver.delete_all_cookies()
        self.driver.close()
        self.driver.quit()


if __name__ == '__main__':
    for r in range(len([*user_login_password.find({})])):
        sts = Sts()
        user = [*user_login_password.find({})][r]
        user_item = [*discharge.find({'id_sts_usr': {'$eq': user['_id']}})]
        if sts.auth(user['user'], user['password']):
            continue
        for number in range(len(user_item)):
            item = user_item[number]
            print(item['id_sts'])
            sts.load(item['id_sts'], item['link'])
        sts.close()
