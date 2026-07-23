from fpdf import FPDF
import markdown
import os

class PDF(FPDF):
    def header(self):
        self.set_font('helvetica', 'B', 15)
        self.cell(0, 10, 'Manual do Usuario - RavenStack', border=False, align='C')
        self.ln(20)
        
    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.cell(0, 10, f'Pagina {self.page_no()}', 0, 0, 'C')

def create_pdf():
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("helvetica", size=11)
    
    with open("manual.md", "r", encoding="utf-8") as f:
        md_text = f.read()

    # Convert MD to HTML
    html = markdown.markdown(md_text, extensions=['tables'])
    
    # Simple fix for h1, h2, h3 scaling in basic fpdf2 html writing if needed
    html = html.replace('<h1>', '<h1 style="font-size:24pt">')
    html = html.replace('<h2>', '<h2 style="font-size:18pt">')
    html = html.replace('<h3>', '<h3 style="font-size:14pt">')

    pdf.write_html(html)
    
    output_path = "Manual_Dashboard_RavenStack.pdf"
    pdf.output(output_path)
    print(f"PDF gerado com sucesso em: {os.path.abspath(output_path)}")

if __name__ == "__main__":
    create_pdf()
