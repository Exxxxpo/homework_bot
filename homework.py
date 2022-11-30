import logging
import os
import sys
import time
from http import HTTPStatus
from logging.handlers import RotatingFileHandler

import requests
import telegram
from dotenv import load_dotenv

from exceptions import StatusCodeError

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
    'rejected': 'Работа проверена: у ревьюера есть замечания.',
}

formatter = logging.Formatter(
    '%(asctime)s [%(levelname)s] | '
    '(%(filename)s).%(funcName)s:%(lineno)d | %(message)s'
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
        sys.exit(1)
    logger.debug('Переменные окружения успешно загружены')


def send_message(bot, message):
    """Отправка сообщения пользователю."""
    try:
        logger.debug('Подготовка к отправке сообщения')
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except telegram.error.TelegramError as error:
        logger.error(error, exc_info=True)
    else:
        logger.debug('Сообщение успешно отправлено!')


def get_api_answer(timestamp):
    """Делаем запрос к эндпоинту API-сервиса."""
    try:
        logger.debug('Делаем запрос к API')
        response = requests.get(
            url=ENDPOINT, headers=HEADERS, params={'from_date': timestamp}
        )
        if response.status_code != HTTPStatus.OK:
            logger.error(f'Ошибка подключения! Код - {response.status_code}')
            raise StatusCodeError(f'Статус сервера: {response.status_code}')
    except requests.RequestException:
        logger.error('Ошибка подключения к эндпоинту')
    else:
        logger.debug('Ответ от API успешно получен')
    return response.json()


def check_response(response):
    """Проверка API на соответствие документации."""
    if not isinstance(response, dict):
        logger.error('API возвращает не словарь')
        raise TypeError('API возвращает не словарь')
    if 'homeworks' not in response:
        logger.error('нет ключа "homeworks"')
        raise KeyError('нет ключа "homeworks"')
    if not isinstance(response['homeworks'], list):
        logger.error('response["homeworks"] возвращает не список')
        raise TypeError('response["homeworks"] возвращает не список')


def parse_status(homework):
    """Извлекает из информации о конкретной домашней работе статус работы."""
    try:
        homework_name = homework['homework_name']
        verdict = HOMEWORK_VERDICTS[homework['status']]
        logger.info('Информация успешно обработана')
    except KeyError:
        logger.error('Неожиданный статус домашней работы')
        return f'У работы "{homework_name}". неизвестный статус {verdict}'
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    check_tokens()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    last_message = None
    while True:
        try:
            response = get_api_answer(timestamp)
            check_response(response)
            if (
                len(response.get('homeworks')) > 0
                and parse_status(response.get('homeworks')[0]) != last_message
            ):
                message = parse_status(response.get('homeworks')[0])
                send_message(bot, message)
                last_message = parse_status(response.get('homeworks')[0])
            else:
                logger.debug('Нет обновлений')
        except telegram.error.TelegramError as e:
            logger.error(f'При отправлении сообщения возникла ошибка {e}')
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
            if message != last_message:
                send_message(bot, message)
                last_message = message
        finally:
            timestamp = response.get('current_date')
            time.sleep(RETRY_PERIOD)
            logger.debug('Таймер закончил работу')


if __name__ == '__main__':
    main()
