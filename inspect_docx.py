from docxtpl import DocxTemplate
import os

template_path = os.path.join(os.path.dirname(__file__), "backend/app/services/docx/template.docx")
if os.path.exists(template_path):
    doc = DocxTemplate(template_path)
    # docxtpl doesn't have a simple "list all placeholders" but we can try to find them in the xml
    # or just try to render with a specific marker to see what remains.
    # Alternatively, we can inspect the undeclared_template_variables
    import re
    xml = doc.get_docx().element.xml
    placeholders = re.findall(r'\{\{\s*(.*?)\s*\}\}', xml)
    print("Found placeholders in XML:", set(placeholders))
else:
    print("Template not found at", template_path)
