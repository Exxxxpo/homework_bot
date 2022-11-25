import os
import sys
import time

import requests
from dotenv import load_dotenv
from telegram import Bot

load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Проверка доступности переменных окружения"""
    if not PRACTICUM_TOKEN and not TELEGRAM_TOKEN:
        sys.exit()


def send_message(bot, message):
    """Отправка сообщения пользователю"""
    bot.send_message(TELEGRAM_CHAT_ID, message)


def get_api_answer(timestamp):
    """Делаем запрос к эндпоинту API-сервиса"""
    try:
        response = requests.get(url=ENDPOINT, headers=HEADERS,
                                params={'from_date': timestamp})
        if response.status_code != 200:
            raise Exception
    except requests.exceptions.RequestException:
        SystemExit('Something wrong')
    # except requests.exceptions.ConnectionError as errc:
    #     print ("Error Connecting:", errc)
    print(response.json())
    return response.json()


def check_response(response):
    """Проверка API на соответствие документации"""
    if type(response) != dict:
        raise TypeError
    if 'homeworks' not in response:
        raise KeyError
    if type(response['homeworks']) != list:
        raise TypeError
def parse_status(homework):
    """Извлекает из информации о конкретной домашней работе статус работы"""
    try:
        homework_name = homework.get('homework_name')
        if not homework_name:
            raise KeyError
        verdict = HOMEWORK_VERDICTS[homework['status']]
        # if not homework.get('status'):
        #     raise KeyError
    except KeyError:
        raise Exception
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())  # int(time.time())
    cache_response = ''
    while True:
        try:
            response = get_api_answer(timestamp)
            check_response(response)
            print(response)
            if response != cache_response:
                message = parse_status(response.get('homeworks')[0])
                print(message)  # delete
                send_message(bot, message)
                cache_response = response
            time.sleep(5)  # set RETRY_PERIOD here

        except Exception as error:
            message = f'Сбой в работе программы: {error}'


if __name__ == '__main__':
    main()
