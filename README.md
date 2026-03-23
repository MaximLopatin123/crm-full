# МОЯ CRM

Лёгкая CRM система с общей базой данных.

## Логины
| Кто     | Логин     | Пароль     |
|---------|-----------|------------|
| Ты      | `maxim`   | `Kx9#mP2w` |
| Друг    | `partner` | `Vn4$jR8q` |

---

## Запуск локально (PyCharm)

1. Установи зависимости:
```
pip install -r requirements.txt
```

2. Запусти:
```
python app.py
```

3. Открой: http://localhost:8080

---

## Деплой на Railway (бесплатно, 5 минут)

1. Зарегистрируйся на https://railway.app (через GitHub)
2. Нажми **New Project → Deploy from GitHub repo**
3. Загрузи папку в GitHub (или используй Railway CLI):
   ```
   npm install -g @railway/cli
   railway login
   railway init
   railway up
   ```
4. Railway сам найдёт `Procfile` и задеплоит
5. Получишь ссылку вида `https://твой-проект.up.railway.app`

### Важно для Railway:
Добавь переменную окружения в настройках:
- `SECRET_KEY` = любая случайная строка (например `myCRM2024secretXYZ`)

---

## Деплой на Render (бесплатно)

1. Зарегистрируйся на https://render.com
2. New → Web Service → загрузи код
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn app:app`
5. Добавь env variable: `SECRET_KEY=myCRM2024secretXYZ`

---

## Структура файлов
```
crm/
├── app.py            ← Flask бэкенд + SQLite
├── requirements.txt  ← зависимости
├── Procfile          ← для Railway/Render
├── README.md
└── static/
    └── index.html    ← фронтенд
```
