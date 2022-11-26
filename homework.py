import os
import sys
import time
import logging

import requests
from dotenv import load_dotenv
import telegram
from logging.handlers import RotatingFileHandler

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
# logging.basicConfig(
#     level=logging.DEBUG,
#     filename='main.log',
#     format='%(asctime)s, %(levelname)s, %(message)s, %(name)s',
# )
formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s - %(name)s '
)
handler = RotatingFileHandler('homework.log', maxBytes=50000000, backupCount=5)
handler.setFormatter(formatter)
# handler.setLevel(logging.DEBUG)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)
# logging.addHandler(handler)

def check_tokens():
    """Проверка доступности переменных окружения"""
    if not PRACTICUM_TOKEN and not TELEGRAM_TOKEN:
        logger.critical('Проверьте переменные окружения')
        sys.exit()
    # return True


def send_message(bot, message):
    """Отправка сообщения пользователю"""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.debug('Сообщение отправлено ботом!')
    except Exception as error:
        logger.error(error, 'Сообщение не отправилось ботом')


def get_api_answer(timestamp):
    """Делаем запрос к эндпоинту API-сервиса"""
    try:
        response = requests.get(url=ENDPOINT, headers=HEADERS,
                                params={'from_date': timestamp})
        if response.status_code != 200:
            logger.error('Status code error')
            raise Exception
    except requests.exceptions.RequestException:
        logger.error('Сбой при запросе к эндпоинту')
        raise Exception
    except requests.exceptions.ConnectionError:
        raise Exception
    except requests.exceptions.HTTPError:
        raise Exception
    except requests.exceptions.Timeout:
        raise Exception

        # SystemExit('Something wrong')
    # except requests.exceptions.ConnectionError as errc:
    #     print ("Error Connecting:", errc)
    # print(response.json())
    return response.json()


def check_response(response):
    """Проверка API на соответствие документации"""
    if type(response) != dict:
        logger.error('API возвращает не словарь')
        raise TypeError
    if 'homeworks' not in response:
        logger.error('нет ключа "homeworks"')
        raise KeyError
    if type(response['homeworks']) != list:
        logger.error('response["homeworks"] возвращает не список')
        raise TypeError
    # return True
    # if not response.get('homeworks'):
    #     logger.error('response["homeworks"] не имеет значения')
    #     raise Exception


def parse_status(homework):
    """Извлекает из информации о конкретной домашней работе статус работы"""
    try:
        homework_name = homework.get('homework_name')
        if not homework_name:
            logger.error('Нет ключа homework_name')
            raise KeyError
        verdict = HOMEWORK_VERDICTS[homework['status']]
        # if not homework.get('status'):
        #     raise KeyError
    except KeyError:
        logger.error('Wrong key')
        raise Exception
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    last_date = 0
    while True:
        try:
            response = get_api_answer(timestamp)
            check_response(response)
            if len(response.get('homeworks')) > 0:
                if response.get('homeworks')[0].get(
                        'date_updated') != last_date:
                    message = parse_status(response.get('homeworks')[0])
                    send_message(bot, message)
                    print('ok')
                    last_date = response.get('homeworks')[0].get(
                        'date_updated')
                    time.sleep(RETRY_PERIOD)  # set RETRY_PERIOD here
                else:
                    time.sleep(RETRY_PERIOD)
                    logger.info('Нет обновлений')
                    print('ждемс')

            else:
                print('Вы не отправили работу')
                logger.info('Работа не отправлена')
                time.sleep(RETRY_PERIOD)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(error)
            send_message(bot, message)
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
