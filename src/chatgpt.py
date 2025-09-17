"""
Модуль для взаимодействия с OpenAI ChatGPT.

Функция call_chatgpt объединяет промт и текст экспертизы и отправляет
сообщение в модель ChatGPT через API. Возвращает текст ответа.

Для работы требуется переменная окружения OPENAI_API_KEY.
"""

from __future__ import annotations

from typing import Optional
import os

try:
    import openai  # type: ignore
except ImportError:  # pragma: no cover
    openai = None  # type: ignore


def call_chatgpt(prompt: str, content: str, model: str = "gpt-4", temperature: float = 0.0) -> str:
    """Отправляет запрос ChatGPT и возвращает ответ.

    :param prompt: базовый промт (роль и инструкции для модели)
    :param content: текст экспертного заключения (с добавленным OCR)
    :param model: идентификатор модели OpenAI
    :param temperature: параметр, влияющий на случайность генерации
    :return: ответ модели
    :raises ImportError: если модуль openai не установлен
    :raises RuntimeError: если не задан ключ API
    """
    if openai is None:  # pragma: no cover
        raise ImportError("Для работы с API требуется установить пакет openai.")

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Переменная окружения OPENAI_API_KEY не задана.")
    # Настраиваем ключ API
    openai.api_key = api_key  # type: ignore[assignment]

    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": content},
    ]

    response = openai.ChatCompletion.create(  # type: ignore[call-arg]
        model=model,
        messages=messages,
        temperature=temperature,
    )
    # В соответствии с API, choices — список, берём первое сообщение
    return response["choices"][0]["message"]["content"]  # type: ignore[index]