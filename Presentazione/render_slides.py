import os
import subprocess
from pypdf import PdfReader, PdfWriter

def compile_and_render(tex_name='presentazione.tex'):
    # Compila con pdflatex
    res = subprocess.run(['pdflatex', '-interaction=nonstopmode', tex_name], capture_output=True, text=True)
    print("PDFLaTeX returncode:", res.returncode)
    
    pdf_name = tex_name.replace('.tex', '.pdf')
    if not os.path.exists(pdf_name):
        print("Errore: PDF non generato!")
        print(res.stdout[-1000:])
        return
    
    # Estrai e renderizza ogni pagina
    reader = PdfReader(pdf_name)
    print(f"Pagine totali: {len(reader.pages)}")
    for i, page in enumerate(reader.pages):
        writer = PdfWriter()
        writer.add_page(page)
        page_pdf = f"page_{i+1}.pdf"
        with open(page_pdf, "wb") as f:
            writer.write(f)
        slide_png = f"slide_{i+1}.png"
        subprocess.run(['sips', '-s', 'format', 'png', page_pdf, '--out', slide_png], capture_output=True)
        print(f"Generata: {slide_png}")

if __name__ == '__main__':
    compile_and_render()
