from docxtpl import DocxTemplate
import os

def test_render():
    template_path = "backend/app/services/docx/template.docx"
    output_path = "test_output.docx"
    
    doc = DocxTemplate(template_path)
    data = {
        "sender_name": "Иван Иванов",
        "sender_position": "Старший менеджер",
        "purpose": "Закупка офисной мебели",
        "items": [
            {"no": 1, "name": "Стол офисный", "quantity": 2, "price": 1500000, "total": 3000000},
            {"no": 2, "name": "Стул эргономичный", "quantity": 2, "price": 850000, "total": 1700000}
        ],
        "total_amount": 4700000.0,
        "currency": "UZS",
        "date": "28.02.2026"
    }
    doc.render(data)
    doc.save(output_path)
    print("Test document generated successfully.")

if __name__ == "__main__":
    test_render()
