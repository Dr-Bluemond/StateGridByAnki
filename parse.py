"""从官方题库 PDF（或提取后的文本）解析题目，默认使用 2027 版。"""
import argparse
from collections import Counter
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parent
DEFAULT_PDF = ROOT / 'data/9.国家电网有限公司高校毕业生招聘考试公共与行业知识题库（2027版）.pdf'


class Parser:
    TYPE = re.compile(r'^(?:[一二三四五六七八九十]+、\s*)?(单选题|多选题|判断题)$')
    PART = re.compile(r'^第[一二三四五六七八九十\d]+部分\s*(.*)$')
    QUESTION = re.compile(r'^(\d+)、\s*(.*)$')
    ANSWER = re.compile(r'^(?:标准)?答案\s*[:：]\s*([A-D](?:\s*、\s*[A-D])*)$')
    OPTION = re.compile(r'^([A-D])[.．]\s*(.*)$')

    def __init__(self):
        self.current_type = None
        self.current_part = None
        self.questions = []

    def _preprocess_lines(self, text: str) -> list:
        lines = []
        for raw in text.splitlines():
            line = re.sub(r'[ \t\u3000]+', ' ', raw).strip()
            if not line or re.fullmatch(r'-\s*\d+\s*-|第\s*\d+\s*页\s*共\s*\d+\s*页', line):
                continue
            if line in {'国家电网有限公司高校毕业生招聘考试', '公共与行业知识题库'}:
                continue
            lines.append(line)
        return lines

    def parse_questions(self, text: str) -> list:
        self.__init__()
        block = []
        pending_part = False
        for line in self._preprocess_lines(text):
            type_match = self.TYPE.fullmatch(line)
            part_match = self.PART.fullmatch(line)
            if type_match or part_match:
                if block or pending_part:
                    raise ValueError(f'题目或分部标题未完成就遇到标题：{line}')
                if type_match:
                    self.current_type = type_match[1]
                    self.current_part = None
                else:
                    self.current_part = part_match[1] or None
                    pending_part = self.current_part is None
                continue
            if pending_part:
                if self.QUESTION.match(line):
                    raise ValueError('分部标题缺少名称')
                self.current_part = line
                pending_part = False
                continue
            if self.QUESTION.match(line) and block:
                raise ValueError(f'上一题缺少答案：{block[0]}')
            block.append(line)
            if re.match(r'^(?:标准)?答案\s*[:：]', line):
                question = self.parse_question_block(block)
                expected_id = len(self.questions) + 1
                if question['id'] != expected_id:
                    raise ValueError(f'题号应为 {expected_id}，实际为 {question["id"]}')
                self.questions.append(question)
                block = []
        if block or pending_part:
            raise ValueError(f'存在残缺题目或标题：{block[:1]}')
        if not self.questions:
            raise ValueError('没有解析到题目')
        return self.questions

    def parse_question_block(self, lines: list) -> dict:
        first = self.QUESTION.fullmatch(lines[0])
        answer = self.ANSWER.fullmatch(lines[-1])
        if not first or not answer:
            raise ValueError(f'题号或答案格式错误：{lines[0]} / {lines[-1]}')
        qid = int(first[1])
        if not self.current_type or not self.current_part:
            raise ValueError(f'题目 {qid} 缺少题型或分部')
        question_lines = [first[2]]
        options = {}
        current_key = None
        for line in lines[1:-1]:
            option = self.OPTION.fullmatch(line)
            if option:
                current_key = option[1]
                if current_key in options:
                    raise ValueError(f'题目 {qid} 选项重复：{current_key}')
                options[current_key] = option[2]
            elif current_key:
                options[current_key] += line
            else:
                question_lines.append(line)
        question = ''.join(question_lines).strip()
        correct = re.split(r'\s*、\s*', answer[1])
        expected_keys = list('AB' if self.current_type == '判断题' else 'ABCD')
        if not question or list(options) != expected_keys or not all(options.values()):
            raise ValueError(f'题目 {qid} 题干或选项不完整：{list(options)}')
        if len(set(correct)) != len(correct) or not set(correct) <= options.keys():
            raise ValueError(f'题目 {qid} 答案重复或超出选项：{correct}')
        if self.current_type != '多选题' and len(correct) != 1:
            raise ValueError(f'题目 {qid} 应只有一个正确答案')
        if self.current_type == '多选题' and len(correct) < 2:
            raise ValueError(f'题目 {qid} 多选题应有至少两个正确答案')
        return {
            'id': qid,
            'question': question,
            'correct_answers': correct,
            'options': options,
            'question_type': self.current_type,
            'part': self.current_part,
        }


def extract_pdf(path: Path) -> str:
    # layout 保持括号及同一行文本的顺序，避免页脚插入跨页题干。
    try:
        return subprocess.run(
            ['pdftotext', '-layout', '-enc', 'UTF-8', str(path), '-'],
            check=True, capture_output=True, encoding='utf-8',
        ).stdout
    except FileNotFoundError as exc:
        raise RuntimeError('请先安装 Poppler（macOS：brew install poppler）') from exc


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('input', nargs='?', type=Path, default=DEFAULT_PDF, help='PDF 或 UTF-8 文本')
    cli.add_argument('--output', type=Path, default=ROOT / 'data/parsed_questions.json')
    cli.add_argument('--text-output', type=Path, default=ROOT / 'data/questions.txt')
    args = cli.parse_args()
    text = extract_pdf(args.input) if args.input.suffix.lower() == '.pdf' else args.input.read_text(encoding='utf-8')
    questions = Parser().parse_questions(text)
    # 通过全部校验后才覆盖生成文件。
    args.text_output.write_text(text, encoding='utf-8')
    args.output.write_text(json.dumps(questions, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'解析 {len(questions)} 题：{dict(Counter(q["question_type"] for q in questions))}')
    print(f'已写入 {args.output}')


if __name__ == '__main__':
    main()
