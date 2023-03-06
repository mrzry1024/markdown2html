# -*- coding: utf-8 -*-
"""
@Author  : mrzry
@File    : markdown2html.py
@Time    : 2023/03/06
@Blog    : https://www.mrzry.top/
@Desc    : markdown文档转html代码
"""

import os
import re
import sys

from pygments import highlight
from pygments.formatters.html import HtmlFormatter
from pygments.lexers import get_lexer_by_name
from pygments.lexers.special import TextLexer

help_document = r'''
命令行格式为：
python markdown2html.py markdown文档路径

示例：
python markdown2html.py README.md
python markdown2html.py "D:\projects\markdown2html\README.md"
python markdown2html.py "/root/projects/markdown2html/README.md"
'''

mycss = '''
body { font-size: 20px; } /* 字体大小 */
.highlight { background-color: rgb(248, 248, 248) !important; }  /* 代码块背景颜色 */
.linenos { background-color: rgb(230, 230, 230) !important; }  /* 行号背景颜色 */
.code { padding-left: 10px; }  /* 代码块左内边距 */
img { max-width: 100%; }  /* 图片最大宽度 */
'''


def syntax_highlight(content):
    """代码块语法高亮

    :param content: 代码块
    :return:
        - highlight_code: 高亮后的html代码
        - css: css样式
    """
    language = content[0][3:]
    code = '\n'.join(content[1:-1])

    # style: 代码风格，具体可见：https://pygments.org/demo/
    # linenos: 是否显示行号
    formatter = HtmlFormatter(style='staroffice', linenos=True)
    css = formatter.get_style_defs('.highlight')
    if language == '':
        lexer = TextLexer()
    else:
        try:
            lexer = get_lexer_by_name(language)
        except:
            lexer = TextLexer()
    highlight_code = highlight(code, lexer, formatter)
    return highlight_code, css


def markdown2html(md_content):
    """markdown转html

    处理顺序：
    1.多行，优先处理
    2.单行，但独占一行
    3.单行，需要多次匹配

    :param md_content: markdown文本
    :return:
        - html_content: html代码
        - css: css样式
    """
    md_list = md_content.split('\n')
    html_list = []

    css = ''
    count = 0
    for i in range(len(md_list)):
        if count != 0:
            count -= 1
            continue
        line = md_list[i]

        # ---------- 多行，优先处理 ----------
        # 代码块
        if re.findall(r'^```', line):
            count += 1
            for j in range(i + 1, len(md_list)):
                count += 1
                if re.findall(r'^```$', md_list[j]):
                    break
            highlight_code, _css = syntax_highlight(md_list[i:i + count])
            if css == '':
                css = f'<style>{mycss + _css}</style>'
            html_list.append(highlight_code)
            continue

        # 无序列表，目前仅支持转换后为单个li标签，相当于 单行，需要多次匹配
        if line[:2] in ['+ ', '- ', '* ']:
            line = f'''<ul><li>{line[2:]}</li></ul>'''

        # ---------- 单行，但独占一行 ----------
        # 标题，标题独占一行，匹配到则直接替换，然后跳出当前循环
        content = None
        content = re.findall(r'^#{1,6} .+', line)
        if content:
            index = content[0].index(' ')
            html_list.append(f'<h{index}>{content[0][index + 1:]}</h{index}>')
            continue

        # 水平分割线，水平分割线要求该行有且仅有-，且要大于3
        content = None
        content = re.findall(r'^-{3,}$', line)
        if content:
            html_list.append('<hr/>')
            continue

        # 图片有两种格式
        #       <img src="链接" alt="描述" style="zoom:33%;" />
        #       ![描述](链接)
        # 其中第一种已经是HTML代码了
        content = None
        content = re.findall(r'<img .+?/>', line)
        if content:
            html_list.append(line)
            continue
        content = re.findall(r'^!\[.*?\]\((.*?)\)', line)
        if content:
            alt = re.findall(r'^!\[(.*?)\]\(.*?\)', line)
            html_list.append(f'<img src="{content[0]}" alt="{alt[0]}" />')
            continue

        # ---------- 单行，需要多次匹配 ----------
        # 删除线
        contents = None
        contents = re.findall(r'~~[^~].*?~~', line)
        if contents:
            for content in contents:
                line = line.replace(content, f'<del>{content[2:-2]}</del>')

        # 加粗/强调
        contents = None
        contents = re.findall(r'\*\*[^*].*?\*\*', line)
        if contents:
            for content in contents:
                line = line.replace(content, f'<strong>{content[2:-2]}</strong>')

        # 超链接，图片格式![]()已经在前面处理过了，所以这里不用考虑[]前面的!
        contents = None
        contents = re.findall(r'\[.+?\]\(.+?\)', line)
        if contents:
            for content in contents:
                alt = re.findall(r'\[(.+?)\].', content)
                src = re.findall(r'.\((.*?)\)', content)
                line = line.replace(content, f'<a href="{src[0]}">{alt[0]}</a>')

        # 代码，代码块```代码块```已经在前面处理过了
        contents = None
        contents = re.findall(r'`.+?`', line)
        if contents:
            for content in contents:
                line = line.replace(content, f'<code>{content[1:-1]}</code>')

        # 每一行都加上p标签
        html_list.append(f'<p>{line}</p>')

    html_content = '\n'.join(html_list)
    return html_content, css


def main(argv):
    if len(sys.argv) != 2:
        print(help_document)
        sys.exit()

    path = os.path.dirname(os.path.abspath(argv[1]))  # markdown文档所在目录的绝对路径
    markdown_file = argv[1].split(os.path.sep)[-1]  # markdown文档带后缀的文件名
    if markdown_file.endswith('.md'):
        filename = markdown_file.split('.')[0]
        try:
            with open(os.path.join(path, markdown_file), 'r', encoding='utf-8') as f:
                md_content = f.read()
        except FileNotFoundError:
            print('文件路径错误')
            print(help_document)
            sys.exit()
        html_content, css = markdown2html(md_content)
        with open(f'{os.path.join(path, filename)}.html', 'w', encoding='utf-8') as f:
            f.write(f'''<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8">''' +
                    f'''<title>{filename}</title>{css}</head><body>{html_content}</body></html>''')
        print('已将markdown文档转为html代码')
    else:
        print('参数必须是markdown文档')
        print(help_document)
        sys.exit()


if __name__ == '__main__':
    main(sys.argv)
