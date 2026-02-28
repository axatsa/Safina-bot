from docxtpl import DocxTemplate
import os
import datetime

# I'm using the writing-plans skill to implement this diagnostic task.
# This script renders the template with static data matching backend/app/api/expenses.py:271

def test_render():
    # Paths relative to project root
    template_path = "backend/app/services/docx/template.docx"
    output_path = "test_output.docx"
    
    if not os.path.exists(template_path):
        # Try finding it relative to script location if root fails
        template_path = os.path.join(os.path.dirname(__file__), template_path)
        
    print(f"Loading template from: {template_path}")
    
    try:
        doc = DocxTemplate(template_path)
        
        # Mock data matching the schema used in the API
        data = {
            "sender_name": "Иван Иванов",
            "sender_position": "Старший менеджер",
            "purpose": "Закупка офисной мебели для нового отдела",
            "items": [
                {
                    "no": 1, 
                    "name": "Стол офисный", 
                    "quantity": 2, 
                    "price": 1500000, 
                    "total": 3000000
                },
                {
                    "no": 2, 
                    "name": "Стул эргономичный", 
                    "quantity": 2, 
                    "price": 850000, 
                    "total": 1700000
                },
                {
                    "no": 3, 
                    "name": "Тумба подкатная", 
                    "quantity": 1, 
                    "price": 600000, 
                    "total": 600000
                }
            ],
            "total_amount": 5300000.0,
            "currency": "UZS",
            "request_id": "TEST-2026-001",
            "date": datetime.datetime.now().strftime("%d.%m.%Y")
        }
        
        print("Rendering with data...")
        doc.render(data)
        
        doc.save(output_path)
        print(f"Success! Output saved to: {os.path.abspath(output_path)}")
        
    except Exception as e:
        print(f"Error during rendering: {e}")

if __name__ == "__main__":
    test_render()
