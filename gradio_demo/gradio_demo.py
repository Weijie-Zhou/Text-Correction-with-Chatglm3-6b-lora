# -*- coding: utf-8 -*-
import gradio as gr
from text_correct import TextCorrect
from text_correct_utils import high_light

def predict(text, file_path, temperature):
    # 获取纠错返回
    data = ''
    if file_path:
        res = model.main(text, file_path.name, temperature)
    else:
        res = model.main(text, '', temperature)
    for i in res:
        data += i
    return data
        

def gen_highlight_markdown(origin, correct, file_path):
    # 生成高亮对比markdown文本
    if file_path:
        origin = origin + TextCorrect.document_loader(file_path.name)
    markdown_str = high_light(origin, correct)
    return '### 高亮对比，黄色为删除，绿色为修改\n' + markdown_str.strip()


if __name__ == '__main__':
    # 初始化纠错模型
    model = TextCorrect(max_token_length=1024)
    with gr.Blocks() as demo:
        gr.Label('Text Correction with Chatglm3-6b-lora')
        temperature = gr.Slider(label="Temperature", value=0.1,  maximum=1, minimum=0)
        inputs = gr.Textbox(label='请输入需要纠错的文本')
        file_path = gr.File(label='可以上传txt或者docx格式的文档', file_count='single', file_types=['txt', 'docx'], type='file')
        outputs = gr.Textbox(label='纠错后的文本')
        high_light_output = gr.Markdown(label='高亮对比文本')
        btn_correct = gr.Button("文本纠错")
        btn_correct.click(predict, [inputs, file_path, temperature], outputs, show_progress=True)
        btn_highlight = gr.Button("高亮对比")
        btn_highlight.click(gen_highlight_markdown, [inputs, outputs, file_path], high_light_output)
        clear = gr.ClearButton(components=[inputs, outputs, file_path, high_light_output], value="清除内容")
    demo.queue()
    demo.launch(server_name='0.0.0.0', server_port=6006)