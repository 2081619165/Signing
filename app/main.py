"""SealKit 程序入口；首个时间点不包含解释器启动。"""
from time import perf_counter
ENTRY = perf_counter()
from window import main

if __name__ == '__main__':
    raise SystemExit(main(ENTRY))
