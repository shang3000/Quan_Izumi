import sys
sys.stdout.reconfigure(encoding='utf-8')

with open('习思想期末复习/刷题题库.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 检查JavaScript语法错误
import re

# 检查括号匹配
bracket_count = 0
for i, char in enumerate(content):
    if char == '{':
        bracket_count += 1
    elif char == '}':
        bracket_count -= 1
    if bracket_count < 0:
        line_num = content[:i].count('\n') + 1
        print(f'括号不匹配，第{line_num}行有多余的}}')
        break

if bracket_count > 0:
    print(f'括号不匹配，缺少{bracket_count}个}}')
elif bracket_count == 0:
    print('括号匹配正确')

# 检查方括号
bracket_count = 0
for i, char in enumerate(content):
    if char == '[':
        bracket_count += 1
    elif char == ']':
        bracket_count -= 1
    if bracket_count < 0:
        line_num = content[:i].count('\n') + 1
        print(f'方括号不匹配，第{line_num}行有多余的]')
        break

if bracket_count > 0:
    print(f'方括号不匹配，缺少{bracket_count}个]')
elif bracket_count == 0:
    print('方括号匹配正确')

# 检查题目数据
lines = content.split('\n')
in_questions = False
question_start = 0
for i, line in enumerate(lines):
    if 'const questions' in line:
        in_questions = True
        question_start = i
    if in_questions and '];' in line:
        print(f'题目数据在第{question_start+1}行到第{i+1}行')
        break

# 统计题目数量
question_count = content.count("type: 'single'") + content.count("type: 'multiple'") + content.count("type: 'fill'")
print(f'统计到{question_count}道题目')
