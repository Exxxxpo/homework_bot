import os
import sys
import time
import logging

import requests
from dotenv import load_dotenv
import telegram

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
logging.basicConfig(
    level=logging.DEBUG,
    filename='main.log',
    format='%(asctime)s, %(levelname)s, %(message)s, %(name)s'
)

def check_tokens():
    """Проверка доступности переменных окружения"""
    if not PRACTICUM_TOKEN and not TELEGRAM_TOKEN:
        logging.critical('Проверьте переменные окружения')
        sys.exit()


def send_message(bot, message):
    """Отправка сообщения пользователю"""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.debug('Сообщение отправлено ботом!')
    except Exception as error:
        logging.error(error, 'Сообщение не отправилось ботом')


def get_api_answer(timestamp):
    """Делаем запрос к эндпоинту API-сервиса"""
    try:
        response = requests.get(url=ENDPOINT, headers=HEADERS,
                                params={'from_date': timestamp})
        if response.status_code != 200:
            logging.error('Status code error')
            raise Exception
    except requests.exceptions.RequestException:
        logging.error('Сбой при запросе к эндпоинту')
        raise Exception
        # SystemExit('Something wrong')
    # except requests.exceptions.ConnectionError as errc:
    #     print ("Error Connecting:", errc)
    # print(response.json())
    return response.json()

def check_response(response):
    """Проверка API на соответствие документации"""
    if type(response) != dict:
        logging.error('API возвращает не словарь')
        raise TypeError
    if 'homeworks' not in response:
        logging.error('нет ключа "homeworks"')
        raise KeyError
    if type(response['homeworks']) != list:
        logging.error('response["homeworks"] возвращает не список')
        raise TypeError
    # if not response.get('homeworks'):
    #     logging.error('response["homeworks"] не имеет значения')
    #     raise Exception
def parse_status(homework):
    """Извлекает из информации о конкретной домашней работе статус работы"""
    try:
        homework_name = homework.get('homework_name')
        if not homework_name:
            logging.error('Нет ключа homework_name')
            raise KeyError
        verdict = HOMEWORK_VERDICTS[homework['status']]
        # if not homework.get('status'):
        #     raise KeyError
    except KeyError:
        logging.error('Wrong key')
        raise Exception
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())  # int(time.time())
    last_date = 0
    while True:
        try:
            response = get_api_answer(timestamp)
            print(response)
            check_response(response)
            if len(response.get('homeworks')) > 0:
                if response.get('homeworks')[0].get('date_updated') != last_date:
                    message = parse_status(response.get('homeworks')[0])
                    send_message(bot, message)
                    print('ok')
                    last_date = response.get('homeworks')[0].get('date_updated')
                    time.sleep(RETRY_PERIOD)  # set RETRY_PERIOD here
                else:
                    time.sleep(RETRY_PERIOD)
                    print('ждемс')

            else:
                print('Вы не отправили работу')
                time.sleep(RETRY_PERIOD)
            timestamp += RETRY_PERIOD

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(error)


if __name__ == '__main__':
    main()
