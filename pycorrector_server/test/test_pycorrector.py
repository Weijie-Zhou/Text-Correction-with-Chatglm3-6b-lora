import requests
import json

document = ['今天新情很好', '你找到你最喜欢的工作，我也很高心。']
model_type = ['mac_bert', 't5']
threshold = 0.9
url = 'http://127.0.0.1:8081/v1/model/corrector'
headers = {"Content-Type": "application/json"}
for model in model_type:
    data = {'document': document, 'model_type': model, 'threshold': threshold, 'csid': '1'}
    res = requests.post(url, headers=headers, data=json.dumps(data))
    print('--------model_type---------', model)
    print(res.json())