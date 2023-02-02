import requests
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor
import os
import random
from random import randrange
from database import Session, User, MatchingUser, Photos, BlacklistedUser
from config import * #token_user, token_search


#token_user = config.token_user
#token_search = config.token_search
class VKinder_bot:

    def __init__(self, token_user: str, token_search: str):
        self.token_user = token_user
        self.token_search = token_search
        self.token_user = vk_api.VkApi(token=token_user)
        self.token_search = vk_api.VkApi(token=token_search)


    def config_read(self):
        '''
        Функция читает необходимые токены из файла для использования в коде.
        Предназначена для соблюдения мер безопасности,
         по использованию персональных данных.
        Результатом выполнения функции являются переменные,
        в которых хранятся ключи доступа для использования VK_API:
        ключ доступа пользователя и ключ доступа сообщества.
        '''
        config = 'all_tokens.config'
        contents = open(config).read()
        config = eval(contents)
        token_user = config['token_user']
        token_search = config['token_search']
        return token_user, token_search


    def get_vk(self, url, new_params, **kwargs):
        params = {
            'access_token': token_search,
            'v': '5.131'
        }
        params.update(new_params)
        response = requests.get(url, params=params, **kwargs)
        if response.status_code != requests.codes.ok:
            print(f'Ошибка при запросе к серверу: {response.text}')
            return None

        result = response.json()

        if 'error' in result:
            print(f'Ошибка в данных: {result["error"]}')
            return None

        if 'errors' in result:
            print(f'Ошибка в данных: {result["errors"]}')
            return None
        return result['response']

    def get_params(add_params: dict = None):
        params = {
            'access_token': token_user,
            'v': '5.131'
        }
        if add_params:
            params.update(add_params)
        return params

    def write_msg(self, user_id, message, keyboard=None):
        post = {'chat_id': user_id, 'message': message, 'random_id': randrange(10 ** 7)}
        if keyboard != None:
            post['keyboard'] = keyboard.get_keyboard()
        else:
            post = post
        vk.method('messages.send', post)
#        vk.method('messages.send', {'chat_id': user_id, 'message': message, 'random_id': random.randint(0, 2048)})

       # получаем имя и фамилию пользователя
    def get_user_name(self):
        response = requests.get(
            'https://api.vk.com/method/users.get', self.get_params({'user_ids': self.user_id})
        )
        resp = response.json()
        items = resp.get('response', {})
        if not items:
            return None
        for user_info in items :
            self.first_name = user_info['first_name']
            self.last_name = user_info['last_name']
        return self.first_name, self.last_name

    def start(self):
        for event in longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                text = event.text.lower()
                if text == 'start':
                    keyboard = VkKeyboard(one_time=False)
                    keyboard.add_button('Да', color=VkKeyboardColor.POSITIVE)
                    keyboard.add_button('Нет', color=VkKeyboardColor.NEGATIVE)
                    keyboard.add_button('Help', color=VkKeyboardColor.SECONDARY)
                    self.write_msg(event.chat_id, f'Привет! \n'
                                                  f'Это VKinder \n'
                                                  f'Найти пару?', keyboard=keyboard)
                    for event in longpoll.listen():
                        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                            text = event.text.lower()
                            text = text.split(' ')[-1]
                            if text == 'да':
                                self.start_vkinder(event)
                            elif text == 'нет':
                                self.write_msg(event.chat_id, 'Заходите еще!')
                                #bot.start()
                                self.start()
                            elif text == 'help':
                                self.write_msg(event.chat_id, 'Приложение для поиска партнера, нажмите start для \
                                                              запуска бота. Заполните данные для \
                                                              поиска партнера')
                                #bot.start()
                                self.start()
                            else:
                                self.write_msg(event.chat_id, 'Ошибка ввода данных')
                else:
                    if text != 'start':
                        self.write_msg(event.chat_id, 'Для запуска наберите - start')
                        #bot.start()
                        self.start()
                        
    def start_vkinder(self, event):
        session = Session()
        dating_id = event.chat_id
        user = session.query(User).filter(User.dating_id == dating_id).all()

        if len(user) == 0:
            self.get_user(event.chat_id)
            return self.start_vkinder
        else:
            self.search_partner_command(event)
            print('search_partner_command(')

    def search_partner_command(self, event):
        print('search_partner_command(')
        session = Session()
        user = session.query(User).all()
        age_from = user[0].age_from
        age_to = user[0].age_to
        city = user[0].city
        partners_sex = user[0].partners_sex

        print("sex: {}, city: {}, age: {}-{}".format(partners_sex, city, age_from, age_to))

        self.choose_partner(event, partners_sex, city, age_to, age_from)

    def choose_partner(self, event, partners_sex, city, age_to, age_from):
        keyboard = VkKeyboard(one_time=False)
        keyboard.add_button('Нравится', color=VkKeyboardColor.PRIMARY)
        keyboard.add_button('Не нравится', color=VkKeyboardColor.NEGATIVE)
        keyboard.add_button('Понравившиеся', color=VkKeyboardColor.POSITIVE)
        keyboard.add_button('Изменить параметры', color=VkKeyboardColor.PRIMARY)
        self.write_msg(event.chat_id, 'Поиск', keyboard=keyboard)

        partners_get = self.search_partner(partners_sex, city, age_to, age_from)
        list_partners = []
        for partners in partners_get:
            if partners['is_closed'] is False:
                partner_id = (partners['first_name'], partners['last_name'], partners['id'])
                list_partners.append(partner_id)

        session = Session()
        id_dater = event.chat_id
        liked_users = session.query(MatchingUser).filter(MatchingUser.id_dater == id_dater).all()
        ignore_users = session.query(BlacklistedUser).filter(BlacklistedUser.id_dater == id_dater).all()

        bd_id = []
        for match_id in liked_users:
            us_id = match_id.matching_id
            bd_id.append(us_id)

        for ign_id in ignore_users:
            ig_id = ign_id.blacklisted_id
            bd_id.append(ig_id)

        for partner in list_partners:
            if partner[2] not in list(bd_id):
                photo_list = self.choose_photo(partner[2])
                photo_dict = {}
                if photo_list['count'] >= 3:
                    for photo in photo_list['items']:
                        photo_id = photo['id']
                        likes = photo['likes']['count']
                        photo_dict[likes] = f'photo{partner[2]}_{photo_id}'
                else:
                    pass
                sorted_photo_dict = {}
                for k in sorted(photo_dict.keys(), reverse=True):
                    sorted_photo_dict[k] = photo_dict[k]
                photos = list(sorted_photo_dict.values())[0:3]

                link_photo = []
                for photog in photo_list['items']:
                    if photog['likes']['count'] in list(sorted_photo_dict.keys())[0:3]:
                        link_photo.append([photog['id'], photog['likes']['count'], photog['sizes'][-1]['url']])

                self.write_msg(event.chat_id, partner[0] + ' ' + partner[1])

                link = 'https://vk.com/id' + str(partner[2])
                self.write_msg(event.chat_id, link)
                for photo_send in photos:
                    self.send_photo(event.chat_id, photo_send)
                print('foto')
                for event in longpoll.listen():
                    if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text:
                        text = event.text
                        if text == 'Нравится':
                            self.add_liked_partner(link_photo, partner[2])
                            break
                        elif text == 'Не нравится':
                            self.add_ignore(partner)
                            break
                        elif text == 'Понравившиеся':
                            self.show_liked(event)
                            break
                        elif text == 'Изменить параметры':
                            self.update_user_data(event)
                            break
                        else:
                            self.write_msg(event.chat_id, 'Ошибка данных, попробуй еще')

    def get_user(self, user_id):
        session = Session()
        info = self.get_vk('https://api.vk.com/method/users.get', {'user_ids': user_id})[0]
        first_name = info['first_name']
        last_name = info['last_name']


        city = self.get_city(user_id)
        sex = self.get_gender(user_id)
        age_to = self.get_age_to(user_id)
        age_from = self.get_age_from(user_id)

        user = User(dating_id=user_id, first_name=first_name, last_name=last_name, age_to=age_to, age_from=age_from,
                    city=city, partners_sex=sex)
        session.add(user)
        session.commit()

        self.write_msg(user_id, f'Пользователь {user_id} добавлен')

    def get_gender(self, user_id):
        keyboard = VkKeyboard(one_time=True)
        keyboard.add_button('Девушка', color=VkKeyboardColor.PRIMARY)
        keyboard.add_button('Парень', color=VkKeyboardColor.SECONDARY)
        self.write_msg(user_id, 'Какого пола нужен партнер ?', keyboard=keyboard)
        for event in longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text:
                text = event.text
                if text == 'Девушка':
                    self.gender = '1'
                elif text == 'Парень':
                    self.gender = '2'
                else:
                    self.write_msg(user_id, 'Выберите: девушка или парень')
                    bot.get_gender(user_id)
                return self.gender

    def get_city(self, user_id):
        self.write_msg(user_id, 'В каком городе искать партнера ?')
        for event in longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text:
                self.city_name = event.text
                self.city = self.get_vk(f'https://api.vk.com/method/database.getCities', {'country_id': '1',
                                                                                          'q': self.city_name,
                                                                                          'count': '1'})['items']
                if len(self.city) == 0:
                    self.write_msg(user_id, f'Не нашел города с названием {self.city_name}')
                    bot.get_city(user_id)
                else:
                    self.city = self.city_name
                return self.city

    def get_age_to(self, user_id):
        self.write_msg(user_id, 'Укажите максимальный возраст')
        for event in longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text:
                self.age_to = event.text.lower()
                return self.age_to

    def get_age_from(self, user_id):
        self.write_msg(user_id, 'Укажите минимальный возраст возраст')
        for event in longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text:
                self.age_from = event.text.lower()
                return self.age_from

    def search_partner(self, partners_sex, city, age_to, age_from):
        partners = self.get_vk('https://api.vk.com/method/users.search', {'is_closed': 'False', 'has_photo': '1',
                                                                          'sex': partners_sex,
                                                                          'status': '6', 'hometown': city,
                                                                          'age_from': age_from,
                                                                          'age_to': age_to, 'count': '20'})['items']

        return partners

    def choose_photo(self, partner_id):
        photo_list = self.get_vk('https://api.vk.com/method/photos.get', {'owner_id': partner_id,
                                                                          'album_id': 'profile',
                                                                          'extended': '1',
                                                                          'count': '20',
                                                                          'photo_sizes': '0'})

        return photo_list

    def send_photo(self, user_id, photo_send):
        response = self.get_vk(f'https://api.vk.com/method/messages.send', {'access_token': token_user,
                                                                            'user_id': user_id,
                                                                            'random_id': random.getrandbits(64),
                                                                            'attachment': photo_send,
                                                                            'v': 5.131})
        return response

    def add_liked_partner(self, link_photo, partner_id):
        session = Session()
        user = session.query(User).all()
        id_dater = user[0].dating_id
        like_partner_info = self.get_vk('https://api.vk.com/method/users.get', {'user_ids': partner_id,
                                                                                'fields': 'sex'})[0]

        first_name = like_partner_info['first_name']
        last_name = like_partner_info['last_name']
        sex = like_partner_info['sex']

        like_partner = MatchingUser(matching_id=partner_id, first_name=first_name, last_name=last_name, id_dater=id_dater, sex=sex)
        session.add(like_partner)
        session.commit()

        for photo in link_photo:
            pic_link = photo[2]
            pic_likes = photo[1]
            photo = Photos(id_matcher=partner_id, photo_link=pic_link, likes_count=pic_likes)
            session.add(photo)
            session.commit()

    def add_ignore(self, partner):
        session = Session()
        user = session.query(User).all()

        id_dater = user[0].dating_id
        blacklisted_id = partner[2]
        first_name = partner[0]
        last_name = partner[1]

        ignore_user = BlacklistedUser(blacklisted_id=blacklisted_id, first_name=first_name, last_name=last_name, id_dater=id_dater)
        session.add(ignore_user)
        session.commit()

    def show_liked(self, event):
        keyboard = VkKeyboard(one_time=False)
        keyboard.add_button('Продолжить поиск', color=VkKeyboardColor.PRIMARY)

        session = Session()

        id_dater = event.chat_id
        liked_users = session.query(MatchingUser).filter(MatchingUser.id_dater == id_dater).all()

        for liked_user in liked_users:
            first_name = liked_user.first_name
            last_name = liked_user.last_name
            us_id = liked_user.matching_id
            user_info = first_name + ' ' + last_name + ' ' + 'https://vk.com/id' + str(us_id)
            self.write_msg(event.chat_id, user_info)

        self.write_msg(event.chat_id, 'Продолжить поиск ?', keyboard=keyboard)
        for event in longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me and event.text:
                text = event.text
                if text == 'Продолжить поиск':
                    self.search_partner_command(event)

    def update_user_data(self, event):
        session = Session()
        user = session.query(User).all()[0]
        us_id = user.dating_id

        city = self.get_city(us_id)
        sex = self.get_gender(us_id)
        age_to = self.get_age_to(us_id)
        age_from = self.get_age_from(us_id)

        session.query(User).filter(User.dating_id == us_id).update({'age_from': age_from,
                                                                    'age_to': age_to,
                                                                    'partners_sex': sex,
                                                                    'city': city})
        session.commit()
        self.write_msg(event.chat_id, 'Информация обновлена')
        self.search_partner_command(event)


if __name__ == "__main__":

    bot = VKinder_bot(token_user, token_search)
    vk = vk_api.VkApi(token = token_user)
    longpoll = VkLongPoll(vk)
    bot.start()
