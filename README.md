# 国家电网入职考试公共知识题库Anki牌组

当前分支使用 `data/9.国家电网有限公司高校毕业生招聘考试公共与行业知识题库（2027版）.pdf`，共 **832 题**：单选 352 题、多选 253 题、判断 227 题，覆盖形势政策、企业文化、公司战略、新型电力系统、品牌建设五部分。题干、选项和答案均按 PDF 原文提取，不对题库答案作知识性修订。

2027 版的代码适配、题库解析、Anki 卡片生成与校验由 **GPT-6.1 Sol 独立完成**。

## 重新生成

需要 Python 3.9+ 和 Poppler 的 `pdftotext`（macOS 可用 `brew install poppler`），无需第三方 Python 包。在项目目录运行：

```bash
python3 parse.py
python3 convert.py
python3 -m unittest discover -s tests -v
```

默认从 2027 版 PDF 提取文本到 `data/questions.txt`，校验后生成 `data/parsed_questions.json`，再导出 `data/anki_cards.tsv`。解析失败会以非零状态退出，并保留已有生成文件。使用 `-layout` 提取以保持同一行括号、文字和跨页选项的顺序；解析时过滤标题和页码，并检查题号连续、题型、分部、选项和答案。

也可以指定输入及输出位置（路径相对于当前工作目录）：

```bash
python3 parse.py /path/to/questions.pdf --text-output /tmp/questions.txt --output /tmp/questions.json
python3 convert.py /tmp/questions.json --output /tmp/cards.tsv --year 2027
```

`parse.py` 也支持 UTF-8 `.txt` 输入。默认输入、输出位置始终相对于脚本所在目录。

## 导入 Anki

`data/anki_cards.tsv` 使用 UTF-8、制表符分隔、无表头，保持原有九列顺序：

| 列 | Anki 字段 | 内容 |
| --- | --- | --- |
| 1 | Number | PDF 题号 |
| 2 | Question | 题干 |
| 3 | Choices | 选项，以 HTML 换行 |
| 4 | HighlightedChoices | 正确项绿色，其余灰色 |
| 5 | CorrectAnswer | 正确答案字母 |
| 6 | QuestionType | 单选题、多选题或判断题 |
| 7 | Part | 所属部分 |
| 8 | isMultiple | 多选题为 `1`，其他留空 |
| 9 | 标签 | 年份、题型、分部标签 |

创建含前八个字段的笔记类型，正面、背面和样式分别使用 `src/front.html`、`src/back.html`、`src/style.css`。导入时允许字段使用 HTML，并将第九列映射到 Anki 的“标签”。支持 `电网::2027`、`电网::多选题`、`电网::新型电力系统` 等筛选。

若同时保留 2026 和 2027 牌组，请为 2027 版复制一个独立笔记类型，再导入到新牌组。两版第一字段均为题号，只换牌组或增加年份标签仍可能将旧笔记识别为重复项并更新。

## 卡片预览

### 单选题

#### 正面

![单选题正面](imgs/单选正面.png)

#### 背面

![单选题背面](imgs/单选背面.png)

### 多选题

#### 正面

![多选题正面](imgs/多选正面.png)

#### 背面

![多选题背面](imgs/多选背面.png)
