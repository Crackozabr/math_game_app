## Математическая карточная игра "Мир компонентов"

Добро пожаловать в проект "Мир компонентов" — это многопользовательская онлайн-игра, в которой игроки соревнуются, составляя математические выражения из карт в руке, чтобы получить числа, лежащие на столе. Используйте свои навыки арифметики и стратегии, чтобы набрать 15 очков и победить!

Проект реализован с использованием **Flask** и **Socket.IO** для обеспечения реального времени взаимодействия между игроками. Frontend построен с использованием HTML, CSS (с Bootstrap) и JavaScript.

---

## Оглавление

- [Описание проекта](#описание-проекта)
- [Правила игры](#правила-игры)
- [Требования](#требования)
- [Установка](#установка)
- [Запуск проекта](#запуск-проекта)
- [Структура проекта](#структура-проекта)
- [Использование](#использование)
- [Особенности](#особенности)
- [Разработка](#разработка)
- [Авторы](#авторы)
- [Лицензия](#лицензия)

---

## Описание проекта

"Мир компонентов" — это математическая карточная игра, где игроки используют карты с числами для составления математических выражений (сложение, умножение, комбинации вида `(A+B)*C` или `A*B+C`). Цель игры — набрать 15 очков, забирая карты со стола, которые соответствуют результатам ваших выражений.

Игра поддерживает от 2 до 4 игроков. Игроки могут создавать новые игры, присоединяться к существующим, общаться в чате и играть в реальном времени. После окончания игры игроки могут выбрать сыграть ещё раз или завершить игру.

---

## Правила игры

### Цель игры
Набрать **15 очков** первым, составляя математические выражения из карт в руке, чтобы получить числа, лежащие на столе.

### Очки
- Использование **2 карт** (сложение или умножение) = **1 очко**.
- Использование **3 карт** (сложение или умножение) = **2 очка**.
- Использование **3 карт** с комбинацией `(A+B)*C` или `A*B+C` = **3 очка**.

### Ход игры
1. Каждый игрок получает **5 карт чисел** в руку. На столе лежат **5 карт ответов**.
2. В свой ход игрок выбирает 2 или 3 карты из руки и операцию (Сложить, Умножить, `(A+B)*C`, `A*B+C`), чтобы получить число, которое есть на столе.
3. Если ход успешен:
   - Карты из руки уходят.
   - Карта со стола забирается.
   - Игрок получает очки.
   - Рука пополняется до 5 карт из колоды чисел.
   - Если на столе меньше 5 карт, стол пополняется из колоды ответов.
4. Вместо хода игрок может взять карту из колоды чисел.
5. Ход передаётся следующему игроку.

### Конец игры
- Первый игрок, набравший **15 очков**, побеждает.
- После победы игроки могут выбрать: сыграть ещё раз или завершить игру.

---

## Требования

Для запуска проекта вам понадобится:

- **Python 3.8+**
- Виртуальное окружение (рекомендуется)
- Браузер (Google Chrome, Firefox или другой современный браузер)

### Зависимости
Зависимости перечислены в файле `requirements.txt`:
- `Flask==3.0.0`
- `Flask-SocketIO==5.3.6`
- `eventlet==0.36.1` (для асинхронной работы Socket.IO)

---

## Установка

1. **Клонируйте репозиторий**:
   ```bash
   git clone https://github.com/Crackozabr/math_game_app.git
   cd math-cards-game
   ```

2. **Создайте и активируйте виртуальное окружение**:
   ```bash
   python -m venv env
   source env/bin/activate  # Для Windows: env\Scripts\activate
   ```

3. **Установите зависимости**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Убедитесь, что у вас есть папка `static`**:
   - В папке `static` должен находиться файл `background.png` (фон для игры).
   - (Опционально) Если вы добавили звуковые эффекты, например `new-game.mp3`, он также должен быть в папке `static`.

5. **Убедитесь, что у вас есть папка `templates`**:
   - В папке `templates` должны быть файлы:
     - `index.html` (главная страница)
     - `waiting.html` (страница ожидания игроков)
     - `game.html` (страница самой игры)

---

## Запуск проекта

1. **Запустите сервер**:
   ```bash
   python server.py
   ```

2. **Откройте игру в браузере**:
   - Перейдите по адресу: `http://localhost:5000`
   - Если вы запускаете на другом устройстве в локальной сети, используйте IP-адрес сервера, например: `http://192.168.1.100:5000`.

---

## Структура проекта

```
math_game_app/
│
├── server.py              # Основной серверный файл (логика игры, маршруты, Socket.IO)
├── requirements.txt       # Список зависимостей
├── README.md              # Документация проекта
│
├── static/                # Статические файлы
│   ├── background.png     # Фоновое изображение
│   └── new-game.mp3       # (Опционально) Звук для уведомления о новой игре
│
└── templates/             # HTML-шаблоны
    ├── index.html         # Главная страница (список игр, создание/присоединение)
    ├── waiting.html       # Страница ожидания игроков
    └── game.html          # Страница самой игры
```

---

## Использование

1. **Создание игры**:
   - На главной странице введите своё имя и нажмите "Создать игру".
   - Вы будете перенаправлены на страницу ожидания, где сможете дождаться других игроков.
   - Когда в игре будет от 2 до 4 игроков, создатель может нажать "Начать игру".

2. **Присоединение к игре**:
   - На главной странице введите своё имя.
   - Выберите доступную игру из списка и нажмите "Присоединиться к игре".
   - Вы попадёте на страницу ожидания, где будете ждать, пока создатель начнёт игру.

3. **Игра**:
   - Используйте карты в руке, чтобы составить выражение, равное числу на столе.
   - Выбирайте операцию (Сложить, Умножить, `(A+B)*C`, `A*B+C`) и подтверждайте ход.
   - Если не можете сделать ход, возьмите карту из колоды.
   - Общайтесь с другими игроками через чат.

4. **Конец игры**:
   - После победы одного из игроков (15 очков) появится модальное окно с результатами.
   - Вы можете выбрать "Сыграть ещё" (все игроки должны согласиться) или "Закончить игру".

---

## Особенности

- **Реальное время**: Используется Socket.IO для обновления списка игр, чата и игрового процесса в реальном времени.
- **Многопользовательская игра**: Поддержка от 2 до 4 игроков.
- **Чат**: Игроки могут общаться в чате во время игры.
- **Динамическое обновление списка игр**: Новые игры появляются на главной странице без необходимости обновления.
- **Адаптивный дизайн**: Интерфейс адаптирован для разных устройств (с использованием Bootstrap).
- **Уведомления**: Системные сообщения о присоединении/отключении игроков.

---

## Разработка

### Технологии
- **Backend**: Flask, Flask-SocketIO, Python
- **Frontend**: HTML, CSS (Bootstrap 5), JavaScript
- **Реальное время**: Socket.IO

### Добавление новых функций
1. **Добавление звуков**:
   - Поместите звуковые файлы в папку `static`.
   - Добавьте `<audio>` элементы в HTML и проигрывайте их через JavaScript.

2. **Новые операции**:
   - В `server.py` в методе `process_play` класса `Game` добавьте новые операции (например, деление или вычитание).
   - Обновите интерфейс в `game.html`, добавив новые кнопки для операций.

3. **Локализация**:
   - Создайте файлы с переводами (например, JSON-файлы).
   - Обновите шаблоны и JavaScript для поддержки нескольких языков.

### Отладка
- Логи сервера выводятся в консоль (например, подключения, ходы, ошибки).
- Используйте `console.log` в JavaScript для отладки клиентской части.

---

## Авторы

- **Crackozabra** — основной разработчик.
- **Grok (xAI)** — помощник в разработке и отладке.

---

## Лицензия

Этот проект распространяется под лицензией **MIT**. Подробности см. в файле `LICENSE`.

