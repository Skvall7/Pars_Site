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

    def auth(self, login, password):
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
        return

    def take(self):
        session = self.session
        page = session.get(self.url + 'private/cards-issue/list?form=30&per-page=100')
        soup = BeautifulSoup(page.text, 'html.parser')
        for td in soup.find_all('tr'):
            href = self.url + str(td.find('a', class_="btn"))[87:125]
            href2 = self.url + str(td.find('a'))[10:39]
            info = td.get_text('|').split('|')
            if info[0][:3] != 'RUD':
                continue
            info.pop(-1)
            info.extend(href2.split())
            time = datetime.datetime.now()
            info.extend([str(time).split()])
            self.result.append(info)
            pdf = session.get(href)
            if not (os.path.isdir(self.download + str(time)[0:10])):
                os.mkdir(self.download + str(time)[0:10])
            with open(f'{self.download}{str(time)[0:10]}/{info[3]}.pdf', 'wb') as file:
                file.write(pdf.content)
                print(f'{self.download}{str(time)[0:10]}/{info[3]}.pdf - файл сохранен')
        return

    def record_db(self, dis):
        for info in self.result:
            base_dict = {'id_sts': info[3], 'date': info[5], 'link': info[4], 'props': info[:3]}
            print(dis.insert_one(base_dict).inserted_id, '- успешно занесено в базу')
        return

    def close(self):
        self.session.cookies.clear_session_cookies()
        self.session.get(self.url + 'private/default/logout')
        return


if __name__ == '__main__':
    item = user_login_password.find({})
    for r in range(100):
        try:
            user = [*item[r].values()]
            r = Sts()
            r.auth(user[1], user[2])
            r.take()
            r.record_db(discharge)
            r.close()
        except:
            continue
