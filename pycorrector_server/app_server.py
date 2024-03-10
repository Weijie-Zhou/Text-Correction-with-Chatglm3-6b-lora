# -*- coding: utf-8 -*-
from __future__ import division
from __future__ import print_function
from __future__ import absolute_import
from __future__ import unicode_literals

import os
import sys
sys.path.append("../")


from app_core import app
from views import correct_blue


# 接口注册
app.register_blueprint(correct_blue)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8081, debug=False)