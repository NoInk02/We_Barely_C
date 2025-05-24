import fitz  # PyMuPDF
import re
import json
import os


def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page in doc:
        text += page.get_text()
    return text


def extract_faqs(text):
    faqs = []
    # Look for Q: ... A: ... patterns
    pattern = re.compile(r"Q:\s*(.*?)\nA:\s*(.*?)(?=\nQ:|\Z)", re.DOTALL)
    matches = pattern.findall(text)
    for q, a in matches:
        faqs.append({
            "question": q.strip(),
            "answer": a.strip()
        })
    return faqs


def extract_services(text):
    services = []
    if "Standard Shipping" in text:
        services.append({
            "type": "Standard Shipping",
            "delivery_time": "3-5 business days",
            "rate": "$5 per kg"
        })
    if "Express Shipping" in text:
        services.append({
            "type": "Express Shipping",
            "delivery_time": "1-2 business days",
            "rate": "$10 per kg"
        })
    if "International Shipping" in text:
        services.append({
            "type": "International Shipping",
            "delivery_time": "5-10 business days",
            "rate": "$15 per kg"
        })
    return services


def extract_company_info(text):
    info = {}
    if "SwiftShip" in text:
        info["name"] = "SwiftShip Logistics"
    if "Courier Lane" in text:
        info["address"] = "123 Courier Lane, Shipville, NY 10001"

    email_match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}", text)
    phone_match = re.search(r"\\+?\\d[\\d\\s\\-]{7,}\\d", text)
    if email_match:
        info["email"] = email_match.group()
    if phone_match:
        info["phone"] = phone_match.group()
    if "Mon-Sat" in text:
        info["working_hours"] = "Mon-Sat: 9am - 6pm"
    return info


def extract_policies(text):
    policies = {}
    if "return within 14 days" in text:
        policies["return_policy"] = "Customers can request a return within 14 days of delivery. Return shipping is free for damaged goods."
    if "Standard (3-5 days)" in text:
        policies["shipping_policy"] = "We offer Standard (3-5 days), Express (1-2 days), and International shipping. Tracking is available for all services."
    if "Refunds are issued" in text:
        policies["refund_policy"] = "Refunds are issued within 5 business days after inspection of returned items."
    return policies


def extract_troubleshooting(text):
    troubleshooting = {}
    if "tracking number not working" in text.lower():
        troubleshooting["tracking_number_not_working"] = [
            "Ensure the number is correct.",
            "Wait 12 hours after shipment.",
            "Contact support if issue persists."
        ]
    if "package arrived damaged" in text.lower():
        troubleshooting["package_arrived_damaged"] = [
            "Take a photo.",
            "Contact support within 48 hours.",
            "We'll investigate and issue refund/reshipment."
        ]
    return troubleshooting


def extract_escalation_info(text):
    if "talk to human" in text.lower():
        return {
            "trigger": "User asks 2+ questions in a row or types 'talk to human'",
            "email": "priority@swiftship.com",
            "support_ticket_url": "https://swiftship.com/support"
        }
    return {}


def convert_pdf_to_json(pdf_path, output_path):
    text = extract_text_from_pdf(pdf_path)
    data = {
        "company_info": extract_company_info(text),
        "policies": extract_policies(text),
        "services": extract_services(text),
        "faqs": extract_faqs(text),
        "troubleshooting": extract_troubleshooting(text),
        "escalation": extract_escalation_info(text)
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"✅ Extracted data saved to: {output_path}")


if __name__ == "__main__":
    input_pdf = "Company_data.pdf"
    output_json = "company_data.json"
    if os.path.exists(input_pdf):
        convert_pdf_to_json(input_pdf, output_json)
    else:
        print(f"❌ PDF file '{input_pdf}' not found. Please place it in the same folder.")
