import json
import csv


def format_choices(options, correct_answers, highlight=False):
    lines = []
    for key in sorted(options.keys()):
        text = f"{key}. {options[key]}"
        if highlight:
            if key in correct_answers:
                text = f'<span style="color:green;">{text}</span>'
            else:
                text = f'<span style="color:#808080;">{text}</span>'
        lines.append(text)
    return "<br>".join(lines)


def json_to_anki_tsv(json_list, output_file):
    with open(output_file, "w", encoding="utf-8", newline='') as f:
        writer = csv.writer(f, delimiter="\t")
        # 写入数据
        for item in json_list:
            number = item["id"]
            question = item["question"]
            options = item["options"]
            correct = item["correct_answers"]
            question_type = item["question_type"]
            part = item["part"]
            is_multiple = "1" if question_type == "多选题" else ""

            choices = format_choices(options, correct, highlight=False)
            highlighted = format_choices(options, correct, highlight=True)
            correct_answer = ", ".join(correct)  # 如果是多选题，也可以显示多个

            tags = "电网::" + question_type + " " + "电网::" + part

            writer.writerow([
                number, question, choices, highlighted, correct_answer,
                question_type, part, is_multiple, tags
            ])


# 示例使用
if __name__ == "__main__":
    with open("data/parsed_questions.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    json_to_anki_tsv(data, "data/anki_cards.tsv")