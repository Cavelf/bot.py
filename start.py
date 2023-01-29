import requests
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

def start(self):
    for event in longpoll.listen():
        if event.type == VkEventType.MESSAGE_NEW and event.to_me:
            text = event.text.lower()
            if text == 'start':
                keyboard = VkKeyboard(one_time=False)
                keyboard.add_button('Да', color=VkKeyboardColor.POSITIVE)
                keyboard.add_button('Нет', color=VkKeyboardColor.NEGATIVE)
                keyboard.add_button('Help', color=VkKeyboardColor.SECONDARY)
                self.write_msg(event.user_id, f'Привет! \n'
                                              f'Это VKinder \n'
                                              f'Найти пару?', keyboard=keyboard)
                for event in longpoll.listen():
                    if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                        text = event.text.lower()
                        if text == 'да':
                            bot.start_vkinder(event)
                        elif text == 'нет':
                            self.write_msg(event.user_id, 'Заходите еще!')
                            bot.start()
                        elif text == 'help':
                            self.write_msg(event.user_id, 'Приложение для поиска партнера, нажмите start для \
                                                          запуска бота. Заполните данные для \
                                                          поиска партнера')
                            bot.start()
                        else:
                            self.write_msg(event.user_id, 'Ошибка ввода данных')
            else:
                if text != 'stop':
                    self.write_msg(event.user_id, 'Пока, до встречи!')
                    bot.stop()
                    break