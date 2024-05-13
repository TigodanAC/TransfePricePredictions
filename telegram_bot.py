import telebot
from telebot import types
import re
import threading
from data_requests import request

TOKEN = '6841505133:AAEoaz0vajJuO7xMhDmSPhnKwCJxbXQY-5E'

bot = telebot.TeleBot(TOKEN)
lock = threading.Lock()

bot_status = 'chat'
find_result = []
current_image_index = 0


def create_image_markup():
    markup = types.InlineKeyboardMarkup(row_width=3)
    prev_button = types.InlineKeyboardButton(text='<', callback_data='prev')
    stop_button = types.InlineKeyboardButton(text='Это он', callback_data='stop')
    next_button = types.InlineKeyboardButton(text='>', callback_data='next')
    back = types.InlineKeyboardButton(text='В начало', callback_data='back')
    markup.add(prev_button, stop_button, next_button, back)
    return markup


@bot.message_handler(commands=['start'])
def hello_message(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True,
                                       row_width=2)
    item_1 = types.KeyboardButton(text="Справка")
    item_2 = types.KeyboardButton(text="Предсказание цены")
    markup.add(item_1, item_2)
    bot.send_message(message.chat.id,
                     f"Здравствуй, {message.from_user.first_name}! Я телеграм-бот, который умеет предсказывать "
                     f"трансферную стоимость футболистов. Для начала работы выбери один из вариантов снизу!",
                     reply_markup=markup)
    global bot_status
    bot_status = 'chat'


@bot.message_handler(content_types=['text'])
def message_reply(message):
    global bot_status
    global find_result
    global current_image_index

    if message.text == "В начало":
        hello_message(message)
    elif message.text == "Справка":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True,
                                           row_width=3)
        item_1 = types.KeyboardButton(text="В начало")
        item_2 = types.KeyboardButton(text="Предсказание цены")
        item_3 = types.KeyboardButton(text="devbutton")
        markup.add(item_1, item_2, item_3)
        bot.send_message(message.chat.id,
                         "Данный бот может предсказывать цену футболиста, основываясь на данных с сайта transfermarkt. "
                         "Для этого вам необходимо нажать на кнопку 'Предсказание цены' ниже и ввести имя и фамилию "
                         "интересующего вас футболиста, после чего выбрать его из списка",
                         reply_markup=markup)
    elif message.text == "Предсказание цены":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True,
                                           row_width=1)
        item_1 = types.KeyboardButton(text="В начало")
        markup.add(item_1)
        bot.send_message(message.chat.id,
                         "Введите имя и фамилию футболиста, например 'Kylian Mbappé'",
                         reply_markup=markup)
        bot_status = 'request_name'
    elif message.text == "Чипи Чипи Чапа Чапа":
        with open('chipi-chapa.gif', 'rb') as gif:
            bot.send_animation(message.chat.id, animation=gif)
    elif message.text == "devbutton":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True,
                                           row_width=4)
        item_1 = types.KeyboardButton(text="В начало")
        item_2 = types.KeyboardButton(text="Справка")
        item_3 = types.KeyboardButton(text="Предсказание цены")
        item_4 = types.KeyboardButton(text="Чипи Чипи Чапа Чапа")
        item_5 = types.KeyboardButton(text="devbutton")
        markup.add(item_1, item_2, item_3, item_4, item_5)
        bot.send_message(message.chat.id, "You are in dev mode", reply_markup=markup)
    elif bot_status == 'request_name':
        find_result = request('GET', 1, message.text, lock)
        current_image_index = 0
        if find_result:
            markup = create_image_markup()
            img = find_result[0][0]
            cap = f"{current_image_index + 1} из {len(find_result)}\n" + find_result[0][1]
            bot.send_photo(message.chat.id, img, caption=cap, reply_markup=markup)
            bot_status = 'chat'
        else:
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True,
                                               row_width=1)
            item_1 = types.KeyboardButton(text="В начало")
            markup.add(item_1)
            bot.send_message(message.chat.id,
                             "Не удалось найти футболиста c таким именем, попробуйте ещё раз или вернитесь в начало",
                             reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "Простите, но я не совсем вас понимаю")


@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    global bot_status
    global find_result
    global current_image_index

    if call.data == 'back':
        bot_status = 'chat'
        hello_message(call.message)
    elif call.data == 'stop':
        bot.send_message(call.message.chat.id, "Я предсказываю...")

        request_result = request('GET', 2, ['predict', find_result[current_image_index][2]], lock)
        value0 = request_result[0][0]
        value1 = request_result[1][0]
        value = '{:,.0f}'.format(int((value0 + value1) / 2))
        real_price = '{:,.0f}'.format(request_result[-1].values[0])
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True,
                                           row_width=1)
        item_1 = types.KeyboardButton(text="В начало")
        markup.add(item_1)
        bot.send_message(call.message.chat.id,
                         f"Что цена этого футболиста примерно {value}€, "
                         f"тогда как цена этого футболиста на transfermarkt равна {real_price}€",
                         reply_markup=markup)
        bot_status = 'chat'
    else:
        markup = create_image_markup()

        if call.data == 'next':
            current_image_index = (current_image_index + 1) % len(find_result)
        elif call.data == 'prev':
            current_image_index = (current_image_index - 1) % len(find_result)

        img = find_result[current_image_index][0]
        cap = f"{current_image_index + 1} из {len(find_result)}\n" + find_result[current_image_index][1]

        bot.edit_message_media(chat_id=call.message.chat.id, message_id=call.message.message_id,
                               media=types.InputMediaPhoto(media=img), reply_markup=markup)
        bot.edit_message_caption(chat_id=call.message.chat.id, message_id=call.message.message_id, caption=cap,
                                 reply_markup=markup)


bot.polling(none_stop=True, interval=0)
