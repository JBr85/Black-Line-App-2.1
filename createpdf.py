from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def generate_pdf(data):
    pdf_file = "output_1.pdf"
    c = canvas.Canvas(pdf_file, pagesize=letter)
    
    # Add content to the PDF
    c.drawString(100, 750, "Generated PDF Content")
    c.drawString(100, 730, f"Data: {data}")
    
    c.save()
    
    return pdf_file
