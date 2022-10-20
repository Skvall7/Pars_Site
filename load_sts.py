import time
import os
import pymongo
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from pdf_compressor.pdf_compressor import compress

client = pymongo.MongoClient('localhost', 27017)
base = client['sts_db']
discharge = base['discharge']
user_login_password = base['user_login_password']
with open('json.json') as f:
    input_file = json.load(f)       # Получаем JSON из файла, будет из базы?


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
        self.notify()
        return

    def notify(self):       # Проверка на всплывающие уведомления
        chrome = self.driver
        chrome.refresh()
        try:
            if chrome.find_element('id', 'mn'):
                btn = chrome.find_element('id', 'read-btn')
                btn.click()
                btn.send_keys(Keys.ENTER)
                self.notify()
            else:
                return
        finally:
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

    def check_card(self, users_id, base_ids):
        users_id = list(set(users_id))      # Отфильтровывает одинаковые sts_id
        chrome = self.driver
        iter_id = 0
        for user_id in users_id:
            chrome.get(f'{self.url}private/cards/list?CardInfo%5Bcard_number%5D=&'
                       f'CardInfo%5Bstatus%5D=&'
                       f'CardInfo%5Bsurname%5D=&'
                       f'CardInfo%5Bname%5D=&'
                       f'CardInfo%5Bmiddlename%5D=&'
                       f'CardInfo%5Bapp_identifer%5D={user_id}&'
                       f'CardInfo%5Bpackage%5D=&'
                       f'CardInfo%5Bpersonalized_date%5D=&'
                       f'CardInfo%5Borg_creator%5D=&'
                       f'CardInfo%5Bissunce_user_id%5D=&'
                       f'CardInfo%5Bdefective_status%5D=&'
                       f'CardInfo%5Bform_producer%5D=&form=30')
            status = chrome.find_elements(By.TAG_NAME, 'tr')[2].text.split(' ')[1]
            print(f'{status} - {user_id} - {base_ids[iter_id]}')
            iter_id += 1
        return

    def close(self):
        self.driver.delete_all_cookies()
        self.driver.close()
        self.driver.quit()


def base_json_to_dict(input_json):
    need_auth = []
    dict_check = {}
    for item in input_json:
        need_auth.append(item['userSts'])
    need_auth = list(set(need_auth))
    for item in input_json:
        for usr in need_auth:
            if list(item.values())[1] == usr:
                if dict_check.get(list(item.values())[1], False) is False:
                    dict_check[usr] = [[list(item.values())[2]], [list(item.values())[0]]]
                else:
                    dict_check[usr][0].append(list(item.values())[2])
                    dict_check[usr][1].append(list(item.values())[0])
    return dict_check


if __name__ == '__main__':
    # for r in range(len([*user_login_password.find({})])):
    #     sts = Sts()
    #     user = [*user_login_password.find({})][r]
    #     user_item = [*discharge.find({'id_sts_usr': {'$eq': user['_id']}})]
    #     if sts.auth(user['user'], user['password']):
    #         continue
    #     for number in range(len(user_item)):
    #         item = user_item[number]
    #         print(item['id_sts'])
    #         sts.load(item['id_sts'], item['link'])
    #     sts.close()
    dict_user = base_json_to_dict(input_file)
    for user in list(dict_user.keys()):
        user_login = [*user_login_password.find({'user': user})]
        list_id_sts = dict_user[user][0]
        list_id = dict_user[user][1]
        sts = Sts()
        sts.auth(user_login[0]['user'], user_login[0]['password'])
        sts.check_card(list_id_sts, list_id)
        sts.close()
