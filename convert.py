import json
import csv
import argparse
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def format_choices(options, correct_answers, highlight=False):
    lines = []
    for key in sorted(options.keys()):
        text = escape(f"{key}. {options[key]}")
        if highlight:
            if key in correct_answers:
                text = f'<span style="color:green;">{text}</span>'
            else:
                text = f'<span style="color:#808080;">{text}</span>'
        lines.append(text)
    return "<br>".join(lines)


def json_to_anki_tsv(json_list, output_file, year="2027"):
    with open(output_file, "w", encoding="utf-8", newline='') as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")
        # 写入数据
        for item in json_list:
            number = item["id"]
            question = escape(item["question"])
            options = item["options"]
            correct = item["correct_answers"]
            question_type = item["question_type"]
            part = item["part"]
            is_multiple = "1" if question_type == "多选题" else ""

            choices = format_choices(options, correct, highlight=False)
            highlighted = format_choices(options, correct, highlight=True)
            correct_answer = ", ".join(correct)  # 如果是多选题，也可以显示多个

            tags = f"电网::{year} 电网::{question_type} 电网::{part}"

            writer.writerow([
                number, question, choices, highlighted, correct_answer,
                question_type, part, is_multiple, tags
            ])


if __name__ == "__main__":
    cli = argparse.ArgumentParser(description="将解析后的题库转换为九列 Anki TSV")
    cli.add_argument("input", nargs="?", type=Path, default=ROOT / "data/parsed_questions.json")
    cli.add_argument("--output", type=Path, default=ROOT / "data/anki_cards.tsv")
    cli.add_argument("--year", default="2027", help="题库年份标签，默认 2027")
    args = cli.parse_args()
    with args.input.open("r", encoding="utf-8") as f:
        data = json.load(f)

    json_to_anki_tsv(data, args.output, year=args.year)
    print(f"已导出 {len(data)} 张卡片到 {args.output}")
