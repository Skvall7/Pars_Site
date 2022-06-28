import requests


class Nasvyazi:
    url = 'https://forum.na-svyazi.ru/'

    def auth(self):
        session = requests.session()
        url = self.url
        params = {'act': 'Login',
                  'CODE': '01',
                  'CookieDate': 1,
                  'UserName': 'Dicobraz',
                  'PassWord': 'User!dic',
                  'x': 31, 'y': 15}
        r = session.post(url, params)
        print(r.text)


if __name__ == '__main__':
    nasvyazi = Nasvyazi()
    nasvyazi.auth()
