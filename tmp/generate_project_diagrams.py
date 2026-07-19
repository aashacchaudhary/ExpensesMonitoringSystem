from pathlib import Path
from PIL import Image, ImageDraw, ImageFont


OUT_DIR = Path(__file__).resolve().parent / "diagrams"
OUT_DIR.mkdir(parents=True, exist_ok=True)

BG = "#F6F8FB"
CARD = "#FFFFFF"
NAVY = "#1E2A38"
TEAL = "#16A085"
TEAL_SOFT = "#DDF7F1"
CORAL = "#FF6B6B"
CORAL_SOFT = "#FFE8E8"
AMBER = "#F4B740"
AMBER_SOFT = "#FFF3D7"
GREEN = "#2ECC71"
GREEN_SOFT = "#E8F8EF"
MUTED = "#6B7280"
BORDER = "#DDE6EF"


def font(size, bold=False):
    candidates = [
        r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\segoeuib.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    return ImageFont.load_default()


F_TITLE = font(42, True)
F_SUBTITLE = font(22)
F_HEADER = font(24, True)
F_BODY = font(18)
F_SMALL = font(15)
F_TINY = font(13)


def canvas(width=1600, height=1000, title="", subtitle=""):
    image = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((36, 32, width - 36, 132), radius=26, fill=NAVY)
    draw.rounded_rectangle((36, 32, 52, 132), radius=8, fill=TEAL)
    draw.text((78, 54), title, font=F_TITLE, fill="white")
    draw.text((78, 103), subtitle, font=F_SMALL, fill="#CFE8E3")
    return image, draw


def text_center(draw, box, text, fnt=F_BODY, fill=NAVY, line_gap=6):
    x1, y1, x2, y2 = box
    lines = []
    for raw_line in str(text).split("\n"):
        words = raw_line.split()
        current = ""
        for word in words:
            proposed = f"{current} {word}".strip()
            if draw.textbbox((0, 0), proposed, font=fnt)[2] <= (x2 - x1 - 28):
                current = proposed
            else:
                if current:
                    lines.append(current)
                current = word
        lines.append(current)
    total_height = sum(draw.textbbox((0, 0), line, font=fnt)[3] for line in lines) + (len(lines) - 1) * line_gap
    y = y1 + ((y2 - y1 - total_height) / 2)
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=fnt)
        x = x1 + ((x2 - x1 - (bbox[2] - bbox[0])) / 2)
        draw.text((x, y), line, font=fnt, fill=fill)
        y += (bbox[3] - bbox[1]) + line_gap


def card(draw, box, text, fill=CARD, outline=BORDER, text_fill=NAVY, fnt=F_BODY):
    draw.rounded_rectangle(box, radius=22, fill=fill, outline=outline, width=2)
    text_center(draw, box, text, fnt=fnt, fill=text_fill)


def arrow(draw, start, end, color=TEAL, width=4, label=None, label_offset=(0, -28)):
    draw.line((start, end), fill=color, width=width)
    sx, sy = start
    ex, ey = end
    dx, dy = ex - sx, ey - sy
    length = max((dx * dx + dy * dy) ** 0.5, 1)
    ux, uy = dx / length, dy / length
    px, py = -uy, ux
    size = 14
    points = [
        (ex, ey),
        (ex - ux * size + px * size * 0.55, ey - uy * size + py * size * 0.55),
        (ex - ux * size - px * size * 0.55, ey - uy * size - py * size * 0.55),
    ]
    draw.polygon(points, fill=color)
    if label:
        mid = ((sx + ex) / 2 + label_offset[0], (sy + ey) / 2 + label_offset[1])
        bbox = draw.textbbox((0, 0), label, font=F_TINY)
        pad = 8
        draw.rounded_rectangle(
            (mid[0] - pad, mid[1] - pad, mid[0] + bbox[2] + pad, mid[1] + bbox[3] + pad),
            radius=10,
            fill=BG,
            outline=BORDER,
        )
        draw.text(mid, label, font=F_TINY, fill=NAVY)


def title_note(draw, xy, title, note):
    x, y = xy
    draw.text((x, y), title, font=F_HEADER, fill=NAVY)
    draw.text((x, y + 34), note, font=F_SMALL, fill=MUTED)


def save(image, name):
    path = OUT_DIR / name
    image.save(path, "PNG")
    return path


def sequence_diagram():
    image, draw = canvas(
        title="Sequence Diagram",
        subtitle="Expense Monitoring System: authentication, expense entry, reporting, family budget",
    )
    actors = [
        ("User", 125),
        ("Django Views", 420),
        ("Forms & Auth", 710),
        ("Models", 1000),
        ("SQLite / PDF", 1295),
    ]
    top, bottom = 180, 910
    for actor, x in actors:
        card(draw, (x - 105, top, x + 105, top + 62), actor, fill=TEAL_SOFT, outline="#BDECE3", fnt=F_SMALL)
        draw.line((x, top + 70, x, bottom), fill="#B9C7D4", width=2)
        for yy in range(top + 90, bottom, 26):
            draw.line((x, yy, x, yy + 10), fill=BG, width=3)

    messages = [
        (125, 420, 285, "register / login"),
        (420, 710, 345, "validate forms"),
        (710, 1000, 405, "create user/session"),
        (125, 420, 480, "add expense"),
        (420, 1000, 540, "save Expense"),
        (1000, 1295, 600, "write SQLite row"),
        (125, 420, 665, "open reports"),
        (420, 1000, 725, "query expenses + budgets"),
        (1000, 1295, 785, "aggregate + generate PDF/CSV"),
        (420, 125, 850, "render dashboard/report"),
    ]
    for x1, x2, y, label in messages:
        arrow(draw, (x1 + (28 if x2 > x1 else -28), y), (x2 - (28 if x2 > x1 else -28), y), label=label)

    save(image, "sequence_diagram.png")


def flowchart():
    image, draw = canvas(
        title="Flowchart",
        subtitle="Main user journey across dashboard, personal reports, budget, and family features",
    )
    nodes = {
        "Home": (120, 205, 360, 285),
        "Authenticated?": (500, 190, 760, 300),
        "Register / Login": (900, 205, 1180, 285),
        "Dashboard": (500, 380, 760, 470),
        "Add Expense": (120, 575, 360, 665),
        "Transactions": (445, 575, 705, 665),
        "My Reports": (770, 575, 1030, 665),
        "Budget Setup": (1095, 575, 1360, 665),
        "Family": (445, 780, 705, 870),
        "Family Budget": (770, 780, 1030, 870),
        "PDF / CSV": (1095, 780, 1360, 870),
    }
    for name, box in nodes.items():
        fill = TEAL_SOFT if name in {"Home", "Dashboard", "Family"} else CARD
        if name == "Authenticated?":
            draw.polygon(
                [
                    ((box[0] + box[2]) / 2, box[1]),
                    (box[2], (box[1] + box[3]) / 2),
                    ((box[0] + box[2]) / 2, box[3]),
                    (box[0], (box[1] + box[3]) / 2),
                ],
                fill=AMBER_SOFT,
                outline=AMBER,
            )
            text_center(draw, box, name, fnt=F_BODY)
        else:
            card(draw, box, name, fill=fill, fnt=F_BODY)

    def right_mid(box):
        return box[2], (box[1] + box[3]) / 2

    def left_mid(box):
        return box[0], (box[1] + box[3]) / 2

    def bottom_mid(box):
        return (box[0] + box[2]) / 2, box[3]

    def top_mid(box):
        return (box[0] + box[2]) / 2, box[1]

    arrow(draw, right_mid(nodes["Home"]), left_mid(nodes["Authenticated?"]), label="visit site")
    arrow(draw, right_mid(nodes["Authenticated?"]), left_mid(nodes["Register / Login"]), label="no")
    arrow(draw, bottom_mid(nodes["Authenticated?"]), top_mid(nodes["Dashboard"]), label="yes")
    arrow(draw, (1040, 285), (700, 380), label="success")
    arrow(draw, (500, 470), (240, 575), label="create")
    arrow(draw, bottom_mid(nodes["Dashboard"]), top_mid(nodes["Transactions"]), label="manage")
    arrow(draw, (760, 470), (900, 575), label="analyze")
    arrow(draw, (760, 425), (1220, 575), label="set budget")
    arrow(draw, bottom_mid(nodes["Transactions"]), top_mid(nodes["Family"]), label="family")
    arrow(draw, right_mid(nodes["Family"]), left_mid(nodes["Family Budget"]), label="creator sets")
    arrow(draw, right_mid(nodes["Family Budget"]), left_mid(nodes["PDF / CSV"]), label="download")
    arrow(draw, right_mid(nodes["My Reports"]), left_mid(nodes["PDF / CSV"]), label="statements")
    save(image, "flowchart.png")


def er_diagram():
    image, draw = canvas(
        title="ER Diagram",
        subtitle="Database structure for users, expenses, budgets, family groups, and memberships",
    )

    tables = {
        "User": (80, 210, 360, 430, ["id PK", "username", "email", "password"]),
        "Expense": (470, 180, 790, 465, ["id PK", "user_id FK", "title", "amount", "category", "date", "payment_method", "description"]),
        "Budget": (910, 180, 1230, 430, ["id PK", "user_id FK", "month", "year", "amount", "created_at", "updated_at"]),
        "FamilyGroup": (80, 585, 400, 815, ["id PK", "name", "code", "created_by_id FK", "created_at"]),
        "FamilyMembership": (520, 585, 860, 845, ["id PK", "user_id FK", "family_group_id FK", "joined_at", "UNIQUE(user, group)"]),
        "FamilyBudget": (980, 585, 1300, 845, ["id PK", "family_group_id FK", "month", "year", "amount", "UNIQUE(group, month, year)"]),
    }

    def table_box(name, box, fields):
        x1, y1, x2, y2 = box
        draw.rounded_rectangle(box, radius=18, fill=CARD, outline=BORDER, width=2)
        draw.rounded_rectangle((x1, y1, x2, y1 + 52), radius=18, fill=NAVY)
        draw.rectangle((x1, y1 + 28, x2, y1 + 52), fill=NAVY)
        text_center(draw, (x1, y1, x2, y1 + 52), name, fnt=F_BODY, fill="white")
        y = y1 + 68
        for field in fields:
            draw.text((x1 + 18, y), field, font=F_SMALL, fill=NAVY if "PK" in field or "FK" in field else MUTED)
            y += 24

    for name, (x1, y1, x2, y2, fields) in tables.items():
        table_box(name, (x1, y1, x2, y2), fields)

    def mid_right(name):
        x1, y1, x2, y2, _ = tables[name]
        return x2, (y1 + y2) / 2

    def mid_left(name):
        x1, y1, x2, y2, _ = tables[name]
        return x1, (y1 + y2) / 2

    def mid_bottom(name):
        x1, y1, x2, y2, _ = tables[name]
        return (x1 + x2) / 2, y2

    def mid_top(name):
        x1, y1, x2, y2, _ = tables[name]
        return (x1 + x2) / 2, y1

    arrow(draw, mid_right("User"), mid_left("Expense"), label="1:N expenses")
    arrow(draw, (360, 305), (910, 305), label="1:N budgets")
    arrow(draw, mid_bottom("User"), mid_top("FamilyGroup"), label="creates")
    arrow(draw, (360, 380), (520, 650), label="1:N memberships")
    arrow(draw, mid_right("FamilyGroup"), mid_left("FamilyMembership"), label="1:N members")
    arrow(draw, mid_right("FamilyMembership"), mid_left("FamilyBudget"), color=AMBER, label="group budget")
    arrow(draw, (400, 700), (980, 700), color=TEAL, label="1:N budgets")
    save(image, "er_diagram.png")


def gantt_chart():
    image, draw = canvas(
        title="Gantt Chart",
        subtitle="Suggested project implementation schedule for documentation",
    )
    x0, y0 = 290, 230
    chart_w, row_h = 1120, 58
    week_w = chart_w / 8
    tasks = [
        ("Requirements & planning", 1, 1.2, TEAL),
        ("Django project setup", 1.4, 1.6, NAVY),
        ("Authentication", 2.2, 1.4, GREEN),
        ("Expense CRUD + filters", 3.0, 2.0, TEAL),
        ("Budgets + alerts", 4.2, 1.5, AMBER),
        ("Reports + charts", 5.0, 1.7, CORAL),
        ("Family groups + family budget", 6.0, 1.6, TEAL),
        ("PDF/CSV statements", 6.8, 1.2, NAVY),
        ("Responsive UI polish", 7.0, 1.4, GREEN),
        ("Testing + documentation", 7.5, 1.2, AMBER),
    ]

    draw.rounded_rectangle((80, 195, 1488, 900), radius=28, fill=CARD, outline=BORDER, width=2)
    draw.text((110, 225), "Tasks", font=F_HEADER, fill=NAVY)
    for week in range(1, 9):
        x = x0 + ((week - 1) * week_w)
        draw.text((x + 26, 225), f"W{week}", font=F_SMALL, fill=NAVY)
        draw.line((x, 265, x, 875), fill=BORDER, width=1)
    draw.line((x0 + chart_w, 265, x0 + chart_w, 875), fill=BORDER, width=1)

    for index, (task, start, duration, color) in enumerate(tasks):
        y = y0 + 65 + (index * row_h)
        draw.text((110, y + 10), task, font=F_SMALL, fill=NAVY)
        bar_x = x0 + ((start - 1) * week_w)
        bar_w = duration * week_w
        draw.rounded_rectangle((bar_x, y, bar_x + bar_w, y + 30), radius=15, fill=color)
        draw.text((bar_x + 12, y + 7), f"{duration:.1f}w", font=F_TINY, fill="white")
        draw.line((100, y + row_h - 13, 1458, y + row_h - 13), fill="#EEF2F7", width=1)

    draw.text((110, 880), "Milestones: MVP by Week 5, family reporting by Week 7, final documentation by Week 8", font=F_SMALL, fill=MUTED)
    save(image, "gantt_chart.png")


def class_diagram():
    image, draw = canvas(
        width=1800,
        height=1120,
        title="Class Diagram",
        subtitle="Core Django model classes and relationships used by the Expense Monitoring System",
    )

    classes = {
        "User": (
            80,
            205,
            390,
            455,
            ["+ id: BigAutoField", "+ username: CharField", "+ email: EmailField", "+ password: CharField"],
            ["+ authenticate()", "+ get_username()"],
            "#243447",
        ),
        "Expense": (
            535,
            185,
            890,
            535,
            [
                "+ user: ForeignKey<User>",
                "+ title: CharField",
                "+ amount: DecimalField",
                "+ category: ChoiceField",
                "+ date: DateField",
                "+ payment_method: ChoiceField",
                "+ description: TextField",
            ],
            ["+ __str__()"],
            TEAL,
        ),
        "Budget": (
            1035,
            205,
            1365,
            485,
            ["+ user: ForeignKey<User>", "+ month: PositiveSmallInteger", "+ year: PositiveInteger", "+ amount: DecimalField"],
            ["+ __str__()", "+ unique(user, month, year)"],
            AMBER,
        ),
        "FamilyGroup": (
            80,
            675,
            440,
            1000,
            ["+ name: CharField", "+ code: CharField", "+ created_by: ForeignKey<User>", "+ created_at: DateTimeField"],
            ["+ save()", "+ generate_unique_code()", "+ __str__()"],
            NAVY,
        ),
        "FamilyMembership": (
            590,
            690,
            950,
            1010,
            ["+ user: ForeignKey<User>", "+ family_group: ForeignKey<FamilyGroup>", "+ joined_at: DateTimeField"],
            ["+ __str__()", "+ unique(user, family_group)"],
            TEAL,
        ),
        "FamilyBudget": (
            1110,
            680,
            1480,
            1010,
            ["+ family_group: ForeignKey<FamilyGroup>", "+ month: PositiveSmallInteger", "+ year: PositiveInteger", "+ amount: DecimalField"],
            ["+ __str__()", "+ unique(group, month, year)"],
            AMBER,
        ),
    }

    def uml_box(name, box, attrs, methods, header_color):
        x1, y1, x2, y2 = box
        draw.rounded_rectangle(box, radius=20, fill=CARD, outline=BORDER, width=2)
        draw.rounded_rectangle((x1, y1, x2, y1 + 58), radius=20, fill=header_color)
        draw.rectangle((x1, y1 + 34, x2, y1 + 58), fill=header_color)
        text_center(draw, (x1, y1, x2, y1 + 58), name, fnt=F_BODY, fill="white")
        sep1 = y1 + 58
        sep2 = y1 + 74 + (len(attrs) * 24)
        draw.line((x1, sep1, x2, sep1), fill=BORDER, width=2)
        draw.line((x1, sep2, x2, sep2), fill=BORDER, width=2)
        y = y1 + 76
        for attr in attrs:
            draw.text((x1 + 18, y), attr, font=F_SMALL, fill=NAVY)
            y += 24
        y = sep2 + 14
        for method in methods:
            draw.text((x1 + 18, y), method, font=F_SMALL, fill=MUTED)
            y += 24

    for name, (x1, y1, x2, y2, attrs, methods, color) in classes.items():
        uml_box(name, (x1, y1, x2, y2), attrs, methods, color)

    def mid_right(name):
        x1, y1, x2, y2, *_ = classes[name]
        return x2, (y1 + y2) / 2

    def mid_left(name):
        x1, y1, x2, y2, *_ = classes[name]
        return x1, (y1 + y2) / 2

    def mid_bottom(name):
        x1, y1, x2, y2, *_ = classes[name]
        return (x1 + x2) / 2, y2

    def mid_top(name):
        x1, y1, x2, y2, *_ = classes[name]
        return (x1 + x2) / 2, y1

    arrow(draw, mid_right("User"), mid_left("Expense"), label="1 user owns many expenses")
    arrow(draw, (390, 320), (1035, 320), label="1 user owns many budgets")
    arrow(draw, mid_bottom("User"), mid_top("FamilyGroup"), label="creates")
    arrow(draw, (390, 430), (590, 765), label="joins groups")
    arrow(draw, mid_right("FamilyGroup"), mid_left("FamilyMembership"), label="has members")
    arrow(draw, (440, 840), (1110, 840), color=AMBER, label="has family budgets")

    draw.rounded_rectangle((1450, 205, 1720, 455), radius=22, fill=TEAL_SOFT, outline="#BDECE3", width=2)
    title_note(draw, (1474, 232), "Django Forms", "ModelForms validate input")
    form_lines = ["RegisterForm", "StyledAuthenticationForm", "ExpenseForm", "BudgetForm", "FamilyBudgetForm"]
    y = 315
    for item in form_lines:
        draw.text((1474, y), item, font=F_SMALL, fill=NAVY)
        y += 27

    draw.rounded_rectangle((1450, 530, 1720, 760), radius=22, fill=AMBER_SOFT, outline="#F5D78A", width=2)
    title_note(draw, (1474, 558), "Django Views", "Controller functions")
    view_lines = ["dashboard()", "expense_list()", "monthly_report()", "family_report()"]
    y = 642
    for item in view_lines:
        draw.text((1474, y), item, font=F_SMALL, fill=NAVY)
        y += 27

    save(image, "class_diagram.png")


def usecase_diagram():
    image, draw = canvas(
        width=1800,
        height=1120,
        title="Use Case Diagram",
        subtitle="Actors and major actions supported by the Expense Monitoring System",
    )

    boundary = (360, 185, 1455, 1030)
    draw.rounded_rectangle(boundary, radius=34, fill=CARD, outline=BORDER, width=3)
    draw.text((395, 215), "Expense Monitoring System", font=F_HEADER, fill=NAVY)

    def actor(x, y, name):
        draw.ellipse((x - 20, y, x + 20, y + 40), outline=NAVY, width=4)
        draw.line((x, y + 40, x, y + 110), fill=NAVY, width=4)
        draw.line((x - 45, y + 66, x + 45, y + 66), fill=NAVY, width=4)
        draw.line((x, y + 110, x - 42, y + 165), fill=NAVY, width=4)
        draw.line((x, y + 110, x + 42, y + 165), fill=NAVY, width=4)
        bbox = draw.textbbox((0, 0), name, font=F_BODY)
        draw.text((x - ((bbox[2] - bbox[0]) / 2), y + 178), name, font=F_BODY, fill=NAVY)
        return x, y + 82

    actors = {
        "Visitor": actor(145, 250, "Visitor"),
        "User": actor(145, 610, "Registered User"),
        "Creator": actor(1620, 390, "Family Creator"),
        "Admin": actor(1620, 755, "Admin"),
    }

    usecases = {
        "Register Account": (520, 295),
        "Login by User ID\nor Username": (795, 295),
        "View Dashboard": (1070, 295),
        "Add Expense": (540, 455),
        "Search Transactions": (820, 455),
        "Delete Expense": (1100, 455),
        "Set Personal Budget": (545, 615),
        "View My Reports": (830, 615),
        "Download PDF/CSV": (1110, 615),
        "Create / Join Family": (560, 785),
        "Set Family Budget": (850, 785),
        "View Family Statement": (1140, 785),
        "Manage Admin Data": (1120, 930),
    }

    def oval(center, label, fill=TEAL_SOFT):
        x, y = center
        w, h = 230, 72
        draw.ellipse((x - w / 2, y - h / 2, x + w / 2, y + h / 2), fill=fill, outline=BORDER, width=2)
        text_center(draw, (x - w / 2, y - h / 2, x + w / 2, y + h / 2), label, fnt=F_SMALL)
        return (x, y)

    centers = {}
    for label, center in usecases.items():
        fill = AMBER_SOFT if "Budget" in label else TEAL_SOFT if "Family" in label else CARD
        centers[label] = oval(center, label, fill=fill)

    def assoc(actor_name, usecase_label, color=TEAL):
        ax, ay = actors[actor_name]
        ux, uy = centers[usecase_label]
        draw.line((ax, ay, ux, uy), fill=color, width=3)

    assoc("Visitor", "Register Account")
    assoc("Visitor", "Login by User ID\nor Username")
    assoc("User", "Login by User ID\nor Username")
    for case in [
        "View Dashboard",
        "Add Expense",
        "Search Transactions",
        "Delete Expense",
        "Set Personal Budget",
        "View My Reports",
        "Download PDF/CSV",
        "Create / Join Family",
        "View Family Statement",
    ]:
        assoc("User", case)
    assoc("Creator", "Set Family Budget", color=AMBER)
    assoc("Creator", "View Family Statement", color=AMBER)
    assoc("Admin", "Manage Admin Data", color=CORAL)

    arrow(draw, (935, 615), (1015, 615), color=MUTED, width=2, label="includes")
    arrow(draw, (1240, 785), (1185, 655), color=MUTED, width=2, label="exports")

    save(image, "usecase_diagram.png")


def main():
    sequence_diagram()
    flowchart()
    er_diagram()
    gantt_chart()
    class_diagram()
    usecase_diagram()
    print(f"Generated diagrams in {OUT_DIR}")


if __name__ == "__main__":
    main()
