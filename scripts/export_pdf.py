import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from markdown_pdf import Section, MarkdownPdf

def main():
    md_file = "docs/Manual_RDL_Consolidado.md"
    pdf_file = "docs/Manual_RDL_Consolidado.pdf"
    
    with open(md_file, 'r', encoding='utf-8') as f:
        md_text = f.read()

    pdf = MarkdownPdf(toc_level=2)
    pdf.add_section(Section(md_text, toc=False))
    pdf.save(pdf_file)
    print("PDF generated successfully.")

if __name__ == "__main__":
    main()
