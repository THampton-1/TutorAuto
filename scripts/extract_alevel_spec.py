"""Extract the Edexcel A Level Mathematics (9MA0) spec points into nodes.json.

One-off, run by hand (ADR-015 step 2). Unlike the GCSE spec (screenshots,
transcribed by hand), Pearson's A-Level PDF is real text, so the spec points
are read straight out of it: nothing is typed or paraphrased.

Each content page is a three-column table: Topics | Content | Guidance. Only
the Content column ("What students need to learn") becomes the node text;
Guidance is worked examples and is left out, as with GCSE. Column edges are
read from each page's own "Content" / "Guidance" headers, because Paper 3's
table sits about 10pt further right than Pure's.

Node IDs are the spec reference with a paper prefix (P = Pure, S = Statistics,
M = Mechanics), because Pure and Statistics both number from 1 (ADR-015).

The spec prints AS content in bold. Each node records how much of its text is
bold ("all", "part", "none") as `as_content`. It is stored in nodes.json only,
for later; nothing reads it yet.

Needs pdfplumber (dev-only: `pip install pdfplumber`); the nightly pipeline
does not use this script.

Usage: python scripts/extract_alevel_spec.py
"""

import json
import pathlib
import re
import sys

import pdfplumber

SPEC_DIR = pathlib.Path("specs/edexcel-alevel-maths-2017")
PDF_PATH = SPEC_DIR / "a-level-l3-mathematics-specification-issue4.pdf"
OUTPUT_PATH = SPEC_DIR / "nodes.json"

# 1-based PDF page numbers of the content tables, read off the PDF.
PURE_PAGES = range(15, 33)
PAPER3_PAGES = range(34, 43)

# Paper 3 numbers Statistics 1-5 and Mechanics 6-9 in one sequence.
LAST_STATISTICS_TOPIC = 5

POINT_ID_PATTERN = re.compile(r"^\d{1,2}\.\d{1,2}$")

SUPERSCRIPTS = {
    "0": "⁰", "1": "¹", "2": "²", "3": "³", "4": "⁴", "5": "⁵", "6": "⁶",
    "7": "⁷", "8": "⁸", "9": "⁹", "n": "ⁿ", "+": "⁺", "-": "⁻", "−": "⁻",
    "x": "ˣ", "i": "ⁱ", "k": "ᵏ",
}
SUBSCRIPTS = {
    "0": "₀", "1": "₁", "2": "₂", "3": "₃", "4": "₄", "5": "₅", "6": "₆",
    "7": "₇", "8": "₈", "9": "₉", "a": "ₐ", "r": "ᵣ", "n": "ₙ", "x": "ₓ", "i": "ᵢ",
}

# The spec point number sits in a narrow column at the left of Content; the
# point's text starts about 35pt to its right. Anything in the number column
# other than a number (e.g. "cont." under a point continued from the previous
# page) is not spec text.
NUMBER_COLUMN_WIDTH = 28


def find_column_edges(words: list[dict]) -> tuple[float, float, float] | None:
    """Return (content_left, guidance_left, table_top) for a content page."""
    content_left = None
    guidance_left = None
    table_top = None
    for word in words:
        if word["text"] == "Content" and word["x0"] > 150 and content_left is None:
            content_left = word["x0"]
            table_top = word["bottom"]
        if word["text"] == "Guidance" and word["x0"] > 300 and guidance_left is None:
            guidance_left = word["x0"]
    if content_left is None or guidance_left is None:
        return None
    return content_left, guidance_left, table_top


def find_footer_top(words: list[dict], page_height: float) -> float:
    # Every page ends with "Pearson Edexcel Level 3 Advanced GCE ..." and a
    # "Specification - Issue 4" line; the table stops above whichever is higher.
    footer_top = page_height
    for word in words:
        if word["text"] in ("Pearson", "Specification") and word["top"] > page_height * 0.8:
            if word["top"] < footer_top:
                footer_top = word["top"]
    return footer_top


def chars_to_lines(chars: list[dict]) -> list[list[dict]]:
    """Group characters into printed lines, top to bottom.

    Superscripts sit a few points above their line's baseline and are smaller,
    so lines are formed from full-size characters first and each small raised
    character is then attached to the nearest line below it.
    """
    sizes = sorted(char["size"] for char in chars)
    body_size = sizes[len(sizes) // 2]

    body_chars = []
    small_chars = []
    for char in chars:
        if char["size"] < body_size * 0.8:
            small_chars.append(char)
        else:
            body_chars.append(char)

    body_chars.sort(key=lambda char: char["bottom"])
    lines = []
    for char in body_chars:
        if len(lines) > 0 and abs(char["bottom"] - lines[-1][0]["bottom"]) < 3:
            lines[-1].append(char)
        else:
            lines.append([char])

    for char in small_chars:
        best_line = None
        best_distance = None
        for line in lines:
            distance = abs(line[0]["bottom"] - char["bottom"])
            if best_distance is None or distance < best_distance:
                best_line = line
                best_distance = distance
        if best_line is None:
            continue
        # Below the line's baseline means subscript (y₁, logₐ); above means
        # superscript (x², eᵏˣ).
        if char["bottom"] > best_line[0]["bottom"] + 0.5:
            char["script"] = "sub"
        else:
            char["script"] = "super"
        best_line.append(char)

    for line in lines:
        line.sort(key=lambda char: char["x0"])
    return lines


def line_to_text(line: list[dict]) -> str:
    text = ""
    previous = None
    for char in line:
        if previous is not None:
            gap = char["x0"] - previous["x1"]
            if gap > previous["size"] * 0.2:
                text += " "
        value = char["text"]
        if char.get("script") == "super":
            value = SUPERSCRIPTS.get(value, "^" + value)
        if char.get("script") == "sub":
            value = SUBSCRIPTS.get(value, "_" + value)
        text += value
        previous = char
    return text


def read_page_points(page) -> tuple[list[tuple[str, str, int, int]], str]:
    """Return ([(point_id or '', line_text, bold_chars, total_chars)], left_text).

    point_id is set on the line where a new spec point starts. left_text is the
    Topics column (topic number and name), used to name modules.
    """
    words = page.extract_words(extra_attrs=["fontname", "size"])
    edges = find_column_edges(words)
    if edges is None:
        return [], ""
    content_left, guidance_left, table_top = edges
    footer_top = find_footer_top(words, page.height)

    number_box = (content_left - 2, table_top + 1, content_left + NUMBER_COLUMN_WIDTH, footer_top - 1)
    point_numbers = []
    for word in page.crop(number_box).extract_words():
        if POINT_ID_PATTERN.match(word["text"]):
            point_numbers.append(word)

    text_box = (content_left + NUMBER_COLUMN_WIDTH, table_top + 1, guidance_left - 2, footer_top - 1)
    content_chars = []
    for char in page.crop(text_box).chars:
        if char["text"].strip() != "":
            content_chars.append(char)

    left_box = (0, table_top + 1, content_left - 2, footer_top - 1)
    left_words = page.crop(left_box).extract_words()
    left_text = " ".join(word["text"] for word in left_words)

    rows = []
    if len(content_chars) == 0:
        return rows, left_text
    lines = chars_to_lines(content_chars)

    # Each point number starts the line nearest to it vertically. Some
    # numbers are printed a few points lower than their first line (S4.1,
    # M7.4), so "the first line below the number" would be wrong.
    starts = {}
    for number in point_numbers:
        best_index = None
        best_distance = None
        for index, line in enumerate(lines):
            line_top = min(char["top"] for char in line)
            distance = abs(line_top - number["top"])
            if best_distance is None or distance < best_distance:
                best_index = index
                best_distance = distance
        if best_distance is not None and best_distance < 10:
            starts[best_index] = number["text"]
        else:
            raise ValueError(f"page {page.page_number}: no line next to point number {number['text']}")

    for index, line in enumerate(lines):
        point_id = starts.get(index, "")
        text = line_to_text(line)
        bold = 0
        total = 0
        for char in line:
            total += 1
            if "Bold" in char["fontname"]:
                bold += 1
        rows.append((point_id, text, bold, total))
    return rows, left_text


def module_names_from_left_column(left_texts: list[str]) -> dict[int, str]:
    """Topic number -> name, from text like '2 Algebra and functions continued'."""
    names = {}
    for left_text in left_texts:
        for match in re.finditer(r"(\d{1,2}) ([^\d]+?)(?= \d{1,2} |$)", left_text):
            number = int(match.group(1))
            name = match.group(2).replace("continued", "").strip()
            if number not in names and name:
                names[number] = name
    return names


# Points whose maths the PDF draws as layout (stacked fractions, the √ sign,
# integral signs, ⁿCᵣ) rather than as text, so the text layer comes out
# scrambled. Each replacement was typed from the rendered page (page number
# given) on 2026-10-10, keeping the spec's wording and only writing the maths
# inline (a/x, θ²/2). `starts` is the extracted text's opening words: if the
# PDF ever changes so the override would land on different text, the script
# stops rather than silently replacing it.
TEXT_OVERRIDES = {
    "P1.1": {
        "page": 15,
        "starts": "Understand and use the structure of mathematical proof",
        "text": "Understand and use the structure of mathematical proof, proceeding from given assumptions through a series of logical steps to a conclusion; use methods of proof, including: Proof by deduction; Proof by exhaustion; Disproof by counter example; Proof by contradiction (including proof of the irrationality of √2 and the infinity of primes, and application to unfamiliar proofs).",
    },
    "P2.7": {
        "page": 18,
        "starts": "Understand and use graphs of functions",
        "text": "Understand and use graphs of functions; sketch curves defined by simple equations including polynomials. The modulus of a linear function. y = a/x and y = a/x² (including their vertical and horizontal asymptotes). Interpret algebraic solution of equations graphically; use intersection points of graphs to solve equations. Understand and use proportional relationships and their graphs.",
    },
    "P4.1": {
        "page": 21,
        "starts": "Understand and use the binomial expansion",
        "text": "Understand and use the binomial expansion of (a + bx)ⁿ for positive integer n; the notations n! and ⁿCᵣ link to binomial probabilities. Extend to any rational n, including its use for approximation; be aware that the expansion is valid for |bx/a| < 1 (proof not required).",
    },
    "P4.2": {
        "page": 22,
        "starts": "Work with sequences including those given by a formula",
        "text": "Work with sequences including those given by a formula for the nth term and those generated by a simple relation of the form xₙ₊₁ = f(xₙ); increasing sequences; decreasing sequences; periodic sequences.",
    },
    "P5.1": {
        "page": 23,
        "starts": "Understand and use the definitions of sine, cosine and tangent",
        "text": "Understand and use the definitions of sine, cosine and tangent for all arguments; the sine and cosine rules; the area of a triangle in the form ½ab sin C. Work with radian measure, including use for arc length and area of sector.",
    },
    "P5.2": {
        "page": 23,
        "starts": "Understand and use the standard small angle approximations",
        "text": "Understand and use the standard small angle approximations of sine, cosine and tangent: sin θ ≈ θ, cos θ ≈ 1 − θ²/2, tan θ ≈ θ, where θ is in radians.",
    },
    "P5.3": {
        "page": 23,
        "starts": "Understand and use the sine, cosine and tangent functions",
        "text": "Understand and use the sine, cosine and tangent functions; their graphs, symmetries and periodicity. Know and use exact values of sin and cos for 0, π/6, π/4, π/3, π/2, π and multiples thereof, and exact values of tan for 0, π/6, π/4, π/3, π and multiples thereof.",
    },
    "P5.5": {
        "page": 24,
        "starts": "Understand and use sinθ",
        "text": "Understand and use tan θ = sin θ / cos θ. Understand and use sin²θ + cos²θ = 1; sec²θ = 1 + tan²θ and cosec²θ = 1 + cot²θ.",
    },
    "P6.3": {
        "page": 25,
        "starts": "Know and use the definition of loga x",
        "text": "Know and use the definition of logₐ x as the inverse of aˣ, where a is positive and x ⩾ 0. Know and use the function ln x and its graph. Know and use ln x as the inverse function of eˣ.",
    },
    "P6.4": {
        "page": 25,
        "starts": "Understand and use the laws of logarithms",
        "text": "Understand and use the laws of logarithms: logₐ x + logₐ y = logₐ (xy); logₐ x − logₐ y = logₐ (x/y); k logₐ x = logₐ xᵏ (including, for example, k = −1 and k = −½).",
    },
    "P7.2": {
        "page": 27,
        "starts": "n Differentiate x",
        "text": "Differentiate xⁿ, for rational values of n, and related constant multiples, sums and differences. Differentiate eᵏˣ and aᵏˣ, sin kx, cos kx, tan kx and related sums, differences and constant multiples. Understand and use the derivative of ln x.",
    },
    "P8.2": {
        "page": 28,
        "starts": "Integrate xⁿ (excluding n = −1)",
        "text": "Integrate xⁿ (excluding n = −1) and related sums, differences and constant multiples. Integrate eᵏˣ, 1/x, sin kx, cos kx and related sums, differences and constant multiples.",
    },
    "P9.1": {
        "page": 30,
        "starts": "Locate roots of f(x) = 0",
        "text": "Locate roots of f(x) = 0 by considering changes of sign of f(x) in an interval of x on which f(x) is sufficiently well behaved. Understand how change of sign methods can fail.",
    },
    "P9.3": {
        "page": 30,
        "starts": "Solve equations using the Newton-Raphson method",
        "text": "Solve equations using the Newton-Raphson method and other recurrence relations of the form xₙ₊₁ = g(xₙ). Understand how such methods can fail.",
    },
    "S3.2": {
        "page": 36,
        "starts": "Understand and use conditional probability",
        "text": "Understand and use conditional probability, including the use of tree diagrams, Venn diagrams, two-way tables. Understand and use the conditional probability formula P(A|B) = P(A ∩ B) / P(B).",
    },
    "M7.4": {
        "page": 40,
        "starts": "Use calculus in kinematics",
        "text": "Use calculus in kinematics for motion in a straight line: v = dr/dt, a = dv/dt = d²r/dt²; r = ∫ v dt, v = ∫ a dt. Extend to 2 dimensions using vectors.",
    },
}


def apply_text_overrides(nodes: list[dict]) -> None:
    applied = []
    for node in nodes:
        override = TEXT_OVERRIDES.get(node["node_id"])
        if override is None:
            continue
        if not node["topic"].startswith(override["starts"]):
            raise ValueError(f"{node['node_id']}: extracted text no longer starts {override['starts']!r}; check the override")
        node["topic"] = override["text"]
        node["typed_from_page_image"] = True
        applied.append(node["node_id"])
    missing = set(TEXT_OVERRIDES) - set(applied)
    if missing:
        raise ValueError(f"Overrides for unknown node(s): {sorted(missing)}")


def tidy_module_name(name: str) -> str:
    # "Coordinate geometry in the ( x , y ) plane" -> "... (x, y) plane"
    name = re.sub(r"\(\s*x\s*,\s*y\s*\)", "(x, y)", name)
    return re.sub(r"\s+", " ", name).strip()


def extract(pdf_path: pathlib.Path) -> list[dict]:
    pdf = pdfplumber.open(pdf_path)
    nodes = []
    spec_order = 0

    for paper_name, pages in (("pure", PURE_PAGES), ("paper3", PAPER3_PAGES)):
        points = {}
        point_order = []
        left_texts = []
        current_id = None
        for page_number in pages:
            rows, left_text = read_page_points(pdf.pages[page_number - 1])
            left_texts.append(left_text)
            for point_id, text, bold, total in rows:
                # A point that runs over a page break is printed again at the
                # top of the next page (e.g. 7.1, pages 26-27); that is the
                # same point continuing, so keep appending to it.
                if point_id and point_id != current_id:
                    if point_id in points:
                        raise ValueError(f"{paper_name}: point {point_id} starts twice (page {page_number})")
                    current_id = point_id
                    points[point_id] = {"lines": [], "bold": 0, "total": 0, "page": page_number}
                    point_order.append(point_id)
                if current_id is None:
                    continue
                if text:
                    points[current_id]["lines"].append(text)
                points[current_id]["bold"] += bold
                points[current_id]["total"] += total

        names = module_names_from_left_column(left_texts)
        for point_id in point_order:
            point = points[point_id]
            topic_number = int(point_id.split(".")[0])
            if paper_name == "pure":
                prefix = "P"
            elif topic_number <= LAST_STATISTICS_TOPIC:
                prefix = "S"
            else:
                prefix = "M"

            if point["bold"] == 0:
                as_content = "none"
            elif point["bold"] >= point["total"] * 0.95:
                as_content = "all"
            else:
                as_content = "part"

            spec_order += 1
            nodes.append(
                {
                    "node_id": prefix + point_id,
                    "spec_ref": point_id,
                    "module": tidy_module_name(names.get(topic_number, f"Topic {topic_number}")),
                    "topic": re.sub(r"\s+", " ", " ".join(point["lines"])).strip(),
                    "spec_order": spec_order,
                    "stretch_content": False,
                    "as_content": as_content,
                    "page": point["page"],
                }
            )
    apply_text_overrides(nodes)
    return nodes


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    nodes = extract(PDF_PATH)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(nodes, f, ensure_ascii=False, indent=2)
    print(f"Wrote {len(nodes)} nodes to {OUTPUT_PATH}")
    for node in nodes:
        print(f"{node['node_id']:<6} p{node['page']:<3} {node['as_content']:<5} {node['module'][:28]:<28} {node['topic'][:90]}")
