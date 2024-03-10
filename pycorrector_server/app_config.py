# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

import os
import re
import json


# ------------全局配置参数------------------
# 预测根目录
BASE_PATH = os.path.join(os.path.dirname(os.getcwd()), 'pycorrector_server')
# 模型存放目录
BASE_ASSETS_PATH = BASE_PATH + "/assets"
# 日志路径
LOGGING_FILE_PATH = os.path.join(BASE_PATH, 'logs/app_server.log')
# 服务版本号
VERSION = 'v1.1_20240123'


config = {
    "py_corrector_model": {
        "macbert4csc_base_chinese_path": BASE_ASSETS_PATH + "/macbert4csc-base-chinese", 
        "mengzi_t5_base_chinese_correction_path": BASE_ASSETS_PATH + "/mengzi-t5-base-chinese-correction"
    }
}

