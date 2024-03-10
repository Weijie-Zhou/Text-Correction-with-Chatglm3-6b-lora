# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

import sys
import time
import logging 

class CoastTime(object):

    def __init__(self, func_name):

        self.t = 0
        self.func_name = func_name

    def __enter__(self):

        self.t = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):

        logging.info(f'{self.func_name} coast time:{time.perf_counter() - self.t:.8f} s')


def coast_time(func):
    # 计算功能耗时
    def fun(*agrs, **kwargs):
        t = time.perf_counter()
        result = func(*agrs, **kwargs)
        s = sys._getframe()
        stack_info = f">> {s.f_code.co_filename} function: {func.__name__} line: {s.f_lineno}"
        decorate_info = f"function {func.__name__} coast time: {time.perf_counter() - t:.8f} s"
        logging.info(decorate_info)
        logging.info(stack_info)
        return result
    return fun
