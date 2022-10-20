import requests
import datetime
import pymongo
import os
from bs4 import BeautifulSoup

client = pymongo.MongoClient('localhost', 27017)
base = client['sts_db']
discharge = base['discharge']
user_login_password = base['user_login_password']


class Sts:
    url = 'http://10.78.78.251/'
    session = requests.session()
    download = '/my/temp/'
    if not (os.path.isdir(download)):
        os.mkdir(download)
    result = []

    def auth(self, login, password):            # Авторизация на сайте СТС
        params = {'_csrf': '',
                  'LoginForm[username]': login,
                  'LoginForm[password]': password,
                  'close-session': 1,
                  'close-not-verification': 1
                  }
        session = self.session
        url = self.url + 'private/default/login'
        page = session.get(url)
        soup = BeautifulSoup(page.text, 'html.parser')
        csrf = str(soup.find('input'))[-59:-3]
        params.update({'_csrf': csrf})
        session.post(url, params)
        self.result = []
        print(login, password)
        # self.notify()           # Проход по уведомлениям
        return

    # def notify(self):
    #     url = self.url + 'private/default/index'
    #     page = self.session.get(url)
    #     soup = BeautifulSoup(page.text, 'html.parser')
    #     ntfy = str(soup.find_all('div', {'id': 'mn'}))      # Находим блок с уведомлением
    #     a = str(BeautifulSoup(ntfy, 'html.parser').find('a', {'data-id': True}))[66:69]     # ИД уведомления
    #     if ntfy != 'None':
    #         print('Уведомление')
    #         m_id = {'messageId': a}
    #         self.session.post(self.url + 'private/messages/read/', data=m_id)
    #         print(a)
    #         return
    #     print(a)
    #     return

    def take(self, dis=discharge):
        # Получение данных из СТС
        session = self.session
        page = session.get(self.url + f'private/cards-issue/list?form=30&per-page=100&page=1')
        check = BeautifulSoup(page.text, 'html.parser')
        check_str = str(check.find_all('div', class_='summary'))
        count = int(BeautifulSoup(check_str, 'html.parser').get_text()[-4:-2].strip())
        page_count = (count // 100) + 2
        for page_number in range(1, page_count):
            page = session.get(self.url + f'private/cards-issue/list?form=30&per-page=100&page={page_number}')
            soup = BeautifulSoup(page.text, 'html.parser')
            for td in soup.find_all('tr'):
                href = self.url + str(td.find('a', class_="btn"))[87:125]
                info = td.get_text('|').split('|')
                if info[0][:3] != 'RUD':
                    continue
                if not self.verify(dis, info[3]):
                    print(f'Запись {info[3]} актуальна')
                    continue
                info.pop(-1)
                time = datetime.datetime.now()
                pdf = session.get(href)
                if not (os.path.isdir(self.download + str(time)[0:10])):
                    os.mkdir(self.download + str(time)[0:10])
                href2 = f'{self.download}{str(time)[0:10]}/{info[3]}.pdf'
                with open(href2, 'wb') as file:
                    file.write(pdf.content)
                    print(f'{href2} - файл сохранен')
                info.extend(href2.split())
                info.extend([str(time).split()])
                self.result.append(info)
        return

    def verify(self, dis, id_sts):
        # Проверка на количество прошедших дней
        user_item = [*dis.find({'id_sts': id_sts})]
        if not user_item:     # Проверка на наличие записи в БД
            return True
        y = int(user_item[-1]['date'][0].split('-')[0])   # Ищет последнюю запись в БД
        m = int(user_item[-1]['date'][0].split('-')[1])
        d = int(user_item[-1]['date'][0].split('-')[2])
        some_date = datetime.datetime(year=y, month=m, day=d)
        date = datetime.datetime.now()
        verify_date = date - some_date
        return verify_date.days > 10        # Если прошло 10 и более дней возвращает True

    def record_db(self, dis, user_id):
        # Запись результата в базу
        for info in self.result:
            base_dict = {'id_sts': info[3], 'date': info[5], 'link': info[4], 'props': info[:3], 'id_sts_usr': user_id}
            print(dis.insert_one(base_dict).inserted_id, '- успешно занесено в базу')
        return

    def close(self):
        # Завершение сессии пользователя
        self.session.cookies.clear_session_cookies()
        self.session.get(self.url + 'private/default/logout')
        return


if __name__ == '__main__':
    item = user_login_password.find({})
    for r in range(100):        # Максимальное количество аккаунтов
        try:
            user = [*item[r].values()]
            sts = Sts()
            sts.auth(user[1], user[2])
            sts.take(discharge)
            sts.record_db(discharge, user[0])
            sts.close()
        except:
            continue
