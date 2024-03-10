from openai import OpenAI
from prompts import get_correct_prompt
from text_correct_utils import document_split_sentence, punctuation_transform, string_q2b, PreCorrect, TokenizerLengthCheck
from langchain.document_loaders import Docx2txtLoader


class TextCorrect:
    def __init__(self, pycorrector_url="http://127.0.0.1:8081/v1/model/corrector", base_url="http://127.0.0.1:8000/v1/", max_token_length=4096):
        self.pycorrector_url = pycorrector_url
        self.pre_corrcet = PreCorrect()
        self.tokenizer_length_check = TokenizerLengthCheck()
        self.max_token_length = max_token_length
        self.client = OpenAI(api_key="EMPTY", base_url=base_url)
    
    @staticmethod
    def document_loader(document_path):
        file_type = document_path.split('.')[-1]
        if file_type == 'txt':
            with open(document_path, 'r') as f:
                document = f.read()
        elif 'docx' in file_type:
            loader = Docx2txtLoader(document_path)
            document_lst = loader.load()
            document = ''.join([document.page_content for document in document_lst])
        else:
            raise Exception('请上传txt/docx类型的文档')
        return document
        
    def document_normalization(self, document):
        # 前处理：全角转半角、英文标点转中文标点
        document = punctuation_transform(string_q2b(document))
        return document
    
    def gen_correct_prompt(self, document, model_type='mac_bert'):
        # 使用pycorrector进行初步纠错，model_type可选mac-bert或者t5
        errors, _ = self.pre_corrcet.pre_correct(document, self.pycorrector_url, model_type)
        error_prompt = ''''''
        for error in errors:
            if error:
                error_prompt += '''错别字：{}, 修改为：{}\n'''.format(error[0], error[1])
        # 拼接最终的prompt
        query = get_correct_prompt(document, py_corrector_prompt=error_prompt)
        # 判断对prompt进行tokenizer后是否超过最大token长度
        input_length_check_tag = self.tokenizer_length_check.input_length_check(query, len_req=self.max_token_length)
        return query, input_length_check_tag
    
    def simple_chat(self, prompt, use_stream=True, temperature=0.8, presence_penalty=1.1, top_p=0.8):
        # 调用openai接口请求chatglm3-6b-lora
        messages = [
        {
            "role": "system",
            "content": "A chat between a curious user and an artificial intelligence assistant. " \
                    "The assistant gives helpful, detailed, and polite answers to the user's questions. " \
        },
        {
            "role": "user",
            "content": prompt
        }
        ]
        response = self.client.chat.completions.create(
                        model="chatglm3-6b",
                        messages=messages,
                        stream=use_stream,
                        max_tokens=self.max_token_length,
                        temperature=temperature,
                        presence_penalty=presence_penalty,
                        top_p=top_p)
        if response:
            if use_stream:
                # 流式输出
                for chunk in response:
                    chunk = chunk.choices[0].delta.content
                    # print(chunk, end='', flush=True)
                    yield chunk
            else:
                content = response.choices[0].message.content
                # print('content', content)
                yield content
        else:
            print("Error:", response.status_code)
    
    def main(self, content, document_path='', temperature=0.1):
        if document_path:
            # 读取文档文件，并拼接用户输入
            document = self.document_loader(document_path)
            document = content + document
        else:
            document = content
        if len(document) == 0:
            raise Exception('用户没有输入！')
        # 文档标准化
        document = self.document_normalization(document)
        # 拼接prompt，并判断是否超过最大token长度
        query, input_length_check_tag = self.gen_correct_prompt(document)
        if not input_length_check_tag:
            # 超出最大token长度，则对传入文本进行切分后，一段段输入大模型纠错
            document_lst = document_split_sentence(document, lens=100)
            for document in document_lst:
                if document == ' ' or len(document) == 0:
                    continue
                query, _ = self.gen_correct_prompt(document)
                for response in self.simple_chat(query, use_stream=False, temperature=0.1):
                    yield response.replace('纠错后的文本：', '').strip()
        else:
            for response in self.simple_chat(query, temperature=0.1):
                yield response
        
        
if __name__ == '__main__':
    text_correct = TextCorrect()
    content = '''由于原、被告双方就被告应当项受的工伤待遇未达成协议，被告白文举向东丰县劳动人事争议仲裁委员会提出仲裁申请，2013年11月8日，东丰县劳动人事争议仲裁委员会以东人仲字（2013）第16号仲裁书作出裁决：1、吉林鑫达钢铁有限公司支付白文举一次性伤残补助金61，713.60元；2、吉林鑫达钢铁有限公司支付白文举住院期间伙食补助费1，123.5元；3、吉林鑫达钢铁有限公司支付白文举补发停工留薪期待遇6，294.88元；4、从2013年7月1日开始由被申请人吉林鑫达钢铁有限公司按月发给申请人白文举本人工资80%的伤残津贴2，146.56元，当申请人的伤残津贴实际金额低于当地最低工资标准时，由被申请人补足差额；5、从2013年7月1日开始被申请人按月发给申请人生活护理费808.28元，上年度统筹地区职工月平均工资发生变化时，护理费额也应随之调整变化；6、被申请人为申请人安装JS22B-1型假知并在使用寿命届满时予以更换；7、自本仲裁生效之日起30日内被申请人在东丰县社会保险局为申请人办理养老保险参保手续，缴费时间从申请人到被申请人处工作的时间2012年5月份开始，缴至申请人与被申请人劳动关系终止，缴纳保费的缴费基数，申请人与被申请人各自承担的比例和金额，以东丰县社会保险局核定为准，其中应由申请人个人承担保费部分由申请人自负；8、自本裁决书生效之日起30日内，在被申请人参加医疗保险的情况下，由被申请人在东丰县医疗保险经办中心为申请人缴纳医疗保险，具体缴费时间、缴费书额，以东丰县医疗保险经办机构核定为准'''
    for i in text_correct.main(content):
        print(i, end='', flush=True)