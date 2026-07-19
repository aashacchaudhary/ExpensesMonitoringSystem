import datetime
import textwrap


PAGE_WIDTH = 612
PAGE_HEIGHT = 792
MARGIN_X = 42
MARGIN_BOTTOM = 48

NAVY = (30, 42, 56)
TEAL = (22, 160, 133)
GREEN = (46, 204, 113)
CORAL = (255, 107, 107)
AMBER = (244, 183, 64)
MUTED = (107, 114, 128)
BORDER = (229, 234, 240)
SOFT_BG = (246, 248, 251)
WHITE = (255, 255, 255)


def _rgb(color):
    return " ".join(f"{component / 255:.3f}" for component in color)


def _num(value):
    return f"{value:.2f}".rstrip("0").rstrip(".")


def _escape(value):
    return str(value).replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _truncate(value, max_chars):
    text = str(value)
    if len(text) <= max_chars:
        return text
    return text[: max(0, max_chars - 1)] + "..."


class StatementPDF:
    def __init__(self):
        self.pages = []
        self.commands = []
        self.y = PAGE_HEIGHT - 46
        self.add_page()

    def add_page(self):
        self.commands = []
        self.pages.append(self.commands)
        self.y = PAGE_HEIGHT - 46
        if len(self.pages) > 1:
            self.text(MARGIN_X, PAGE_HEIGHT - 34, "Expense Monitor System", size=10, font="bold", color=NAVY)
            self.line(MARGIN_X, PAGE_HEIGHT - 48, PAGE_WIDTH - MARGIN_X, PAGE_HEIGHT - 48, color=BORDER)
            self.y = PAGE_HEIGHT - 70

    def cmd(self, value):
        self.commands.append(value)

    def text(self, x, y, value, size=10, font="regular", color=NAVY):
        font_name = "FBold" if font == "bold" else "FRegular"
        self.cmd(f"BT {_rgb(color)} rg /{font_name} {size} Tf {_num(x)} {_num(y)} Td ({_escape(value)}) Tj ET")

    def line(self, x1, y1, x2, y2, color=BORDER, width=1):
        self.cmd(f"q {_rgb(color)} RG {_num(width)} w {_num(x1)} {_num(y1)} m {_num(x2)} {_num(y2)} l S Q")

    def rect(self, x, y, width, height, fill=WHITE, stroke=BORDER, stroke_width=1):
        self.cmd(
            f"q {_rgb(fill)} rg {_rgb(stroke)} RG {_num(stroke_width)} w "
            f"{_num(x)} {_num(y)} {_num(width)} {_num(height)} re B Q"
        )

    def filled_rect(self, x, y, width, height, fill=TEAL):
        self.cmd(f"q {_rgb(fill)} rg {_num(x)} {_num(y)} {_num(width)} {_num(height)} re f Q")

    def path(self, points, color=TEAL, width=2):
        if not points:
            return
        start = points[0]
        parts = [f"{_num(start[0])} {_num(start[1])} m"]
        parts.extend(f"{_num(x)} {_num(y)} l" for x, y in points[1:])
        self.cmd(f"q {_rgb(color)} RG {_num(width)} w {' '.join(parts)} S Q")

    def ensure_space(self, needed):
        if self.y - needed < MARGIN_BOTTOM:
            self.add_page()

    def header(self, title, subtitle):
        self.filled_rect(0, PAGE_HEIGHT - 112, PAGE_WIDTH, 112, fill=NAVY)
        self.filled_rect(0, PAGE_HEIGHT - 112, 7, 112, fill=TEAL)
        self.text(MARGIN_X, PAGE_HEIGHT - 42, "Expense Monitor System", size=11, font="bold", color=(205, 250, 242))
        self.text(MARGIN_X, PAGE_HEIGHT - 72, title, size=24, font="bold", color=WHITE)
        self.text(MARGIN_X, PAGE_HEIGHT - 94, subtitle, size=10, color=(214, 224, 232))
        self.text(PAGE_WIDTH - 190, PAGE_HEIGHT - 42, "Generated", size=8, font="bold", color=(205, 250, 242))
        self.text(PAGE_WIDTH - 190, PAGE_HEIGHT - 58, datetime.date.today().strftime("%d %b %Y"), size=10, color=WHITE)
        self.y = PAGE_HEIGHT - 140

    def meta_panel(self, rows):
        self.ensure_space(92)
        x = MARGIN_X
        width = PAGE_WIDTH - (MARGIN_X * 2)
        row_count = max(1, (len(rows) + 1) // 2)
        height = 36 + (row_count * 20)
        bottom = self.y - height
        self.rect(x, bottom, width, height, fill=WHITE)
        self.text(x + 18, self.y - 20, "Statement Details", size=12, font="bold", color=NAVY)
        y = self.y - 42
        col_width = (width - 36) / 2
        for index, (label, value) in enumerate(rows):
            col = index % 2
            row = index // 2
            tx = x + 18 + (col * col_width)
            ty = y - (row * 20)
            self.text(tx, ty, label.upper(), size=7, font="bold", color=MUTED)
            self.text(tx + 92, ty, _truncate(value, 34), size=9, font="bold", color=NAVY)
        self.y = bottom - 20

    def summary_cards(self, cards):
        self.ensure_space(96)
        gap = 10
        card_width = (PAGE_WIDTH - (MARGIN_X * 2) - (gap * 3)) / 4
        card_height = 74
        y = self.y - card_height
        for index, card in enumerate(cards[:4]):
            x = MARGIN_X + (index * (card_width + gap))
            color = card.get("color", TEAL)
            self.rect(x, y, card_width, card_height, fill=WHITE, stroke=BORDER)
            self.filled_rect(x, y + card_height - 5, card_width, 5, fill=color)
            self.text(x + 12, y + 47, card["label"].upper(), size=7, font="bold", color=MUTED)
            self.text(x + 12, y + 25, card["value"], size=15, font="bold", color=color)
            if card.get("note"):
                self.text(x + 12, y + 10, _truncate(card["note"], 18), size=7, color=MUTED)
        self.y = y - 24

    def section_title(self, title):
        self.ensure_space(34)
        self.text(MARGIN_X, self.y, title, size=13, font="bold", color=NAVY)
        self.line(MARGIN_X, self.y - 8, PAGE_WIDTH - MARGIN_X, self.y - 8, color=BORDER)
        self.y -= 28

    def bar_chart(self, title, labels, values, color=TEAL):
        labels = list(labels)
        values = [float(value or 0) for value in values]
        if not labels:
            return
        rows = list(zip(labels, values))[:8]
        height = 80 + (len(rows) * 24)
        self.ensure_space(height + 20)
        x = MARGIN_X
        width = PAGE_WIDTH - (MARGIN_X * 2)
        bottom = self.y - height
        self.rect(x, bottom, width, height, fill=WHITE, stroke=BORDER)
        self.text(x + 18, self.y - 22, title, size=12, font="bold", color=NAVY)
        max_value = max(values) or 1
        label_width = 116
        chart_width = width - label_width - 92
        y = self.y - 52
        for label, value in rows:
            bar_width = chart_width * (value / max_value)
            self.text(x + 18, y + 3, _truncate(label, 17), size=8, font="bold", color=NAVY)
            self.filled_rect(x + label_width, y, chart_width, 10, fill=SOFT_BG)
            if bar_width:
                self.filled_rect(x + label_width, y, bar_width, 10, fill=color)
            self.text(x + label_width + chart_width + 14, y + 2, f"{value:.2f}", size=8, font="bold", color=MUTED)
            y -= 24
        self.y = bottom - 22

    def line_chart(self, title, labels, values, color=CORAL):
        labels = list(labels)
        values = [float(value or 0) for value in values]
        if not labels:
            return
        height = 208
        self.ensure_space(height + 20)
        x = MARGIN_X
        width = PAGE_WIDTH - (MARGIN_X * 2)
        bottom = self.y - height
        self.rect(x, bottom, width, height, fill=WHITE, stroke=BORDER)
        self.text(x + 18, self.y - 22, title, size=12, font="bold", color=NAVY)

        chart_x = x + 48
        chart_y = bottom + 48
        chart_width = width - 82
        chart_height = height - 96
        self.line(chart_x, chart_y, chart_x + chart_width, chart_y, color=BORDER)
        self.line(chart_x, chart_y, chart_x, chart_y + chart_height, color=BORDER)

        max_value = max(values) or 1
        if len(values) == 1:
            points = [(chart_x + (chart_width / 2), chart_y + (chart_height * (values[0] / max_value)))]
        else:
            points = [
                (
                    chart_x + (index * chart_width / (len(values) - 1)),
                    chart_y + (chart_height * (value / max_value)),
                )
                for index, value in enumerate(values)
            ]
        self.path(points, color=color, width=2.2)
        for point_x, point_y in points:
            self.filled_rect(point_x - 2, point_y - 2, 4, 4, fill=color)

        self.text(chart_x, bottom + 22, _truncate(labels[0], 18), size=8, color=MUTED)
        self.text(chart_x + chart_width - 60, bottom + 22, _truncate(labels[-1], 18), size=8, color=MUTED)
        self.text(chart_x + chart_width - 62, chart_y + chart_height + 8, f"Max {max_value:.2f}", size=8, color=MUTED)
        self.y = bottom - 22

    def table(self, title, headers, rows, widths):
        self.section_title(title)
        row_height = 24
        header_height = 26

        def draw_header():
            self.ensure_space(header_height + row_height)
            y = self.y - header_height
            self.filled_rect(MARGIN_X, y, sum(widths), header_height, fill=NAVY)
            x = MARGIN_X
            for header, width in zip(headers, widths):
                self.text(x + 7, y + 9, header.upper(), size=7, font="bold", color=WHITE)
                x += width
            self.y = y

        draw_header()
        for index, row in enumerate(rows):
            if self.y - row_height < MARGIN_BOTTOM:
                self.add_page()
                draw_header()
            y = self.y - row_height
            fill = WHITE if index % 2 == 0 else SOFT_BG
            self.filled_rect(MARGIN_X, y, sum(widths), row_height, fill=fill)
            x = MARGIN_X
            for value, width in zip(row, widths):
                max_chars = max(6, int(width / 5.2))
                self.text(x + 7, y + 8, _truncate(value, max_chars), size=7.5, color=NAVY)
                x += width
            self.y = y
        self.y -= 18

    def empty_state(self, text):
        self.ensure_space(46)
        self.rect(MARGIN_X, self.y - 42, PAGE_WIDTH - (MARGIN_X * 2), 42, fill=SOFT_BG, stroke=BORDER)
        self.text(MARGIN_X + 18, self.y - 26, text, size=9, color=MUTED)
        self.y -= 60

    def build(self):
        for page_number, commands in enumerate(self.pages, start=1):
            commands.append(f"BT {_rgb(MUTED)} rg /FRegular 8 Tf {MARGIN_X} 24 Td (Page {page_number}) Tj ET")
            commands.append(
                f"BT {_rgb(MUTED)} rg /FRegular 8 Tf {PAGE_WIDTH - 168} 24 Td "
                f"(Generated by Expense Monitor System) Tj ET"
            )

        page_count = len(self.pages)
        regular_font_id = 3
        bold_font_id = 4
        objects = {
            1: "<< /Type /Catalog /Pages 2 0 R >>",
            regular_font_id: "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
            bold_font_id: "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>",
        }
        page_ids = []
        next_id = 5
        for commands in self.pages:
            page_id = next_id
            content_id = next_id + 1
            next_id += 2
            page_ids.append(page_id)
            content = "\n".join(commands)
            objects[page_id] = (
                f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {PAGE_WIDTH} {PAGE_HEIGHT}] "
                f"/Resources << /Font << /FRegular {regular_font_id} 0 R /FBold {bold_font_id} 0 R >> >> "
                f"/Contents {content_id} 0 R >>"
            )
            objects[content_id] = (
                f"<< /Length {len(content.encode('latin-1', errors='replace'))} >>\n"
                f"stream\n{content}\nendstream"
            )
        objects[2] = f"<< /Type /Pages /Kids [{' '.join(f'{page_id} 0 R' for page_id in page_ids)}] /Count {page_count} >>"

        max_id = next_id - 1
        pdf = bytearray(b"%PDF-1.4\n")
        offsets = [0]
        for object_id in range(1, max_id + 1):
            offsets.append(len(pdf))
            body = objects[object_id].encode("latin-1", errors="replace")
            pdf.extend(f"{object_id} 0 obj\n".encode("latin-1"))
            pdf.extend(body)
            pdf.extend(b"\nendobj\n")

        xref_offset = len(pdf)
        pdf.extend(f"xref\n0 {max_id + 1}\n".encode("latin-1"))
        pdf.extend(b"0000000000 65535 f \n")
        for offset in offsets[1:]:
            pdf.extend(f"{offset:010d} 00000 n \n".encode("latin-1"))
        pdf.extend(
            f"trailer\n<< /Size {max_id + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode("latin-1")
        )
        return bytes(pdf)


def build_statement_pdf(title, subtitle, details, summary_cards, charts, table_title, table_headers, table_rows, table_widths):
    doc = StatementPDF()
    doc.header(title, subtitle)
    doc.meta_panel(details)
    doc.summary_cards(summary_cards)
    if charts:
        doc.section_title("Statement Charts")
        for chart in charts:
            if chart["type"] == "line":
                doc.line_chart(chart["title"], chart["labels"], chart["values"], color=chart.get("color", CORAL))
            else:
                doc.bar_chart(chart["title"], chart["labels"], chart["values"], color=chart.get("color", TEAL))
    if table_rows:
        doc.table(table_title, table_headers, table_rows, table_widths)
    else:
        doc.empty_state("No transactions found for this statement.")
    return doc.build()
