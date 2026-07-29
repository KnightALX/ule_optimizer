"""项目日志模块（标准库 logging）。

格式：<时间戳> [<LEVEL>] <logger> — <message>
例：2026-07-29 23:50:00 [INFO] ule_opt.parsers.path_extract — BFS 起点=in, 目标=out
"""
from __future__ import annotations
import logging
import sys

_FORMAT = "%(asctime)s [%(levelname)s] %(name)s — %(message)s"
_DATEFMT = "%Y-%m-%d %H:%M:%S"


def get_logger(name: str) -> logging.Logger:
    """获取或创建带格式的 logger。多次调用返回同一实例。"""
    lg = logging.getLogger(name)
    if not lg.handlers:
        h = logging.StreamHandler(sys.stderr)
        h.setFormatter(logging.Formatter(_FORMAT, datefmt=_DATEFMT))
        lg.addHandler(h)
        lg.setLevel(logging.INFO)
        lg.propagate = False
    return lg
