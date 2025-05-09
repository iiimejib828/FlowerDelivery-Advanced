# FlowerDelivery-Advanced

![Flower Shop](flower_shop/core/static/images/Flowershop.webp)

**FlowerDelivery-Advanced** — это веб-приложение на Django для управления цветочным магазином с функциями каталога, корзины, заказов и интеграцией с Telegram-ботом для уведомлений. Проект предоставляет удобный интерфейс для пользователей, администраторов и включает тестирование функциональности.

## Основные возможности

- **Каталог цветов**: Просмотр доступных цветов с добавлением в корзину.
- **Корзина**: Добавление, обновление и удаление товаров, оформление заказа с проверкой рабочего времени.
- **Заказы**: Управление заказами (просмотр истории, повторение, отмена) с уведомлениями в Telegram.
- **Профиль пользователя**: Регистрация, вход, редактирование данных (ФИО, телефон, адрес, Telegram ID).
- **Админ-панель**: Управление цветами, заказами, пользователями и рабочим временем.
- **Telegram-бот**: Уведомления о статусе заказов и обновлениях профиля, возможность отмены заказа.
- **Тестирование**: Полное покрытие тестами для моделей, представлений и форм.

## Технологии

- **Backend**: Django 4.x, Python 3.11+
- **Frontend**: Bootstrap 5.3, HTML/CSS/JavaScript
- **База данных**: SQLite (по умолчанию, можно настроить PostgreSQL)
- **Telegram API**: Aiogram для интеграции с ботом
- **Тестирование**: Django Test Framework, Pytest
- **Дополнительно**: Django Signals, Session Management

## Установка

### Требования

- Python 3.11+
- Git
- Виртуальное окружение (рекомендуется)
- Telegram-бот (токен для интеграции)

### Шаги

1. **Клонируйте репозиторий**:
   ```bash
   git clone https://github.com/iiimejib828/FlowerDelivery-Advanced.git
   cd FlowerDelivery-Advanced
2. **Создайте и активируйте виртуальное окружение**:
   ```
   python -m venv venv 
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
3. **Установите зависимости**:
   ```
   pip install -r requirements.txt
4. **Настройте работу с телеграм: Создайте файл bot/config.py и добавьте**:
   ```
   TOKEN = 'YOUR BOT TOKEN'
   ADMIN_IDS = [123456789]  # Укажите Tekegram ID администраторов
5. **Примените миграции**:
   ```
   python manage.py migrate
6. **Создайте суперпользователя**:
   ```
   python manage.py createsuperuser
7. **Запустите сервер**:
   ```
   python manage.py runserver
8. **Доступ**:
   - Веб-приложение: http://127.0.0.1:8000/
   - Админ-панель: http://127.0.0.1:8000/admin/
   - Telegram-бот: @flowershop_delivery_bot

## Структура проекта
- flower_shop/ — Основные настройки проекта (settings.py, urls.py, wsgi/asgi).
- catalog/ — Модуль каталога цветов.
- cart/ — Модуль управления корзиной и оформлением заказов.
- orders/ — Модуль управления заказами.
- users/ — Модуль аутентификации и профилей пользователей.
- core/ — Главная страница и базовые шаблоны.
- bot/ — Логика Telegram-бота.
## Использование
### Регистрация и вход:
- Зарегистрируйтесь через /register/ или войдите через /login/.
- Обновите профиль на /profile/, добавив Telegram ID для уведомлений.
### Работа с каталогом:
- Перейдите в каталог через /catalog/ и добавьте цветы в корзину.
### Оформление заказа:
- Перейдите в корзину (/cart/), проверьте товары и оформите заказ.
### История заказов:
- Просмотрите заказы на /orders/, повторите или отмените их при необходимости.
### Telegram-уведомления:
- Привяжите Telegram ID в профиле и отправьте /start боту для получения уведомлений.
### Тестирование
- Запустите тесты с помощью:
pytest
- Тесты покрывают модели, представления, формы и интеграцию.

## Контрибьютинг
- Форкните репозиторий.
- Создайте ветку (git checkout -b feature/ваша-фича).
- Внесите изменения и закоммитьте (git commit -m "Добавлена фича").
- Отправьте в ваш форк (git push origin feature/ваша-фича).
- Создайте Pull Request.

## Лицензия
- Проект распространяется под лицензией MIT. См. файл LICENSE для подробностей.

## Контакты
- Репозиторий: github.com/iiimejib828/FlowerDelivery-Advanced
- Telegram-бот: @flowershop_delivery_bot
