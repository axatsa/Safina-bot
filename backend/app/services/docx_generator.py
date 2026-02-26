from docxtpl import DocxTemplate
import io
import datetime

def generate_docx(template_path, data):
    """
    Generate a DOCX file from a template and data using docxtpl.
    Returns an io.BytesIO stream.
    """
    doc = DocxTemplate(template_path)
    
    # Ensure date is formatted if it's a datetime object
    if isinstance(data.get("date"), (datetime.date, datetime.datetime)):
        data["date"] = data["date"].strftime("%d.%m.%Y")
    
    # The template expects specific variables:
    # {{ sender_name }}, {{ sender_position }}, {{ purpose }}, {{ request_id }}, {{ date }}
    # {{ total_amount }}, {{ currency }}
    # And a loop for items: {% for item in items %} ... {{ item.name }}, {{ item.quantity }}, {{ item.amount }} ... {% endfor %}
    
    doc.render(data)
    
    file_stream = io.BytesIO()
    doc.save(file_stream)
    file_stream.seek(0)
    return file_stream
