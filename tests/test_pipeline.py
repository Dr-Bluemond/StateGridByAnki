import csv
from collections import Counter
import json
from pathlib import Path
import tempfile
import unittest

from convert import json_to_anki_tsv
from parse import Parser, ROOT, extract_pdf


class ParserTests(unittest.TestCase):
    def sample(self):
        return '''国家电网有限公司高校毕业生招聘考试
公共与行业知识题库
一、单选题
第一部分
形势政策
1、跨页题干（ ）
第 1 页 共 159 页
\f继续题干
A. 选项一
- 2 -
的续行
B. 选项二
C. 选项三
D. 选项四
答案：B
'''

    def test_page_breaks_and_split_heading(self):
        question = Parser().parse_questions(self.sample())[0]
        self.assertEqual(question['question'], '跨页题干（ ）继续题干')
        self.assertEqual(question['options']['A'], '选项一的续行')
        self.assertEqual(question['part'], '形势政策')
        self.assertEqual(question['correct_answers'], ['B'])

    def test_incomplete_and_invalid_questions_fail(self):
        for text in [
            self.sample().replace('答案：B', ''),
            self.sample().replace('1、', '2、'),
            self.sample().replace('B. 选项二', 'A. 选项二'),
            self.sample().replace('D. 选项四\n', ''),
            self.sample().replace('答案：B', '答案：B、C'),
            self.sample().replace('答案：B', '答案：B错误'),
            self.sample().replace('形势政策\n', ''),
        ]:
            with self.subTest(text=text), self.assertRaises(ValueError):
                Parser().parse_questions(text)

    def test_multiple_and_judgment(self):
        multiple = self.sample().replace('单选题', '多选题').replace('答案：B', '答案：A、C')
        self.assertEqual(Parser().parse_questions(multiple)[0]['correct_answers'], ['A', 'C'])
        judgment = self.sample().replace('单选题', '判断题').replace('C. 选项三\nD. 选项四\n', '')
        self.assertEqual(len(Parser().parse_questions(judgment)[0]['options']), 2)

    def test_2026_pdf_compatibility(self):
        old_text = extract_pdf(ROOT / 'data/9.国家电网有限公司高校毕业生招聘考试公共与行业知识题库（2026版）.pdf')
        actual = Parser().parse_questions(old_text)
        self.assertEqual(len(actual), 790)
        self.assertEqual(Counter(q['question_type'] for q in actual),
                         {'单选题': 335, '多选题': 249, '判断题': 206})

    def test_export_escapes_html_and_preserves_fields(self):
        question = Parser().parse_questions(self.sample())[0]
        question['question'] = '1 < 2 & 3 > 2'
        question['options']['B'] = '<正确> & "答案"'
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'cards.tsv'
            json_to_anki_tsv([question], output)
            with output.open(encoding='utf-8', newline='') as stream:
                rows = list(csv.reader(stream, delimiter='\t'))
        self.assertEqual(len(rows), 1)
        self.assertEqual(len(rows[0]), 9)
        self.assertEqual(rows[0][1], '1 &lt; 2 &amp; 3 &gt; 2')
        self.assertIn('&lt;正确&gt;', rows[0][2])
        self.assertIn('color:green;', rows[0][3])
        self.assertEqual(rows[0][4:8], ['B', '单选题', '形势政策', ''])
        self.assertIn('电网::2027', rows[0][8])

    def test_generated_2027_files(self):
        questions = Parser().parse_questions((ROOT / 'data/questions.txt').read_text(encoding='utf-8'))
        self.assertEqual(questions, json.loads((ROOT / 'data/parsed_questions.json').read_text(encoding='utf-8')))
        self.assertEqual([q['id'] for q in questions], list(range(1, 833)))
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'cards.tsv'
            json_to_anki_tsv(questions, output)
            self.assertEqual(output.read_bytes(), (ROOT / 'data/anki_cards.tsv').read_bytes())


if __name__ == '__main__':
    unittest.main()
