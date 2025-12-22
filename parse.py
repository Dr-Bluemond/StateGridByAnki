import re
import json


class Parser:
    """Parser 保存当前部分、当前题型和已解析的题目列表。

    字段：
    - self.current_type: 当前题型（单选题/多选题/判断题 或 None）
    - self.current_part: 当前部分（第x部分后的描述或 None）
    - self.questions: 已解析题目的列表（每项为 dict）
    """

    def __init__(self):
        self.current_type = None
        self.current_part = None
        self.questions = []

    def _preprocess_lines(self, text: str) -> list:
        lines_raw = text.splitlines()
        clean_lines = []
        # 只在整行（去首尾空白后）完全为 "- <数字> -" 时认为是页码行并跳过
        page_full_line = re.compile(r'^-\s*\d+\s*-$')
        for raw in lines_raw:
            if not raw:
                continue
            # 仅当整行匹配页码格式时跳过；否则保留原始行的全部内容（去除首尾空白）
            stripped = raw.strip()
            if page_full_line.match(stripped):
                continue
            if stripped:
                clean_lines.append(stripped)
        return clean_lines

    def _process(self, text: str):
        """逐行处理文本，识别题型、部分，并在遇到 标准答案 时完成一道题的解析并存入 self.questions。"""
        clean_lines = self._preprocess_lines(text)
        block_lines = []
        type_keywords = ['单选题', '多选题', '判断题']
        part_pattern = re.compile(r'^第(.*?)部分\s*(.*)')

        for line in clean_lines:
            # detect question type header
            matched_type = False
            for kw in type_keywords:
                if kw in line:
                    self.current_type = kw
                    print("Detected question type:", line)
                    matched_type = True
                    break
            if matched_type:
                continue

            # detect part header
            m = part_pattern.match(line)
            if m:
                trailing = m.group(2).strip()
                self.current_part = trailing if trailing else None
                print("Detected part:", line)
                continue

            # normal content
            block_lines.append(line)
            if line.startswith('答案'):
                q = self.parse_question_block(block_lines)
                self.questions.append(q)
                block_lines = []

        if block_lines:
            raise RuntimeError("存在未以『标准答案』结尾的残缺题目。")

    def parse_question_block(self, lines: list) -> dict:
        """解析一道题块，使用 self.current_type 和 self.current_part 作为元数据。"""

        qid = None
        question_lines = []
        options = {}
        current_option_key = None
        in_options = False
        correct = []

        for line in lines:

            # 提取标准答案
            if line.startswith("答案"):
                answer_match = re.search(r'答案[:：]\s*([A-D](?:、[A-D])*)', line)
                if not answer_match:
                    raise ValueError("标准答案格式错误")
                correct = answer_match.group(1).split('、')
                continue

            # 提取题号和第一行题干
            if qid is None:
                match = re.match(r'^(\d+)、\s*(.*)', line)
                if not match:
                    raise ValueError("题号或题干格式错误")
                qid = int(match.group(1))
                question_lines.append(match.group(2))
                continue

            # 提取选项
            option_match = re.match(r'^([A-D])[.．]\s*(.*)', line)
            if option_match:
                in_options = True
                current_option_key = option_match.group(1)
                options[current_option_key] = option_match.group(2)
            else:
                if in_options and current_option_key:
                    options[current_option_key] += line
                else:
                    question_lines.append(line)

        if qid is None or not options or not correct:
            raise ValueError("题目结构不完整")

        expected_keys = [chr(ord('A') + i) for i in range(len(options))]
        actual_keys = list(options.keys())
        if actual_keys != expected_keys:
            raise ValueError(f"题目 {qid} 的选项不是按 A, B, C... 顺序排列：实际为 {actual_keys}")

        for c in correct:
            if c not in options:
                raise ValueError(f"题目 {qid} 的正确答案 {c} 不在选项中")

        return {
            "id": qid,
            "question": ''.join(question_lines).strip(),
            "correct_answers": correct,
            "options": options,
            "question_type": self.current_type,
            "part": self.current_part,
        }

    def parse_questions(self, text: str) -> list:
        # reset state
        self.current_type = None
        self.current_part = None
        self.questions = []
        self._process(text)
        return self.questions

# 示例：读取并解析文件
if __name__ == "__main__":
    with open("data/questions.txt", "r", encoding="utf-8") as f:
        raw_text = f.read()

    try:
        p = Parser()
        questions = p.parse_questions(raw_text)
        print("解析题目数量：", len(questions))
        with open("data/parsed_questions.json", "w", encoding="utf-8") as f:
            json.dump(questions, f, ensure_ascii=False, indent=2)
        print("✅ 所有题目成功解析为 data/parsed_questions.json")
    except Exception as e:
        print("❌ 解析失败：", e)
