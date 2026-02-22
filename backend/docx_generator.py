from docxtpl import DocxTemplate
import io
import datetime

def generate_docx(template_path, data):
    """
    data should contain:
    - sender_name: str (e.g. "Давуров Фаррух")
    - sender_position: str
    - purpose: str
    - items: list of dicts (name, quantity, amount, currency)
    - total_amount: float
    - currency: str
    - date: datetime
    """
    doc = DocxTemplate(template_path)
    
    # Format name to "Lastname I." (e.g. "Давуров Ф.")
    full_name = data.get("sender_name", "—")
    initial_name = full_name
    try:
        parts = full_name.split()
        if len(parts) >= 2:
            initial_name = f"{parts[0]} {parts[1][0]}."
        elif len(parts) == 1:
            initial_name = parts[0]
    except:
        pass

    # Helpers for template
    def format_price(value):
        try:
            return "{:,.2f}".format(float(value)).replace(",", " ")
        except:
            return value

    request_date = data.get("date")
    if isinstance(request_date, datetime.datetime):
        date_str = request_date.strftime("%d.%m.%Y")
    else:
        date_str = datetime.datetime.now().strftime("%d.%m.%Y")

    context = {
        "sender_name": full_name,
        "sender_initials": initial_name,
        "sender_position": data.get("sender_position", "—"),
        "purpose": data.get("purpose", ""),
        "items": data.get("items", []),
        "total_amount": format_price(data.get("total_amount", 0)),
        "currency": data.get("currency", "UZS"),
        "date": date_str,
    }
    
    doc.render(context)
    
    file_stream = io.BytesIO()
    doc.save(file_stream)
    file_stream.seek(0)
    return file_stream
