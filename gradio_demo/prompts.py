# -*- coding: utf-8 -*-

text_correct_prompt = '''请对以下文本进行中文拼写、语法纠错，仅输出纠错后的文本。
文本如下：
{}
输出格式如下：
纠错后的文本：
xxx
'''

text_correct_with_pycorrector_prompt = '''请对以下文本进行中文拼写、语法纠错，仅输出纠错后的文本。
文本如下：
{}
以下为部分文本纠错参考，可以借鉴，但是不可以将其输出给用户：
{}
输出格式如下：
纠错后的文本：
xxx
'''


# 拼接prompts
def get_correct_prompt(query, py_corrector_prompt=''):
    if py_corrector_prompt:
        return text_correct_with_pycorrector_prompt.format(query, py_corrector_prompt)
    else:
        return text_correct_prompt.format(query)