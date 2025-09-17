"""
Модуль для распознавания текста на изображениях с помощью pytesseract.

Функция ocr_images принимает список байтов изображений (например, извлечённых
из PDF или DOCX) и возвращает строку с объединённым распознанным текстом.
"""

from __future__ import annotations

from typing import Iterable
import io

try:
    from PIL import Image  # type: ignore
except ImportError:  # pragma: no cover
    Image = None  # type: ignore

try:
    import pytesseract  # type: ignore
except ImportError:  # pragma: no cover
    pytesseract = None  # type: ignore


def ocr_images(images: Iterable[bytes], languages: str = "rus+eng") -> str:
    """Распознаёт текст на наборе изображений.

    :param images: итерируемый объект с изображениями в виде байтов
    :param languages: строка языков для tesseract (например, "rus", "eng" или "rus+eng")
    :return: строка с объединённым распознанным текстом
    """
    if Image is None or pytesseract is None:  # pragma: no cover
        raise ImportError("Для OCR необходимы Pillow и pytesseract. Добавьте их в зависимости.")

    results = []
    for img_bytes in images:
        try:
            with Image.open(io.BytesIO(img_bytes)) as img:
                # Некоторые изображения могут быть в режиме с альфаканалом,
                # tesseract требует RGB
                if img.mode not in ("RGB", "L"):
                    img = img.convert("RGB")
                text = pytesseract.image_to_string(img, lang=languages)  # type: ignore[arg-type]
                if text:
                    results.append(text)
        except Exception:
            continue
    return "\n".join(results)