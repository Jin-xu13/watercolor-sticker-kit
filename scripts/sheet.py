#!/usr/bin/env python3
"""把一组透明贴纸拼成一张预览页。纯标准库实现，不依赖 Pillow。

用法:
    python sheet.py <输出.png> [--cols 3] [--cell 512] [--bg bfc7cc] <贴纸1.png> <贴纸2.png> ...

贴纸按面积加权缩小（box filter），不会出现锯齿。预览页背景不透明，
透明贴纸本身不在此脚本内修改。
"""

import sys
import os
import zlib
import struct

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from matte import decode_png, encode_png  # noqa: E402


def hex_to_rgb(s):
    s = s.lstrip("#")
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16))


def downscale(w, h, rgba, dw, dh):
    """box filter，带 alpha 加权，输出 dw*dh RGBA。"""
    out = bytearray(dw * dh * 4)
    for dy in range(dh):
        y0 = dy * h // dh
        y1 = max(y0 + 1, (dy + 1) * h // dh)
        for dx in range(dw):
            x0 = dx * w // dw
            x1 = max(x0 + 1, (dx + 1) * w // dw)
            r = g = b = a = 0
            n = 0
            for y in range(y0, y1):
                base = y * w
                for x in range(x0, x1):
                    i = (base + x) * 4
                    al = rgba[i + 3]
                    r += rgba[i] * al
                    g += rgba[i + 1] * al
                    b += rgba[i + 2] * al
                    a += al
                    n += 1
            if n == 0:
                n = 1
            o = (dy * dw + dx) * 4
            if a > 0:
                out[o] = min(255, r // a)
                out[o + 1] = min(255, g // a)
                out[o + 2] = min(255, b // a)
            out[o + 3] = a // n
    return out


def main():
    args = sys.argv[1:]
    if len(args) < 2:
        print(__doc__)
        return 1
    dst = args[0]
    cols, cell, bg = 3, 512, (191, 199, 204)
    files = []
    i = 1
    while i < len(args):
        a = args[i]
        if a == "--cols":
            cols = int(args[i + 1]); i += 2
        elif a == "--cell":
            cell = int(args[i + 1]); i += 2
        elif a == "--bg":
            bg = hex_to_rgb(args[i + 1]); i += 2
        else:
            files.append(a); i += 1

    if not files:
        print("没有输入文件")
        return 1

    rows = (len(files) + cols - 1) // cols
    margin = gap = max(8, cell // 40)
    W = margin * 2 + cols * cell + (cols - 1) * gap
    H = margin * 2 + rows * cell + (rows - 1) * gap

    canvas = bytearray(W * H * 4)
    for n in range(W * H):
        canvas[n * 4] = bg[0]
        canvas[n * 4 + 1] = bg[1]
        canvas[n * 4 + 2] = bg[2]
        canvas[n * 4 + 3] = 255

    for idx, fp in enumerate(files):
        w, h, px = decode_png(fp)
        small = downscale(w, h, px, cell, cell)
        cx = margin + (idx % cols) * (cell + gap)
        cy = margin + (idx // cols) * (cell + gap)
        for y in range(cell):
            drow = (cy + y) * W
            srow = y * cell
            for x in range(cell):
                si = (srow + x) * 4
                a = small[si + 3]
                if a == 0:
                    continue
                di = (drow + cx + x) * 4
                f = a / 255.0
                for k in range(3):
                    canvas[di + k] = int(small[si + k] * f + canvas[di + k] * (1 - f))

    encode_png(dst, W, H, canvas)
    print("%d 枚 -> %dx%d 预览页: %s" % (len(files), W, H, dst))
    return 0


if __name__ == "__main__":
    sys.exit(main())
