import argparse
import sys
import os
from typing import List
from PyPDF2 import PdfReader
from pdf2image import convert_from_path
import pytesseract
from PIL import Image

TEXT_THRESHOLD = 50  # if extracted text length < threshold, treat as empty and OCR


def extract_text_from_pdf(path: str) -> str:
    # Try to extract selectable text using PyPDF2
    reader = PdfReader(path)
    texts: List[str] = []
    for i, page in enumerate(reader.pages):
        try:
            txt = page.extract_text() or ""
        except Exception:
            txt = ""
        if txt:
            texts.append(txt)
    return "\n\n".join(texts).strip()


def ocr_pdf(path: str, dpi: int = 300, lang: str = "eng") -> str:
    # Render PDF pages to images then OCR with pytesseract
    images = convert_from_path(path, dpi=dpi)
    ocr_texts: List[str] = []
    for i, img in enumerate(images, start=1):
        if img.mode != "RGB":
            img = img.convert("RGB")
        txt = pytesseract.image_to_string(img, lang=lang)
        ocr_texts.append(f"--- PAGE {i} ---\n{txt.strip()}")
    return "\n\n".join(ocr_texts).strip()


def read_pdf(path: str, force_ocr: bool = False, ocr_lang: str = "eng") -> tuple[str, str]:
    # Returns (text, method_used)
    if not os.path.isfile(path):
        raise FileNotFoundError(f"{path} not found")

    method = "PyPDF2"

    text = ""
    if not force_ocr:
        try:
            text = extract_text_from_pdf(path)
        except Exception:
            text = ""
    if force_ocr or not text or len(text) < TEXT_THRESHOLD:
        method = "OCR"
        text = ocr_pdf(path, lang=ocr_lang)

    return text, method


def main():
    parser = argparse.ArgumentParser(description="Simple PDF reader with OCR fallback.")
    parser.add_argument("pdf", help="Path to PDF file")
    parser.add_argument("--out", "-o", help="Write extracted text to file instead of printing")
    parser.add_argument("--ocr", action="store_true", help="Force OCR (skip PyPDF2 extraction)")
    parser.add_argument("--lang", default="eng", help="Tesseract language code, default 'eng'")
    parser.add_argument("--dpi", type=int, default=300, help="DPI for rendering pages (pdf2image). Default 300")
    args = parser.parse_args()

    try:
        text, method = read_pdf(args.pdf, force_ocr=args.ocr, ocr_lang=args.lang)
    except Exception as e:
        print("Error:", e, file=sys.stderr)
        sys.exit(2)

    if not text:
        print("No text found in PDF.", file=sys.stderr)
        sys.exit(1)

    print(f"\n[INFO] PDF read method: {method}\n")

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"Saved extracted text to {args.out}")
    else:
        print(text)


if __name__ == "__main__":
    # Uncomment this if Tesseract isn’t in PATH (Windows)
    # pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    main()
