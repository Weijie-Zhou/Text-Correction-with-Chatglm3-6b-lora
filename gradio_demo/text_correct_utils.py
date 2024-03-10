import difflib
import json
import math
import re

import requests
import sentencepiece as spm


class TokenizerLengthCheck:
    '''token长度检查及截断'''
    def __init__(self):
        self.sp = spm.SentencePieceProcessor()
        self.sp.Load("/root/autodl-tmp/ZhipuAI/chatglm3-6b-lora/tokenizer.model")

    def input_length_check(self, text, len_req=8096):
        # 判断prompt+文本后长度是否超过要求长度
        text_tokens = self.sp.EncodeAsIds(text)
        if len(text_tokens) < len_req:
            return True
        else:
            return False
    
    def input_trunc(self, prompt, text, len_req=8096):
        # 输入文本截断
        prompt_tokens = self.sp.EncodeAsIds(prompt)
        text_tokens = self.sp.EncodeAsIds(text)
        total_len = len(prompt_tokens) + len(text_tokens)
        if total_len < len_req:
            return text
        else:
            res_len = len_req - len(prompt_tokens)
            half_res_len = int((len(text_tokens)-res_len) / 2)
            text_tokens = text_tokens[half_res_len: -half_res_len]
            return self.sp.Decode(text_tokens)
        
        
def b2q(uchar):
    '''半角转全角'''
    inside_code = ord(uchar)
    if inside_code < 0x0020 or inside_code > 0x7e:
        # 不是半角字符就返回原来的字符
        return uchar
    if inside_code == 0x0020:
        # 除了空格，其他的全角半角的公式为：全角 = 半角 + 0xfee0
        inside_code = 0x3000
    else:
        inside_code += 0xfee0
    return chr(inside_code)


def q2b(uchar):
    '''全角转半角'''
    inside_code = ord(uchar)
    if inside_code == 0x3000:
        # 全角空格
        inside_code = 0x0020
    else:
        # 半角 = 全角 - 0xfee0
        inside_code -= 0xfee0
    if inside_code < 0x0020 or inside_code > 0x7e:
        # 转完之后不是半角字符则返回原来的字符
        return uchar
    return chr(inside_code)


def string_q2b(ustring):
    '''将字符串全角转半角'''
    return ''.join([q2b(uchar) for uchar in ustring])


def string_b2q(ustring):
    '''将字符串半角转全角'''
    return ''.join([b2q(uchar) for uchar in ustring])


def punctuation_transform(document):
    '''英文标点转中文标点'''
    punctuations = {',': '，', '?': '？', '!': '！', ';': '；', ':': '：', '(': '（', ')': '）', "'": '‘',   '"': '“'}
    for punctuation in punctuations.keys():
        document = document.replace(punctuation, punctuations[punctuation])
    return document


def high_light(origin_document, correct_document):
    '''纠错文本前后高亮对比markdown'''
    # correct_document = correct_document.replace('纠错后的文本：', '').replace('文本到此结束。', '').replace('文本到此结束', '').replace('【', '').replace('】', '')
    origin_document = origin_document.replace('\n\n', '\n')
    diff = difflib.Differ().compare(origin_document, correct_document)
    high_light_markdown = ''
    for i in diff:
        if i[0] == ' ':
            high_light_markdown += i[2]
        elif i[0] == '+':
            high_light_markdown += '<mark style="background: green!important">{}</mark>'.format(i[2])
        elif i[0] == '-':
            high_light_markdown += '<mark style="background: yello!important">{}</mark>'.format(i[2])
    high_light_markdown = high_light_markdown.replace('\n', '<br>')
    return high_light_markdown


class TextSplitter:
    '''文本分句'''
    def __init__(self, stops='([，。？?！!；;：:\n ])'):
        '''
        通过正则，设置句子的分隔符
        []里面设置分隔符，表示或者的意思；()表示split的时候，返回分隔符，主要防止索引错位
        '''
        self.stops = stops
        # 提前编译正则，加速
        self.re_split_sentence = re.compile(self.stops)
    
    def split_sentencs_for_seg(self, content, max_len=256):
        '''使用正则regex.split分句'''
        sentences = []
        content = content.strip()
        for sent in self.re_split_sentence.split(content):
            # 分句
            if not sent:
                # 跳过空句子
                continue
            for i in range(math.ceil(len(sent) / max_len)):
                # 对子句进行max_len分段，控制子句长度
                sent_segment = sent[i*max_len:(i+1)*max_len]
                sentences.append(sent_segment)
        return sentences


def document_split_sentence(document, lens=100, stops=['。', '？', '?', '！', '!', '\n']):
    '''按照分隔符以及分割长度分句'''
    document = document.strip()
    text_splitter = TextSplitter("([" + ''.join(stops) + "])")
    document_lst = []
    text_cache = ''
    for sent in text_splitter.split_sentencs_for_seg(document):
        text_cache += sent
        if len(text_cache) > lens:
            document_lst.append(text_cache)
            text_cache = ''
        if sent in text_splitter.stops and text_cache == sent:
            if document_lst != []:
                document_lst[-1] += sent
                text_cache = ''
    document_lst.append(text_cache)
    return document_lst
    
    
class PreCorrect:
    '''pycorrect纠错'''
    def __init__(self):
        self.splitter_stops = ['，', ',', '。', '？', '?', '！', '!', '；', ';', '：', ':', '、', '\n', ' ']
        self.text_splitter = TextSplitter("([" + ''.join(self.splitter_stops) + "])")
    
    def request_pycorrector(self, text, url, model_type):
        headers = {"Content-Type": "application/json"}
        data = {'document': text, 'model_type': model_type, 'threshold': 0.95, 'csid': '1'}
        return requests.post(url, headers=headers, data=json.dumps(data), verify=False).json()

    def pre_correct(self, document, url, model_type='mac_bert'):
        # py_corrector第一次纠错
        document = document.strip()
        document_lst = self.text_splitter.split_sentencs_for_seg(document)
        errors = []
        target = ''
        for document in document_lst:
            if document in self.splitter_stops:
                target += document
            else:
                res = self.request_pycorrector(document, url, model_type)
                errors.extend(res['result'][0]['errors'])
                target += res['result'][0]['target']
        return errors, target