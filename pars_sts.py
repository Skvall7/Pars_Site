import requests
import datetime
import pymongo
from bs4 import BeautifulSoup


class Sts:
    url = 'http://10.78.78.251/'
    session = requests.session()
    result = []
    client = pymongo.MongoClient('localhost', 27017)
    base = client['sts_db']
    discharge = base['discharge']
    user_login_password = base['user_login_password']

    def auth(self):
        params = {'_csrf': '',
                  'LoginForm[username]': 'aoka19@im.ru20',
                  'LoginForm[password]': 'Aoka12346',
                  'login-button': '',
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
        return

    def take(self):
        session = self.session
        page = session.get(self.url + 'private/cards-issue/list?form=30&per-page=100')
        soup = BeautifulSoup(page.text, 'html.parser')
        for td in soup.find_all('tr'):
            href = self.url + str(td.find('a'))[9:39]
            info = td.get_text('|').split('|')
            info.pop(-1)
            info.extend(href.split())
            time = datetime.datetime.now()
            info.extend([str(time).split()])
            self.result.append(info)
        self.result.pop(0)
        self.result.pop(0)
        print(self.result)
        return self.result

    def record_db(self):
        for info in self.result:
            base_dict = {'id_sts': info[3], 'date': info[5], 'link': info[4], 'props': info[:2]}
            print(self.discharge.insert_one(base_dict).inserted_id)


if __name__ == '__main__':
    sts = Sts()
    sts.auth()
    sts.take()
    sts.record_db()
