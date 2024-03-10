# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals


import logging
import traceback
from flask import request

from utils.deal_response import azx_json_preview


ALLOW_OCR_TYPE_LIST = ()


__ALL__ = ['CorrectApiCommon']


class BaseDealParams:
    '''
    基础请求参数处理
    '''

    @staticmethod
    def get_base_ocr_params():
        
        pass

    @staticmethod
    def getJsonParam(paramName):
        '''
        处理表单请求参数
        :param paramName:
        :return: str | None
        '''
        params = request.get_json()
        if params is None:
            params = request.form
        if params is not None:
            if paramName in params.keys():
                return params[paramName]
        return None

    @staticmethod
    def checkParamIsNull(paramList):
        '''
        校验参数中是否有空值
        :param paramList: type: list、dict
        :return: bool
        '''
        if isinstance(paramList, dict):
            for k, v in paramList.items():
                if v is None or v == "":
                    return True
        else:
            for param in paramList:
                if param is None or param == "":
                    return True
        return False

    @staticmethod
    def checkParamIsStr(paramList):
        '''
        校验参数类型
        :param paramList:
        :return:
        '''
        if isinstance(paramList, dict):
            for k, v in paramList.items():
                if k != "ocr_json" and not isinstance(v, str):
                    return False
        else:
            for param in paramList:
                if not isinstance(param, str):
                    return False
        return True

    @staticmethod
    def isSupportFileType(inputPath):
        '''
        校验文件类型是否允许OCR
        :param inputPath:
        :return:
        '''
        file_type = inputPath.split('.')[-1].lower()
        return (file_type in ALLOW_OCR_TYPE_LIST)


class CorrectApiCommon(BaseDealParams):
    """处理文本纠错所需的参数"""

    model_configs = None
    model_merge_map = None
    merge_elem_dict_map = {}

    @staticmethod
    def parse_request():
        """
            处理请求的数据读取, 玩咯延时耗时处理接受请求
        """
        document, model_type, threshold, csid = None, None, None, ''
        try:
            # 由平台验证并透传 app_id + capability_name + suid  
            headers = request.headers
            logging.info("request headers is: {}".format(str(headers)))
            if request.method == 'POST':
                csid = CorrectApiCommon.getJsonParam("csid")
                if not csid:
                    logging.error("The required parameter csid is missing")
                    raise ValueError()
                document = CorrectApiCommon.getJsonParam('document')
                model_type = CorrectApiCommon.getJsonParam('model_type')
                threshold =  CorrectApiCommon.getJsonParam('threshold')
            else:
                logging.error('Request method not support.')
                return azx_json_preview('', csid=csid, code='10001')
            

            logging.info('Get request parameters successfully.')

            return document, model_type, threshold, csid
        except Exception as err:
            logging.error('Failed to get request parameter timeout')
            logging.error(traceback.format_exc())
            return azx_json_preview('', csid=csid, code='10001')

    @staticmethod
    def get_ext_parame(document=None, model_type=None, threshold=None):
        """
            处理预测接口参数
        """
        try:
            # 这里将会兼容三种方式传递参数, 首先以图片为主, 其次是pdf文件, 最后是url,
            if not any([document, model_type, threshold]):
                return None
                    
            ext_parama = {
                "document": document,
                "model_type": model_type,
                "threshold": threshold
            }
            return ext_parama
        except Exception as err:
            logging.error(traceback.format_exc())
            raise "Parse parameter error."
     