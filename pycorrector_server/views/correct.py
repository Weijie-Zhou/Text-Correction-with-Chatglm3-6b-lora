# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

import time 
import json
import logging
import traceback
from flask import Blueprint, Response

from app_config import VERSION
from app_core import init_models
from utils import azx_json_preview, CorrectApiCommon, JSONEncoder


correct_blue = Blueprint('correct', __name__)
correct_infer = init_models()  # 模型对象


def construct_response_result(response, csid, start_time, VERSION):
    """
        构造响应体
    """
    final_result = {}

    cost_time = time.time() - start_time

    final_result['version'] = VERSION
    final_result['csid'] = csid
    final_result['timestamp'] = int(time.time())
    final_result['time_cost'] = str(cost_time)
    final_result['code'] = "200"
    final_result['result'] = response

    return final_result

# py_corrector文本纠错
@correct_blue.route('/v1/model/corrector', methods=['POST'])
def correct_predict():
    """文本纠错入口"""
    # 这里是网络传输耗时
    req_start_time = time.time()
    document, model_type, threshold, csid = CorrectApiCommon.parse_request()
    req_end_time = time.time()
    logging.info('The request data reception is completed, cost: {} s'.format(req_end_time - req_start_time))        
    logging.info('The current program fingerprint is: {}'.format(csid))
    try:        
        start_time = time.time()
        correct_parame = CorrectApiCommon.get_ext_parame(document, model_type, threshold)
        logging.info('Image preprocess cost: {}'.format(time.time() - start_time))
        if not correct_parame:
            logging.error('The parameter error, please check the input parameters.')
            return azx_json_preview('', csid=csid, code='10001')
        
        def generate():
            """返回响应"""
            response = correct_infer.__call__(correct_parame)
            final_result = construct_response_result(response, csid, start_time, VERSION)
            logging.info('final_result: {}'.format(final_result))
            return final_result
        return Response(json.dumps(generate(), ensure_ascii=False, cls=JSONEncoder), mimetype='application/json')
        # return Response(generate())
    
    except:
        logging.error(traceback.format_exc())
        return azx_json_preview('', csid=csid, code='10002')


@correct_blue.route("/health")
def health():
    result = {'status': 'UP'}
    return Response(json.dumps(result), mimetype='application/json')