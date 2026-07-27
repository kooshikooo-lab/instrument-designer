"""Convert RESEARCH-REPORT.md to PDF using fpdf2."""
import re
import os
import sys
from fpdf import FPDF

FONT_DIR = os.path.join(os.environ.get('WINDIR', r'C:\Windows'), 'Fonts')

class ReportPDF(FPDF):
    def __init__(self):
        super().__init__()
        self.set_auto_page_break(auto=True, margin=25)
        self.add_font('DejaVu', '', os.path.join(FONT_DIR, 'DejaVuSans.ttf'), uni=True)
        self.add_font('DejaVu', 'B', os.path.join(FONT_DIR, 'DejaVuSans-Bold.ttf'), uni=True)
        self.add_font('DejaVu', 'I', os.path.join(FONT_DIR, 'DejaVuSans-Oblique.ttf'), uni=True)
        self.add_font('DejaVu', 'BI', os.path.join(FONT_DIR, 'DejaVuSans-BoldOblique.ttf'), uni=True)
        self.add_font('DejaVuMono', '', os.path.join(FONT_DIR, 'DejaVuSansMono.ttf'), uni=True)
        
    def header(self):
        if self.page_no() > 1:
            self.set_font('DejaVu', 'I', 8)
            self.set_text_color(128, 128, 128)
            self.cell(0, 5, 'Woodwind Instrument Designer -- Research Report', align='L')
            self.cell(0, 5, f'Page {self.page_no()}', align='R', new_x="LMARGIN", new_y="NEXT")
            self.line(10, 12, 200, 12)
            self.ln(4)
    
    def footer(self):
        self.set_y(-15)
        self.set_font('DejaVu', 'I', 7)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, 'July 2026 -- Ongoing Research Document', align='C')

    def title_page(self):
        self.add_page()
        self.ln(40)
        self.set_font('DejaVu', 'B', 28)
        self.set_text_color(26, 54, 93)
        self.multi_cell(0, 12, 'Computational Design of\nWoodwind Instruments', align='C')
        self.ln(8)
        self.set_font('DejaVu', '', 14)
        self.set_text_color(42, 74, 127)
        self.multi_cell(0, 8, 'A Research Report', align='C')
        self.ln(4)
        self.set_font('DejaVu', 'I', 11)
        self.set_text_color(100, 100, 100)
        self.multi_cell(0, 7, 'Integrating Open-Source Tools for Bore Profile Optimization', align='C')
        self.ln(20)
        self.set_font('DejaVu', '', 11)
        self.set_text_color(60, 60, 60)
        self.cell(0, 7, 'Instrument Designer Project', align='C', new_x="LMARGIN", new_y="NEXT")
        self.cell(0, 7, 'Desktop & Laptop Collaborative Team', align='C', new_x="LMARGIN", new_y="NEXT")
        self.ln(4)
        self.set_font('DejaVu', 'I', 10)
        self.cell(0, 7, 'July 2026 (ongoing)', align='C', new_x="LMARGIN", new_y="NEXT")
        self.ln(20)
        self.set_draw_color(26, 54, 93)
        self.set_line_width(0.5)
        self.line(60, self.get_y(), 150, self.get_y())

    def add_heading(self, level, text):
        if level == 1:
            self.add_page()
            self.set_font('DejaVu', 'B', 18)
            self.set_text_color(26, 54, 93)
            self.ln(4)
            self.multi_cell(0, 9, text)
            self.set_draw_color(26, 54, 93)
            self.set_line_width(0.4)
            self.line(10, self.get_y()+1, 200, self.get_y()+1)
            self.ln(6)
        elif level == 2:
            self.ln(4)
            self.set_font('DejaVu', 'B', 13)
            self.set_text_color(42, 74, 127)
            self.multi_cell(0, 7, text)
            self.ln(3)
        elif level == 3:
            self.ln(2)
            self.set_font('DejaVu', 'B', 11)
            self.set_text_color(58, 90, 143)
            self.multi_cell(0, 6, text)
            self.ln(2)

    def add_text(self, text, bold=False, italic=False):
        style = ''
        if bold: style += 'B'
        if italic: style += 'I'
        self.set_font('DejaVu', style, 10)
        self.set_text_color(30, 30, 30)
        self.multi_cell(0, 5, text)
        self.ln(1)

    def add_blockquote(self, text):
        self.set_fill_color(240, 244, 248)
        self.set_font('DejaVu', 'I', 10)
        self.set_text_color(50, 50, 50)
        x = self.get_x()
        self.set_x(x + 5)
        self.multi_cell(175, 5, text, fill=True)
        self.set_x(x)
        self.ln(2)

    def add_code(self, text):
        self.set_fill_color(248, 248, 248)
        self.set_draw_color(220, 220, 220)
        self.set_font('DejaVuMono', '', 8)
        self.set_text_color(40, 40, 40)
        x = self.get_x()
        lines = text.strip().split('\n')
        h = 4.5
        box_h = len(lines) * h + 6
        self.rect(x, self.get_y(), 190, box_h, style='DF')
        self.set_x(x + 4)
        self.ln(3)
        for line in lines:
            self.set_x(x + 4)
            self.cell(0, h, line[:100], new_x="LMARGIN", new_y="NEXT")
            self.set_x(x + 4)
        self.ln(3)

    def add_table(self, headers, rows):
        self.set_font('DejaVu', 'B', 9)
        self.set_fill_color(240, 244, 248)
        self.set_draw_color(200, 200, 200)
        self.set_text_color(26, 54, 93)
        
        n_cols = len(headers)
        col_widths = [190 / n_cols] * n_cols
        
        # Adjust column widths based on content
        for i, h in enumerate(headers):
            w = self.get_string_width(h) + 8
            if w > col_widths[i]:
                col_widths[i] = min(w, 60)
        
        # Normalize
        total = sum(col_widths)
        col_widths = [w * 190 / total for w in col_widths]
        
        # Header
        for i, h in enumerate(headers):
            self.cell(col_widths[i], 6, h[:40], border=1, fill=True, align='C')
        self.ln()
        
        # Rows
        self.set_font('DejaVu', '', 8)
        self.set_text_color(30, 30, 30)
        for row_idx, row in enumerate(rows):
            fill = row_idx % 2 == 0
            if fill:
                self.set_fill_color(250, 251, 252)
            for i, cell in enumerate(row):
                self.cell(col_widths[i], 5.5, str(cell)[:50], border=1, fill=fill, align='L')
            self.ln()
        self.ln(2)

    def add_bullet_list(self, items):
        self.set_font('DejaVu', '', 10)
        self.set_text_color(30, 30, 30)
        for item in items:
            x = self.get_x()
            self.set_x(x + 5)
            self.cell(4, 5, '\u2022')
            self.multi_cell(175, 5, item)
            self.ln(0.5)
        self.ln(1)


def parse_md_table(lines):
    """Parse a markdown table into headers and rows."""
    headers = [c.strip() for c in lines[0].strip('|').split('|')]
    rows = []
    for line in lines[2:]:  # skip header and separator
        if line.strip() and '---' not in line:
            row = [c.strip() for c in line.strip('|').split('|')]
            rows.append(row)
    return headers, rows


def main():
    md_path = os.path.join(os.path.dirname(__file__), "chat-logs/RESEARCH-REPORT.md")
    pdf_path = os.path.join(os.path.dirname(__file__), "chat-logs/RESEARCH-REPORT.pdf")
    
    with open(md_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    pdf = ReportPDF()
    pdf.set_title("Computational Design of Woodwind Instruments")
    pdf.set_author("Instrument Designer Project")
    pdf.title_page()
    
    # Skip YAML front matter
    start = 0
    for i, line in enumerate(lines):
        if line.strip() == '---' and i > 0:
            start = i + 1
            break
    
    i = start
    in_code = False
    code_buf = []
    in_table = False
    table_buf = []
    
    while i < len(lines):
        line = lines[i].rstrip('\n')
        
        # Code blocks
        if line.startswith('```'):
            if in_code:
                pdf.add_code('\n'.join(code_buf))
                code_buf = []
                in_code = False
            else:
                in_code = True
            i += 1
            continue
        
        if in_code:
            code_buf.append(line)
            i += 1
            continue
        
        # Tables
        if '|' in line and line.strip().startswith('|'):
            table_buf.append(line)
            i += 1
            continue
        elif table_buf:
            headers, rows = parse_md_table(table_buf)
            if headers and rows:
                pdf.add_table(headers, rows)
            table_buf = []
        
        # Empty line
        if not line.strip():
            pdf.ln(1)
            i += 1
            continue
        
        # Headings
        if line.startswith('# ') and not line.startswith('## '):
            text = line[2:].strip()
            pdf.add_heading(1, text)
            i += 1
            continue
        if line.startswith('## '):
            text = line[3:].strip()
            pdf.add_heading(2, text)
            i += 1
            continue
        if line.startswith('### '):
            text = line[4:].strip()
            pdf.add_heading(3, text)
            i += 1
            continue
        
        # Blockquote
        if line.startswith('> '):
            text = line[2:].strip()
            pdf.add_blockquote(text)
            i += 1
            continue
        
        # Bullet list
        if line.strip().startswith('- '):
            items = []
            while i < len(lines) and lines[i].strip().startswith('- '):
                items.append(lines[i].strip()[2:])
                i += 1
            pdf.add_bullet_list(items)
            continue
        
        # Horizontal rule
        if line.strip() in ('---', '***', '___'):
            pdf.ln(3)
            i += 1
            continue
        
        # Regular text — collect multi-line paragraphs
        text_buf = []
        while i < len(lines) and lines[i].strip() and not lines[i].strip().startswith('#') and not lines[i].strip().startswith('```') and not lines[i].strip().startswith('|') and not lines[i].strip().startswith('- ') and not lines[i].strip().startswith('> '):
            text_buf.append(lines[i].strip())
            i += 1
        if text_buf:
            text = ' '.join(text_buf)
            # Handle inline formatting
            text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
            text = re.sub(r'\*(.+?)\*', r'\1', text)
            text = re.sub(r'`(.+?)`', r'\1', text)
            pdf.add_text(text)
            continue
        
        i += 1
    
    # Flush remaining table
    if table_buf:
        headers, rows = parse_md_table(table_buf)
        if headers and rows:
            pdf.add_table(headers, rows)
    
    pdf.output(pdf_path)
    print(f"PDF written to: {pdf_path}")
    print(f"Size: {os.path.getsize(pdf_path) / 1024:.1f} KB")


if __name__ == "__main__":
    main()
