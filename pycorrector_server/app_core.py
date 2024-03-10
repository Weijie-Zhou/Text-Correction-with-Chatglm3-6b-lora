# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

import os
import logging
import traceback
from flask import Flask

from utils import log_file
import app_config
from predict.pycorrector.inference import Inference as Pycorrector_Infer


def creat_app():
    # 将flask的static_folder作为中间结果目录的全局变量
    app = Flask(__name__)
    log_file(logging.INFO)
    return app
app = creat_app()


# 初始化模型
def init_models():
    try:
        # 初始化推理引擎
        py_correct_infer = Pycorrector_Infer(app_config.config)
    except Exception as err:
        logging.error(traceback.format_exc())
        raise "Faild to init pycorrector inference engine."
    return py_correct_infer