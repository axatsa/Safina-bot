from docxtpl import DocxTemplate
import io
import datetime

def generate_docx(template_path, data):
    """
    data should contain:
    - sender_name: str
    - sender_position: str
    - purpose: str
    - items: list of dicts (name, quantity, amount, currency)
    - total_amount: float
    - currency: str
    - date: str (formatted)
    """
    doc = DocxTemplate(template_path)
    
    # Enrich data for template
    # We can add more helpers here if needed
    context = {
        **data,
        "current_year": datetime.datetime.now().year,
        "current_date": datetime.datetime.now().strftime("%d.%m.%Y")
    }
    
    doc.render(context)
    
    file_stream = io.BytesIO()
    doc.save(file_stream)
    file_stream.seek(0)
    return file_stream
