# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

import json
import uuid
import decimal
import datetime
import numpy as np
from flask import Response

# __All__ = ['json_preview', 'JSONEncoder']

STATUS_CODES = {
    "0": "success",
    "100": "parameter error",
    "101": "data duplication",
    "102": "data not found",
    "103": "gpu_id unuseable",
    "104": "fastdfs file transmit error",
    "201": "data exception, please try again",
    "202": "thread exception",
    "500": "系统错误",
    "601": "elemId not found"
}

AZX_STATUS_CODES = {
    "10001": "Parameter error.",
    "10002": "Model prediction failed."
}

class JSONEncoder(json.JSONEncoder):


    def default(self, o):
        """
        如有其他的需求可直接在下面添加
        :param o:
        :return:
        """
        if isinstance(o, datetime.datetime):
            # 格式化时间
            return o.strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(o, datetime.date):
            # 格式化日期
            return o.strftime('%Y-%m-%d')
        if isinstance(o, decimal.Decimal):
            # 格式化高精度数字
            return float(o)
        if isinstance(o, uuid.UUID):
            # 格式化uuid
            return str(o)
        if isinstance(o, bytes):
            # 格式化字节数据
            return o.decode("utf-8")
        if isinstance(o, np.ndarray):
            return o.tolist()

        return json.JSONEncoder.default(self, o)


def azx_json_preview(result, csid='', code=None):
    """
        目前客户提供只有一个10002响应码
    """
    if code:
        err_result = {
            'error': code,
            'message': AZX_STATUS_CODES[code],
            'csid': csid
        }
        return Response(json.dumps(err_result, ensure_ascii=False, cls=JSONEncoder), mimetype='application/json')

    return Response(json.dumps(result, ensure_ascii=False, cls=JSONEncoder), mimetype='application/json')