import fitz  # PyMuPDF
import json
import re
import os

def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def extract_sections(text):
    sections = {}
    current_section = "General"
    buffer = []

    lines = text.splitlines()
    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Detect section headings by uppercase or colon pattern
        if re.match(r"^[A-Z\s]{3,}$", line) or re.match(r"^[A-Za-z ]+:$", line):
            if buffer:
                sections[current_section] = "\n".join(buffer).strip()
                buffer = []
            current_section = line.strip(':').strip()
        else:
            buffer.append(line)

    if buffer:
        sections[current_section] = "\n".join(buffer).strip()

    return sections

def convert_pdf_to_json_dynamic(pdf_path, output_path):
    text = extract_text_from_pdf(pdf_path)
    sections = extract_sections(text)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(sections, f, indent=2)
    print(f"✅ Extracted JSON saved to: {output_path}")

if __name__ == "__main__":
    input_pdf = "Company_data.pdf"
    output_json = "company_data_dynamic.json"
    if os.path.exists(input_pdf):
        convert_pdf_to_json_dynamic(input_pdf, output_json)
    else:
        print(f"❌ PDF file '{input_pdf}' not found. Please place it in the same folder.")
