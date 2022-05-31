import configparser
import json

from telethon.sync import TelegramClient
from telethon import connection

#для корректного переноса времени сообщений в json
from datetime import date, datetime

#классы для работы с каналами
from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.types import ChannelParticipantsSearch

#класс для работы с сообщениями
from telethon.tl.functions.messages import GetHistoryRequest

import pprint

#Считываем учетные данные
config = configparser.ConfigParser()
config.read("config.ini")

#Присваиваем значения внутренним переменным
api_id   = config['Telegram']['api_id']
api_hash = config['Telegram']['api_hash']
username = config['Telegram']['username']

client = TelegramClient(username, api_id, api_hash)

client.start()

async def dump_all_participants(channel):
    """Записывает json-файл с информацией о всех участниках канала/чата"""
    offset_user = 0    # номер участника, с которого начинается считывание
    limit_user = 100   # максимальное число записей, передаваемых за один раз

    all_participants = []   # список всех участников канала
    filter_user = ChannelParticipantsSearch('')

    while True:
        participants = await client(GetParticipantsRequest(channel,
            filter_user, offset_user, limit_user, hash=0))
        if not participants.users:
            break
        all_participants.extend(participants.users)
        offset_user += len(participants.users)

    all_users_details = []   # список словарей с интересующими параметрами участников канала

    for participant in all_participants:
        all_users_details.append({"id": participant.id,
            "first_name": participant.first_name,
            "last_name": participant.last_name,
            "user": participant.username,
            "phone": participant.phone,
            "is_bot": participant.bot})

    with open('channel_users.json', 'w', encoding='utf8') as outfile:
        json.dump(all_users_details, outfile, ensure_ascii=False)
        
async def dump_all_messages(channel):
    """Записывает json-файл с информацией о всех сообщениях канала/чата"""
    offset_msg = 0    # номер записи, с которой начинается считывание
    limit_msg = 25   # максимальное число записей, передаваемых за один раз

    all_messages = []   # список всех сообщений
    dialog_output = []
    total_messages = 0
    total_count_limit = 25  # поменять это значение, если нужны не все сообщения

    class DateTimeEncoder(json.JSONEncoder):
        '''Класс для сериализации записи дат в JSON'''
        def default(self, o):
            if isinstance(o, datetime):
                return o.isoformat()
            if isinstance(o, bytes):
                return list(o)
            return json.JSONEncoder.default(self, o)

    while True:
        history = await client(GetHistoryRequest(
            peer=channel,
            offset_id=offset_msg,
            offset_date=None, add_offset=0,
            limit=limit_msg, max_id=0, min_id=0,
            hash=0))
        if not history.messages:
            break
        messages = history.messages
        for message in messages:
            all_messages.append(message.to_dict())
        offset_msg = messages[len(messages) - 1].id
        total_messages = len(all_messages)
        if total_count_limit != 0 and total_messages >= total_count_limit:
            break
                
    with open('channel_messages.json', 'w', encoding='utf8') as outfile:
         json.dump(all_messages, outfile, ensure_ascii=False, cls=DateTimeEncoder)

async def dump_only_messages():
    with open('channel_messages.json', 'r', encoding='utf8') as file:
        __stock = json.load(file)
        my_keys = ['message','date','peer_id'] #нужные ключи
        for stock in __stock:
            dialog_output = {}
            dialog_output[my_keys[0]] = stock['message']
            dialog_output[my_keys[1]] = stock['date']
            if stock['from_id']:
                dialog_output[my_keys[2]] = stock['from_id']['user_id']
            else:
                dialog_output[my_keys[2]] = 'unknown_id'
            for key in my_keys:
                print(dialog_output[key])
            print()
        
async def main():
    url = input("Введите ссылку на чат/юзернейм пользователя нужного чата: ")
    channel = await client.get_entity(url)
    await dump_all_messages(channel)
    await dump_only_messages()
    #await dump_all_participants(channel)
with client:
    client.loop.run_until_complete(main())