"""
Точка входа для утилиты анализа судебных экспертиз.

Этот модуль обеспечивает командный интерфейс, позволяя пользователю
указать входной файл (PDF или DOCX) с экспертным заключением, путь к
выходному файлу с отчётом, а также дополнительные параметры: путь к
собственному промту, язык OCR, модель OpenAI и значение temperature.

Пример запуска:

```
python -m src.main --input data/экспертиза.pdf --output results/отчёт.docx
```
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from .extract import extract_from_pdf, extract_from_docx
from .ocr import ocr_images
from .chatgpt import call_chatgpt
from .report import create_report


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Извлечение текста из экспертного заключения и его анализ с помощью ChatGPT",
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Путь к входному файлу (PDF или DOCX)",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Путь к выходному DOCX‑файлу с отчётом",
    )
    parser.add_argument(
        "--prompt",
        default=None,
        help="Путь к собственному текстовому файлу с промтом (опционально)",
    )
    parser.add_argument(
        "--model",
        default="gpt-4",
        help="Идентификатор модели OpenAI (по умолчанию gpt-4)",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.0,
        help="Параметр temperature для генерации ответов (по умолчанию 0.0)",
    )
    parser.add_argument(
        "--ocr-lang",
        default="rus+eng",
        help="Код языка для Tesseract, например 'rus', 'eng' или 'rus+eng'",
    )
    return parser.parse_args(argv)


def load_prompt(prompt_path: Path | None) -> str:
    """Загружает текст промта из указанного файла.

    Если путь не задан, пытается прочитать файл prompt.txt в корне
    проекта. Если файл не найден, возвращает пустую строку.
    """
    if prompt_path is not None:
        return prompt_path.read_text(encoding="utf-8")
    # По умолчанию читаем prompt.txt из корня репозитория
    default_path = Path(__file__).resolve().parent.parent / "prompt.txt"
    try:
        return default_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv or sys.argv[1:])
    input_path = Path(args.input)
    output_path = Path(args.output)
    prompt_path = Path(args.prompt) if args.prompt else None

    # Загружаем базовый промт
    prompt_text = load_prompt(prompt_path)

    # Извлекаем текст и изображения из файла
    suffix = input_path.suffix.lower()
    if suffix == ".pdf":
        text, images = extract_from_pdf(str(input_path))
    elif suffix == ".docx":
        text, images = extract_from_docx(str(input_path))
    else:
        raise SystemExit(f"Неподдерживаемый формат входного файла: {suffix}")

    # Распознаём текст с изображений
    ocr_text = ocr_images(images, languages=args.ocr_lang)
    # Объединяем текст: сначала основной текст, затем результат OCR
    combined_text = text
    if ocr_text.strip():
        combined_text = combined_text + "\n" + ocr_text

    # Обращаемся к ChatGPT
    response_text = call_chatgpt(prompt_text, combined_text, model=args.model, temperature=args.temperature)

    # Создаём отчёт
    create_report(response_text, output_path)


if __name__ == "__main__":  # pragma: no cover
    main()