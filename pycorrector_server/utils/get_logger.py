# # -*- coding: utf-8 -*-

import io
import os
import re
import time

from portalocker import LOCK_EX, lock, unlock
from contextlib import contextmanager
import logging
from logging.handlers import TimedRotatingFileHandler
from logging import FileHandler

import app_config


# 根据开源包 ConcurrentRotatingFileHandler 抽象出给文件加锁的类
class ConcurrentLock(FileHandler):
    def __init__(self, filename, mode='a', encoding=None, delay=False, umask=None):
        """
        Use the specified filename for streamed logging
        """
        self.mode = mode
        self.encoding = encoding
        FileHandler.__init__(self, filename, mode, encoding, delay)

        self.terminator = "\n"
        self.lockFilename = self.getLockFilename()
        self.is_locked = False
        self.stream_lock = None
        self.umask = umask
        self.unicode_error_policy = 'ignore'

    def getLockFilename(self):
        """
        Decide the lock filename. If the logfile is file.log, then we use `.__file.lock` and
        not `file.log.lock`. This only removes the extension if it's `*.log`.
        :return: the path to the lock file.
        """
        if self.baseFilename.endswith(".log"):
            lock_file = self.baseFilename[:-4]
        else:
            lock_file = self.baseFilename
        lock_file += ".lock"
        lock_path, lock_name = os.path.split(lock_file)
        # hide the file on Unix and generally from file completion
        lock_name = ".__" + lock_name
        return os.path.join(lock_path, lock_name)

    def _open_lockfile(self):
        if self.stream_lock and not self.stream_lock.closed:
            return
        lock_file = self.lockFilename

        with self._alter_umask():
            self.stream_lock = open(lock_file, "wb", buffering=0)

    def _open(self, mode=None):
        # Normally we don't hold the stream open. Only do_open does that
        # which is called from do_write().
        return None

    def do_open(self, mode=None):
        """
        Open the current base file with the (original) mode and encoding.
        Return the resulting stream.
        Note:  Copied from stdlib.  Added option to override 'mode'
        使用（原始）模式和编码打开当前基本文件。
        返回结果流。
        注：从stdlib复制。添加了覆盖“模式”的选项
        """
        if mode is None:
            mode = self.mode
        with self._alter_umask():
            stream = io.open(self.baseFilename, mode=mode)
        return stream

    @contextmanager
    def _alter_umask(self):
        """Temporarily alter umask to custom setting, if applicable 临时将umask更改为自定义设置（如果适用）"""
        if self.umask is None:
            yield  # nothing to do
        else:
            prev_umask = os.umask(self.umask)
            try:
                yield
            finally:
                os.umask(prev_umask)

    def _close(self):
        """ Close file stream.  Unlike close(), we don't tear anything down, we
        expect the log to be re-opened after rotation."""

        if self.stream:
            try:
                if not self.stream.closed:
                    # Flushing probably isn't technically necessary, but it feels right
                    self.stream.flush()
                    self.stream.close()
            finally:
                self.stream = None

    def flush(self):
        """Does nothing; stream is flushed on each write."""
        return

    def do_write(self, msg):
        """Handling writing an individual record; we do a fresh open every time.
        This assumes emit() has already locked the file."""
        self.stream = self.do_open()
        stream = self.stream
    
        msg = msg + self.terminator
        try:
            stream.write(msg)
        except UnicodeError:
            # Try to emit in a form acceptable to the output encoding
            # The unicode_error_policy determines whether this is lossy.
            try:
                encoding = getattr(stream, 'encoding', self.encoding or 'us-ascii')
                msg_bin = msg.encode(encoding, self.unicode_error_policy)
                msg = msg_bin.decode(encoding, self.unicode_error_policy)
                stream.write(msg)
            except UnicodeError:
                raise

        stream.flush()
        self._close()
        return


    def _do_lock(self):
        if self.is_locked:
            raise   # already locked... recursive?
        self._open_lockfile()
        if self.stream_lock:
            for i in range(10):
                # noinspection PyBroadException
                try:
                    lock(self.stream_lock, LOCK_EX)
                    self.is_locked = True
                    break
                except Exception:
                    continue
            else:
                raise RuntimeError("Cannot acquire lock after 10 attempts")

    def _do_unlock(self):
        if self.stream_lock:
            if self.is_locked:
                unlock(self.stream_lock)
                self.is_locked = False
            self.stream_lock.close()
            self.stream_lock = None

    
# # 继承TimedRotatingFileHandler类，然后修改了doRollover方法，和emit方法
class MyTimedRotatingFileHandler(TimedRotatingFileHandler, ConcurrentLock):
    def __init__(self, filename, when='h', interval=1, backupCount=15, encoding=None, delay=False, utc=False, atTime=None):
        TimedRotatingFileHandler.__init__(self, filename, when, interval, backupCount, encoding, delay, utc, atTime)
        ConcurrentLock.__init__(self, filename, 'a', encoding, delay)
        
    def shouldRollover(self, record):
        del record
        return self._shouldRollover()

    def _shouldRollover(self):
        self.stream = self.do_open()
        t = int(time.time())
        if t >= self.rolloverAt:
            return 1
        self._close()
        return 0

    def doRollover(self):
        self._close()
        currentTime = int(time.time())
        dstNow = time.localtime(currentTime)[-1]
        t = self.rolloverAt - self.interval
        if self.utc:
            timeTuple = time.gmtime(t)
        else:
            timeTuple = time.localtime(t)
            dstThen = timeTuple[-1]
            if dstNow != dstThen:
                if dstNow:
                    addend = 3600
                else:
                    addend = -3600
                timeTuple = time.localtime(t + addend)

        dfn = "%s.%s" % (self.baseFilename, time.strftime(self.suffix, timeTuple))
        # if os.path.exists(dfn):
        #     os.remove(dfn)
        if not os.path.exists(dfn) and os.path.exists(self.baseFilename):
            os.rename(self.baseFilename, dfn)

        if self.backupCount > 0:
            for s in self.getFilesToDelete():
                os.remove(s)
        if not self.delay:
            self.stream = self.do_open()
        newRolloverAt = self.computeRollover(currentTime)
        while newRolloverAt <= currentTime:
            newRolloverAt = newRolloverAt + self.interval
        if (self.when == 'MIDNIGHT' or self.when.startswith('W')) and not self.utc:
            dstAtRollover = time.localtime(newRolloverAt)[-1]
            if dstNow != dstAtRollover:
                if not dstNow:
                    addend = -3600
                else:
                    addend = 3600
                newRolloverAt += addend
        self.rolloverAt = newRolloverAt

    def emit(self, record):
        """
            发出一个记录。从父类重写以在滚动和写入期间处理文件锁定。这也会在获取*锁之前格式化*以防格式本身记录内部的调用。锁定时也会发生翻转。
        """
        # noinspection PyBroadException
        try:
            msg = self.format(record)
            try:
                self._do_lock()
                try:
                    if self.shouldRollover(record):
                        self.doRollover()
                except Exception as e:
                    pass
                self.do_write(msg)
            finally:
                self._do_unlock()

        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception:
            self.handleError(record)
    
    
def log_file(LEVEL):
    """记录日志内容"""
    # 设置日志的记录等级
    logging.basicConfig(level=LEVEL) # 调试debug级
    # 获取当前文件的目录
    # current_dir= os.getcwd()
    # if not os.path.isdir(current_dir + "/logs"):
    #     os.makedirs(current_dir+"/logs")
    logger_dir_path = os.path.dirname(app_config.LOGGING_FILE_PATH)
    if not os.path.exists(logger_dir_path):
        os.makedirs(logger_dir_path)
    # log_path = current_dir + "/logs" + "/console.log"
    log_path = app_config.LOGGING_FILE_PATH
    # logs/log--需要修改成自己定义的路径&文件名
    # 创建日志记录器，指明日志保存的路径、每个日志文件的最大大小、保存的日志文件个数上限
    file_log_handler = MyTimedRotatingFileHandler(filename=log_path, when="MIDNIGHT", interval=1, backupCount=14)
    file_log_handler.suffix = "%Y-%m-%d.log"
    file_log_handler.extMatch = re.compile(r"^\d{4}-\d{2}-\d{2}.log$")

    # 创建日志记录的格式 日志等级 输入日志信息的文件名 行数 日志信息
    formatter = logging.Formatter('[%(asctime)s] [%(process)d]' + ' [{}] '.format(id) + '[%(levelname)s] - %(module)s.%(funcName)s (%(filename)s:%(lineno)d) - %(message)s')
    # 为刚创建的日志记录器设置日志记录格式
    file_log_handler.setFormatter(formatter) # 为全局的日志工具对象（flask app使用的）添加日志记录器
    logging.getLogger().addHandler(file_log_handler)


    # std_log_handler = logging.StreamHandler(file_log_handler)
    # std_log_handler.suffix = "%Y-%m-%d.log"
    # std_log_handler.extMatch = re.compile(r"^\d{4}-\d{2}-\d{2}.log$")

    # # 创建日志记录的格式 日志等级 输入日志信息的文件名 行数 日志信息
    # formatter = logging.Formatter('[%(asctime)s] [%(process)d] [%(levelname)s] - %(module)s.%(funcName)s (%(filename)s:%(lineno)d) - %(message)s')
    # # 为刚创建的日志记录器设置日志记录格式
    # std_log_handler.setFormatter(formatter) # 为全局的日志工具对象（flask app使用的）添加日志记录器
    # logging.getLogger().addHandler(file_log_handler)