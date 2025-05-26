import fitz  # PyMuPDF
import json
import re
import os

class PDF_to_JSON:
    def extract_text_from_pdf(self, file_obj):
        doc = fitz.open(stream=file_obj.read(), filetype="pdf")  # read from memory
        text = ""
        for page in doc:
            page_text = page.get_text()
            page_text = page_text.encode("utf-8", errors="ignore").decode("utf-8", errors="ignore")
            text += page_text
        return text



    def extract_sections(self,text):
        sections = {}
        current_section = "General"
        buffer = []

        lines = text.splitlines()
        for line in lines:
            line = line.strip()
            line = line.encode("utf-8", errors="ignore").decode("utf-8", errors="ignore")  # clean up
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


    def normalize_sections(self, sections):
        normalized = {}

        # Handle escalation section
        if "ESCALATION" in sections:
            lines = sections["ESCALATION"].splitlines()
            esc = {}
            for line in lines:
                if ":" in line:
                    key, val = line.split(":", 1)
                    key = key.strip().lower()
                    val = val.strip()
                    if "email" in key:
                        esc["email_for_escalation"] = val
                    elif "portal" in key or "url" in key:
                        esc["support_ticket_url"] = val
                    elif "trigger" in key:
                        esc["human_contact_trigger"] = val
            normalized["escalation"] = esc

        # Include remaining sections (raw)
        for section, content in sections.items():
            if section == "ESCALATION":
                continue
            key = section.lower().replace(" ", "_")
            normalized[key] = content

        return normalized


    def convert_pdf_to_json_dynamic(self, file_obj):
        text = self.extract_text_from_pdf(file_obj)
        sections = self.extract_sections(text)
        structured_data = self.normalize_sections(sections)

        print(f"✅ Extracted JSON: {structured_data}")
        return structured_data


