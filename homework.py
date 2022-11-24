import os
import time

import requests
import telegram
from telegram import Bot
from dotenv import load_dotenv

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
    pass


def send_message(bot, message):
    bot.send_message(TELEGRAM_CHAT_ID, message)

def get_api_answer(timestamp):
    response = requests.get(ENDPOINT, headers=HEADERS, params={'from_date': timestamp})
    answer = response.json()['homeworks'][0]
    return answer


def check_response(response):
    pass


def parse_status(homework):
    homework_name = homework.get('homework_name')
    verdict = HOMEWORK_VERDICTS[homework['status']]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""

    bot = Bot(token=TELEGRAM_TOKEN)
    timestamp = 0
    message = parse_status(get_api_answer(timestamp))
    print(message)
    send_message(bot, message)

    # while True:
    #     try:
    #
    #
    #     except Exception as error:
    #         message = f'Сбой в работе программы: {error}'


if __name__ == '__main__':
    main()
