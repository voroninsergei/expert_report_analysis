"""
Модуль для извлечения текста и изображений из документов PDF и DOCX.

Функции из этого модуля возвращают строку с извлечённым текстом и список
байтовых представлений изображений, найденных в документе. Изображения
впоследствии могут быть переданы на OCR для распознавания текста.
"""

from __future__ import annotations

from typing import List, Tuple
from pathlib import Path

import io

try:
    import pdfplumber  # type: ignore
except ImportError as e:  # pragma: no cover
    pdfplumber = None

try:
    from docx import Document  # type: ignore
except ImportError as e:  # pragma: no cover
    Document = None  # type: ignore


def extract_from_pdf(pdf_path: str | Path) -> Tuple[str, List[bytes]]:
    """Извлекает текст и изображения из PDF‑файла.

    :param pdf_path: путь к PDF‑файлу
    :return: кортеж (text, images), где text — конкатенация текста всех
        страниц, а images — список байтов изображений
    """
    if pdfplumber is None:  # pragma: no cover
        raise ImportError("pdfplumber не установлен. Добавьте его в зависимости.")

    path = Path(pdf_path)
    images: List[bytes] = []
    texts: List[str] = []
    # Открываем PDF и проходимся по страницам
    with pdfplumber.open(str(path)) as pdf:
        for page in pdf.pages:
            try:
                page_text = page.extract_text() or ""
                texts.append(page_text)
            except Exception:
                # Если извлечение текста с pdfplumber не удалось, продолжаем
                texts.append("")
            # Извлекаем изображения
            for img in page.images:
                try:
                    obj_id = img.get("object_id") or img.get("name")
                    if obj_id is None:
                        # Некоторые версии pdfplumber используют xref
                        obj_id = img.get("xref")
                    # extract_image возвращает словарь с ключом "image"
                    image_info = page.extract_image(obj_id)  # type: ignore
                    image_data = image_info.get("image")  # type: ignore
                    if isinstance(image_data, (bytes, bytearray)):
                        images.append(bytes(image_data))
                except Exception:
                    # пропускаем изображение, если возникла ошибка
                    continue
    full_text = "\n".join(texts)
    return full_text, images


def extract_from_docx(docx_path: str | Path) -> Tuple[str, List[bytes]]:
    """Извлекает текст и изображения из DOCX‑файла.

    :param docx_path: путь к файлу DOCX
    :return: кортеж (text, images)
    """
    if Document is None:  # pragma: no cover
        raise ImportError("python-docx не установлен. Добавьте его в зависимости.")

    path = Path(docx_path)
    doc = Document(str(path))
    texts = []
    for paragraph in doc.paragraphs:
        texts.append(paragraph.text)

    images: List[bytes] = []
    # Извлекаем бинарные данные изображений из связанных объектов
    for rel in doc.part._rels.values():  # type: ignore[attr-defined]
        try:
            if getattr(rel.target_part, "content_type", "").startswith("image"):
                # target_part.blob содержит бинарные данные изображения
                data = rel.target_part.blob  # type: ignore[attr-defined]
                images.append(data)
        except Exception:
            continue
    full_text = "\n".join(texts)
    return full_text, images