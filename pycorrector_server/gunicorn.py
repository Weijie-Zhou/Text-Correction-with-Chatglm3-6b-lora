# -*- coding: utf-8 -*-
# import os
# import pynvml  
# import multiprocessing

# def getFreeGPUMemory():
#     pynvml.nvmlInit()
#     handle = pynvml.nvmlDeviceGetHandleByIndex(0)
#     info = pynvml.nvmlDeviceGetMemoryInfo(handle)
#     pynvml.nvmlShutdown()
#     return info.free / 1024 / 1024  # MiB

# 进程数

# workers = multiprocessing.cpu_count() * 2 + 1  

# print('free gup: {} Mib'.format(getFreeGPUMemory()))
# workers = os.environ.get('GUNICORN_WORKERS', None) or int(getFreeGPUMemory() / (1024 * 2))  # 根据当前所剩显存除以模型的最大占用来判断需要起几个进程

# 根据GPU进行自动分配worker
import os
try:
    import pynvml 
    pynvml.nvmlInit()
    gpuDeviceCount = pynvml.nvmlDeviceGetCount()
except:
    gpuDeviceCount = 1 #8
gpuDevicePool = []
 
def pre_fork(server, worker):
    try:
        gid = gpuDevicePool.pop(0)
    except:
        gid = (worker.age - 1) % gpuDeviceCount
    worker.gid = gid
 
def post_fork(server,worker):
    os.environ['CUDA_VISIBLE_DEVICES'] = str(worker.gid)
    server.log.info(f'worker(age:{worker.age}, pid:{worker.pid}, cuda:{worker.gid})')
    
def child_exit(server, worker):
    gpuDevicePool.append(worker.gid)


workers = 1  # 工作进程数

backlog = 2048  # 等待服务客户的数量，最大为2048，即最大挂起的连接数
max_requests = 1000  # 默认的最大客户端并发数量
daemon = False
reload = False  # 当代码有修改时，自动重启workers。适用于开发环境
timeout = 180  # 最大超时

bind = '0.0.0.0:8081'  # 绑定监听ip和端口号和启动docker端口映射一致
pidfile = './logs/app_server.pid'  # 设置pid文件的文件名
# 状态行 - 时间 - 进程id - Host - User-Agent - Accept-Encoding - Accept - Connection - X-Server-Param - X-Checksum - X-Curtime - Content-Length - Content-Type
access_log_format = "%(r)s  %(s)s %(H)s  %(L)s  %(p)s %(h)s %(a)s %({Accept-Encoding}i)s %({Accept}i)s %({connection}i)s %({X-Server-Param}i)s %({X-Checksum}i)s %({X-Curtime}i)s %({Content-Length}i)s %({Content-Type}i)s"
accesslog = './logs/app_server.log'  # 置访问日志
errorlog = './logs/app_server.log'  # 设置问题记录日志
