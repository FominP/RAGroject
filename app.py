import streamlit as st
import os
import requests
from PyPDF2 import PdfReader
from dotenv import load_dotenv

# --- Загрузка переменных окружения ---
def clean(var: str) -> str:
    if not var:
        return ""
    var = var.strip()
    if var.startswith('"') and var.endswith('"'):
        var = var[1:-1]
    if var.startswith("'") and var.endswith("'"):
        var = var[1:-1]
    return var.strip()

try:
    API_KEY = clean(st.secrets["YANDEX_API_KEY"])
    FOLDER_ID = clean(st.secrets["YANDEX_CATALOG_ID"])
except Exception:
    load_dotenv()
    API_KEY = clean(os.getenv("YANDEX_API_KEY", ""))
    FOLDER_ID = clean(os.getenv("YANDEX_CATALOG_ID", ""))

if not API_KEY or not FOLDER_ID:
    st.error("Не найдены YANDEX_API_KEY или YANDEX_CATALOG_ID")
    st.stop()

# --- Функция вызова YandexGPT (генерация) ---
def call_yandex_gpt(prompt: str, max_tokens: int = 2000, temperature: float = 0.3, system_prompt: str = None) -> str:
    url = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
    headers = {
        "Authorization": f"Api-Key {API_KEY}",
        "Content-Type": "application/json"
    }
    messages = []
    if system_prompt:
        messages.append({"role": "system", "text": system_prompt})
    messages.append({"role": "user", "text": prompt})
    data = {
        "modelUri": f"gpt://{FOLDER_ID}/yandexgpt-lite/latest",
        "completionOptions": {
            "stream": False,
            "temperature": temperature,
            "maxTokens": max_tokens
        },
        "messages": messages
    }
    response = requests.post(url, headers=headers, json=data)
    response.raise_for_status()
    result = response.json()
    return result['result']['alternatives'][0]['message']['text']

# --- Анализ документа с синтезом итогового ответа ---
def analyze_document(text: str, analysis_type: str, user_question: str = None) -> str:
    max_chunk_size = 5000  # символов, безопасно для модели (~600-700 токенов)
    chunks = [text[i:i+max_chunk_size] for i in range(0, len(text), max_chunk_size)]
    
    # Режим "Ответ на вопрос" – используем полный текст (ограниченный до 12k символов)
    if analysis_type == "Ответ на вопрос":
        if not user_question:
            return "Не задан вопрос."
        full_text = text[:12000]  # ограничение, чтобы не превысить контекст
        prompt = f"""Ответь на вопрос, используя только содержимое документа. Если ответа нет в документе, напиши 'Не найдено'.

Документ:
{full_text}

Вопрос: {user_question}"""
        return call_yandex_gpt(prompt, max_tokens=1000, temperature=0.2)
    
    # Режимы "Основные мысли" и "Классификация утверждений"
    if analysis_type == "Основные мысли":
        chunk_prompt_template = "Выдели 3-5 основных мыслей из следующего фрагмента документа:\n\n{}"
        system_prompt = "Ты — помощник для анализа документов. Выделяй только основные идеи, без лишних деталей."
        synthesis_prompt_template = """Ниже приведены результаты анализа отдельных частей одного документа. Объедини эти результаты в единый связный ответ, выделив основные мысли всего документа целиком. Не повторяй одинаковые мысли, сгруппируй похожее. Ответ должен быть структурирован и легко читаем.

Результаты по частям:
{}

Итоговые основные мысли документа:"""
    elif analysis_type == "Классификация утверждений":
        chunk_prompt_template = "Классифицируй утверждения из следующего фрагмента документа по категориям: Факты, Мнения, Оценки, Рекомендации. Ответ дай в виде списка.\n\n{}"
        system_prompt = "Ты — классификатор текста. Относи каждое утверждение к одной из категорий."
        synthesis_prompt_template = """Ниже приведены результаты классификации отдельных частей одного документа. Объедини эти результаты в единую классификацию для всего документа. Удали дубликаты, сгруппируй похожие утверждения, представь итоговый ответ в виде списка по категориям.

Результаты по частям:
{}

Итоговая классификация для всего документа:"""
    else:
        return "Неизвестный тип анализа"

    part_results = []
    for i, chunk in enumerate(chunks, 1):
        chunk_prompt = chunk_prompt_template.format(chunk)
        part_res = call_yandex_gpt(chunk_prompt, max_tokens=1000, temperature=0.3, system_prompt=system_prompt)
        part_results.append(f"**Часть {i}:**\n{part_res}")
    
    # Если документ поместился в один чанк, возвращаем результат напрямую
    if len(chunks) == 1:
        return part_results[0]
    
    # Иначе – синтезируем итоговый ответ
    combined = "\n\n---\n\n".join(part_results)
    synthesis_prompt = synthesis_prompt_template.format(combined)
    final_answer = call_yandex_gpt(synthesis_prompt, max_tokens=1500, temperature=0.2)
    return final_answer

# --- Интерфейс Streamlit ---
st.set_page_config(page_title="Анализатор PDF", page_icon="📄", layout="wide")
st.title("📄 Анализатор PDF документов")
st.markdown("Загрузите PDF, и YandexGPT выделит основные мысли или классифицирует утверждения по всему документу.")

with st.sidebar:
    uploaded_file = st.file_uploader("Загрузите PDF", type="pdf")
    analysis_mode = st.radio(
        "Режим анализа",
        ["Основные мысли", "Классификация утверждений", "Ответ на вопрос"]
    )
    user_question = ""
    if analysis_mode == "Ответ на вопрос":
        user_question = st.text_area("Ваш вопрос по документу:", height=100)
    analyze_button = st.button("🔍 Запустить анализ", type="primary")

if analyze_button and uploaded_file:
    with st.spinner("Извлечение текста из PDF..."):
        pdf_reader = PdfReader(uploaded_file)
        full_text = "".join([page.extract_text() for page in pdf_reader.pages if page.extract_text()])
        if not full_text.strip():
            st.error("Не удалось извлечь текст из PDF. Возможно, файл отсканирован.")
            st.stop()
        st.sidebar.info(f"📄 Извлечено символов: {len(full_text)}")

    if analysis_mode == "Ответ на вопрос" and not user_question.strip():
        st.warning("Введите вопрос.")
        st.stop()

    with st.spinner("Анализ документа..."):
        if analysis_mode == "Ответ на вопрос":
            result = analyze_document(full_text, "Ответ на вопрос", user_question=user_question)
        else:
            result = analyze_document(full_text, analysis_mode)

    st.subheader("Результат анализа:")
    st.write(result)

    with st.expander("Превью извлечённого текста (первые 2000 символов)"):
        st.text(full_text[:2000] + ("..." if len(full_text) > 2000 else ""))