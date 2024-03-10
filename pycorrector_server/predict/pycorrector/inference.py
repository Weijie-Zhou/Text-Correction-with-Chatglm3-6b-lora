# -*- coding: utf-8 -*-
import logging
import traceback
from utils import coast_time

from pycorrector import MacBertCorrector
from pycorrector import T5Corrector

import torch

torch.inference_mode = torch.no_grad



class Inference:
    def __init__(self, config):
        mac_bert_path = config['py_corrector_model']['macbert4csc_base_chinese_path']
        t5_path = config['py_corrector_model']['mengzi_t5_base_chinese_correction_path']
        self.correct_model_mac_bert = MacBertCorrector(mac_bert_path)
        self.correct_model_t5 = T5Corrector(t5_path)

    def corrector_mac_bert(self, document, max_len=128, threshold=0.9, batch_size=32):
        if type(document) == str:
            document = [document]
        if type(document) == list:
            batch_size = len(document)
        res = self.correct_model_mac_bert.correct_batch(document, max_length=max_len, threshold=threshold, batch_size=batch_size)
        return res
        
    def corrector_t5(self, document, max_len=128, batch_size=32):
        if type(document) == str:
            document = [document]
        if type(document) == list:
            batch_size = len(document)
        res = self.correct_model_t5.correct_batch(document, max_length=max_len, batch_size=batch_size)
        return res
    
    @coast_time
    def __call__(self, inputs):
        """
            :param inputs: 输入
        """
        try:
            document, model_type, threshold = inputs['document'], inputs['model_type'], inputs['threshold']
            if model_type == 'mac_bert' and threshold:
                return self.corrector_mac_bert(document, threshold=threshold)
            elif model_type == 't5':
                return self.corrector_t5(document)
        except Exception as err:
            logging.error(traceback.format_exc())
            raise "Faild to model predict."