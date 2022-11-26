import logging
import os
import sys
import time
from http import HTTPStatus
from logging.handlers import RotatingFileHandler

import requests
import telegram
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

formatter = logging.Formatter(
    '%(asctime)s - %(levelname)s - %(message)s - %(name)s '
)
handler = RotatingFileHandler('homework.log', maxBytes=50000000, backupCount=5)
handler.setFormatter(formatter)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(handler)


def check_tokens():
    """Проверка доступности переменных окружения."""
    if not PRACTICUM_TOKEN or not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        logger.critical('Проверьте переменные окружения')
        sys.exit()


def send_message(bot, message):
    """Отправка сообщения пользователю."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.debug('Сообщение успешно отправлено!')
    except Exception as error:
        logger.error(error, 'Сообщение не удалось отправить!')


def get_api_answer(timestamp):
    """Делаем запрос к эндпоинту API-сервиса."""
    try:
        response = requests.get(url=ENDPOINT, headers=HEADERS,
                                params={'from_date': timestamp})
        if response.status_code != HTTPStatus.OK:
            logger.error('Ошибка подключения')
            raise Exception
    except requests.RequestException as error:
        logger.error(error, 'Сбой при запросе к эндпоинту')
    return response.json()


def check_response(response):
    """Проверка API на соответствие документации."""
    if type(response) != dict:
        logger.error('API возвращает не словарь')
        raise TypeError
    if 'homeworks' not in response:
        logger.error('нет ключа "homeworks"')
        raise KeyError
    if type(response['homeworks']) != list:
        logger.error('response["homeworks"] возвращает не список')
        raise TypeError


def parse_status(homework):
    """Извлекает из информации о конкретной домашней работе статус работы."""
    try:
        homework_name = homework['homework_name']
        verdict = HOMEWORK_VERDICTS[homework['status']]
        logger.info('Информация успешно обработана')
    except KeyError:
        logger.error('Неожиданный статус домашней работы')
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
                    last_date = response.get('homeworks')[0].get(
                        'date_updated')
                    time.sleep(RETRY_PERIOD)
                else:
                    logger.debug('Нет обновлений')
                    time.sleep(RETRY_PERIOD)
            else:
                logger.debug('Работа была отправлена на проверку')
                time.sleep(RETRY_PERIOD)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
            send_message(bot, message)
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
