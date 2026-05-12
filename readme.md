# PDF Анализатор с YandexGPT

Приложение на Streamlit для анализа PDF-документов с использованием нейросети YandexGPT (без эмбеддингов, но с разбиением на части). Поддерживает три режима:

- **Основные мысли** – выделение 3-5 ключевых идей документа.
- **Классификация утверждений** – разделение утверждений на категории: Факты, Мнения, Оценки, Рекомендации.
- **Ответ на вопрос** – генерация ответа на пользовательский вопрос по содержанию документа.

## 🚀 Быстрый старт

### 1. Получение API-ключей Yandex Cloud

1. Зарегистрируйтесь в [Yandex Cloud](https://cloud.yandex.ru/).
2. Создайте платёжный аккаунт (первые 10 млн токенов в месяц бесплатно).
3. В сервисе **YandexGPT** активируйте доступ к API.
4. Создайте **сервисный аккаунт** и назначьте ему роль `ai.languageModels.user`.
5. Создайте **API-ключ** для этого аккаунта.
6. Скопируйте **идентификатор каталога** (Folder ID) и API-ключ.

> Подробнее: [Инструкция Yandex Cloud](https://cloud.yandex.ru/docs/iam/operations/api-key/create)

### 2. Локальный запуск (без Docker)

```bash
# Клонируйте репозиторий
git clone https://github.com/ваш-username/rag-project.git
cd rag-project

# Создайте виртуальное окружение
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate     # Windows

# Установите зависимости
pip install -r requirements.txt

# Создайте файл .env с вашими ключами (см. пример ниже)
# Запустите приложение
streamlit run app.py
```

### 3.Запуск в Docker
```bash
# Соберите образ
docker build -t pdf-analyzer .

# Запустите контейнер, передав переменные окружения
docker run -p 8501:8501 \
  -e YANDEX_API_KEY="ваш_api_ключ" \
  -e YANDEX_CATALOG_ID="ваш_folder_id" \
  pdf-analyzer
```
После запуска откройте браузер по адресу http://localhost:8501.

## 🔧 Файл окружения (.env)
Создайте файл .env в корне проекта (не добавляйте его в Git):

```dotenv
YANDEX_API_KEY=ваш_ключ
YANDEX_CATALOG_ID=ваш_folder_id
```

## 📦 Зависимости
- Python 3.12+
- streamlit
- PyPDF2
- requests
- python-dotenv

## 📁 Структура проекта
```text
.
├── app.py                  # Основное приложение Streamlit
├── requirements.txt        # Зависимости Python
├── Dockerfile              # Инструкция для сборки Docker-образа
├── .dockerignore           # Исключения для Docker
├── .gitignore              # Исключения для Git
└── README.md               # Этот файл
```

## 🐳 Dockerfile (пример)
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8501
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

## 💡 Примечания
При очень длинных документах (>6000 символов) текст разбивается на части, каждая анализируется отдельно, после чего результаты объединяются.

Бесплатный тариф Yandex Cloud позволяет до 10 млн токенов в месяц, что достаточно для тестирования.

## 📄 Лицензия
MIT