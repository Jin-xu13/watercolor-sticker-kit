#!/usr/bin/env python3
"""把白底贴纸 PNG 抠成透明底。纯标准库实现，不依赖 Pillow / numpy。

用法:
    python matte.py <输入.png> [输出.png]

算法: 从画布四边出发做洪水填充，只吃掉「接近纯白且中性」的像素，
      贴纸内部的暖白留边(偏黄)和浮动投影(偏灰、明度低)都会被保留。

若省略输出路径，会写成 <输入名>-alpha.png。
"""

import sys
import os
import zlib
import struct
from collections import deque

# 判定「白底」的阈值。暖白留边 #F7F2E8 的通道极差为 15，
# 靠 MAX_CHROMA 把它挡在外面，不会被误删。
MIN_LEVEL = 238   # 三通道都要 >= 这个值
MAX_CHROMA = 10   # 三通道极差要 <= 这个值（纯白/灰才符合，暖白不符合）


def decode_png(path):
    """读 8bit RGB/RGBA 非隔行 PNG，返回 (w, h, bytearray RGBA)。"""
    data = open(path, "rb").read()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("不是 PNG 文件: %s" % path)

    pos, idat = 8, []
    w = h = ct = bd = interlace = None
    while pos < len(data):
        (length,) = struct.unpack(">I", data[pos:pos + 4])
        ctype = data[pos + 4:pos + 8]
        chunk = data[pos + 8:pos + 8 + length]
        if ctype == b"IHDR":
            w, h, bd, ct = struct.unpack(">IIBB", chunk[:10])
            interlace = chunk[12]
        elif ctype == b"IDAT":
            idat.append(chunk)
        elif ctype == b"IEND":
            break
        pos += 12 + length

    if bd != 8:
        raise ValueError("只支持 8bit 位深，当前 %s" % bd)
    if interlace:
        raise ValueError("不支持隔行 PNG")
    if ct not in (2, 6):
        raise ValueError("只支持 color type 2(RGB) / 6(RGBA)，当前 %s" % ct)

    raw = zlib.decompress(b"".join(idat))
    bpp = 3 if ct == 2 else 4
    stride = w * bpp
    out = bytearray(h * stride)
    prev = bytearray(stride)
    p = 0
    for y in range(h):
        f = raw[p]
        p += 1
        line = bytearray(raw[p:p + stride])
        p += stride
        if f == 1:
            for i in range(bpp, stride):
                line[i] = (line[i] + line[i - bpp]) & 0xFF
        elif f == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 0xFF
        elif f == 3:
            for i in range(stride):
                a = line[i - bpp] if i >= bpp else 0
                line[i] = (line[i] + ((a + prev[i]) >> 1)) & 0xFF
        elif f == 4:
            for i in range(stride):
                a = line[i - bpp] if i >= bpp else 0
                b = prev[i]
                c = prev[i - bpp] if i >= bpp else 0
                pp = a + b - c
                pa, pb, pc = abs(pp - a), abs(pp - b), abs(pp - c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (line[i] + pr) & 0xFF
        out[y * stride:(y + 1) * stride] = line
        prev = line

    if ct == 6:
        return w, h, out

    rgba = bytearray(w * h * 4)
    for i in range(w * h):
        rgba[i * 4] = out[i * 3]
        rgba[i * 4 + 1] = out[i * 3 + 1]
        rgba[i * 4 + 2] = out[i * 3 + 2]
        rgba[i * 4 + 3] = 255
    return w, h, rgba


def is_background(rgba, idx):
    r, g, b = rgba[idx], rgba[idx + 1], rgba[idx + 2]
    if r < MIN_LEVEL or g < MIN_LEVEL or b < MIN_LEVEL:
        return False
    return (max(r, g, b) - min(r, g, b)) <= MAX_CHROMA


def matte(w, h, rgba):
    """四边洪水填充，把连通的白底设为 alpha=0。返回被清除的像素数。"""
    removed = bytearray(w * h)
    q = deque()

    def push(x, y):
        n = y * w + x
        if not removed[n] and is_background(rgba, n * 4):
            removed[n] = 1
            q.append(n)

    for x in range(w):
        push(x, 0)
        push(x, h - 1)
    for y in range(h):
        push(0, y)
        push(w - 1, y)

    count = 0
    while q:
        n = q.popleft()
        count += 1
        x, y = n % w, n // w
        if x > 0:
            push(x - 1, y)
        if x < w - 1:
            push(x + 1, y)
        if y > 0:
            push(x, y - 1)
        if y < h - 1:
            push(x, y + 1)

    for n in range(w * h):
        if removed[n]:
            rgba[n * 4 + 3] = 0
    return count


def encode_png(path, w, h, rgba):
    raw = bytearray()
    stride = w * 4
    for y in range(h):
        raw.append(0)  # filter type 0
        raw += rgba[y * stride:(y + 1) * stride]

    def chunk(tag, payload):
        return (struct.pack(">I", len(payload)) + tag + payload +
                struct.pack(">I", zlib.crc32(tag + payload) & 0xFFFFFFFF))

    ihdr = struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        f.write(chunk(b"IHDR", ihdr))
        f.write(chunk(b"IDAT", zlib.compress(bytes(raw), 9)))
        f.write(chunk(b"IEND", b""))


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    src = sys.argv[1]
    dst = sys.argv[2] if len(sys.argv) > 2 else os.path.splitext(src)[0] + "-alpha.png"

    w, h, rgba = decode_png(src)
    cleared = matte(w, h, rgba)
    encode_png(dst, w, h, rgba)

    pct = 100.0 * cleared / (w * h)
    print("%dx%d，清除白底 %.1f%%，已写入 %s" % (w, h, pct, dst))
    if pct < 5:
        print("警告: 清除面积过小，可能背景不是白底，检查一下输入图。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
