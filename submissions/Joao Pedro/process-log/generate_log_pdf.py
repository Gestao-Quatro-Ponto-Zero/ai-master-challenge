from fpdf import FPDF
import markdown

class PDF(FPDF):
    def header(self):
        self.set_font('helvetica', 'B', 15)
        self.cell(0, 10, 'Process Log - Case G4 Churn', border=False, align='C')
        self.ln(20)
        
    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.cell(0, 10, f'Pagina {self.page_no()}', align='C')

def create_pdf():
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("helvetica", size=11)
    
    with open("C:/Users/User/.gemini/antigravity/brain/ee100a1f-8171-4bcb-aa0e-7c0145167ef1/process_log.md", "r", encoding="utf-8") as f:
        md_text = f.read()

    # Convert MD to HTML
    html = markdown.markdown(md_text, extensions=['tables'])
    
    # Write to PDF
    pdf.write_html(html)
    
    pdf.output("C:/Users/User/.gemini/antigravity/scratch/Case-G4-Churn/Process_Log.pdf")

create_pdf()
print("Process Log PDF gerado com sucesso!")
