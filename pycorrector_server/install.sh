# 创建虚拟环境
conda create -n pycorrector python=3.8
conda activate pycorrector
# 升级pip
python -m pip install --upgrade pip
# 更换 pypi 源加速库的安装
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
pip install -r requirements.txt