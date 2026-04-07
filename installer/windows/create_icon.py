# ============================================================================
# Copyright (c) 2026 정화민 (Junghwamin)
# All rights reserved.
#
# This file is part of a personal research analysis portal by 정화민 (Junghwamin).
# Licensed under the PolyForm Noncommercial License 1.0.0.
# See the LICENSE file in the project root, or visit:
#     https://polyformproject.org/licenses/noncommercial/1.0.0
#
# Commercial use is strictly prohibited without prior written consent.
# Repository: https://github.com/Junghwamin/Hoseo-IR-
# Hoseo-IR-FINGERPRINT: do not remove this line (used for provenance tracking)
# ============================================================================

"""
앱 아이콘(.ico) 생성 스크립트

Pillow로 간단한 차트 아이콘을 생성한다.
Pillow가 없으면 기본 아이콘 없이 진행.

사용법:
    pip install Pillow
    python installer/windows/create_icon.py
"""

import struct
from pathlib import Path


def create_simple_ico(output_path: Path):
    """BMP 기반의 간단한 32x32 ICO 파일을 순수 Python으로 생성한다."""
    size = 32
    # BGRA 픽셀 데이터 (32x32, 하단→상단 순서)
    pixels = bytearray()

    for y_inv in range(size):
        y = size - 1 - y_inv  # BMP는 아래→위 순서
        for x in range(size):
            # 배경: 진한 파란색 (#1B3A5C)
            b, g, r, a = 0x5C, 0x3A, 0x1B, 0xFF

            # 테두리 (1px)
            if x == 0 or x == size - 1 or y == 0 or y == size - 1:
                b, g, r, a = 0x79, 0x4E, 0x1F, 0xFF  # 약간 밝은 파란

            # "IR" 텍스트 영역 (중앙)
            # I: x=10~12, y=8~23
            if 10 <= x <= 12 and 8 <= y <= 23:
                b, g, r, a = 0xFF, 0xFF, 0xFF, 0xFF  # 흰색

            # R: x=15~22, y=8~23
            # R 세로줄
            if 15 <= x <= 17 and 8 <= y <= 23:
                b, g, r, a = 0xFF, 0xFF, 0xFF, 0xFF
            # R 상단 가로
            if 17 <= x <= 22 and 8 <= y <= 10:
                b, g, r, a = 0xFF, 0xFF, 0xFF, 0xFF
            # R 중간 가로
            if 17 <= x <= 22 and 14 <= y <= 16:
                b, g, r, a = 0xFF, 0xFF, 0xFF, 0xFF
            # R 오른쪽 세로 (상단)
            if 20 <= x <= 22 and 10 <= y <= 14:
                b, g, r, a = 0xFF, 0xFF, 0xFF, 0xFF
            # R 대각선 (하단)
            diag_x = 17 + (y - 16) * 5 // 7
            if 16 <= y <= 23 and diag_x <= x <= diag_x + 2 and x <= 23:
                b, g, r, a = 0xFF, 0xFF, 0xFF, 0xFF

            # 하단 차트 바 영역 (y=25~30)
            if 25 <= y <= 30:
                bar_heights = {5: 3, 6: 5, 7: 4, 8: 6, 9: 3,
                               10: 5, 11: 4, 12: 6, 13: 5, 14: 3,
                               17: 4, 18: 6, 19: 5, 20: 3, 21: 5,
                               22: 6, 23: 4, 24: 5, 25: 3, 26: 6}
                if x in bar_heights and y >= 31 - bar_heights[x]:
                    b, g, r, a = 0x0E, 0x7F, 0xFF, 0xFF  # 주황색 (#FF7F0E)

            pixels.extend([b, g, r, a])

    # AND mask (32x32, 1bpp = 4 bytes/row)
    and_mask = b"\x00" * (4 * size)

    # BMP InfoHeader (BITMAPINFOHEADER)
    bmp_header = struct.pack(
        "<IiiHHIIiiII",
        40,          # biSize
        size,        # biWidth
        size * 2,    # biHeight (ICO에서는 2배)
        1,           # biPlanes
        32,          # biBitCount (BGRA)
        0,           # biCompression
        len(pixels) + len(and_mask),  # biSizeImage
        0, 0,        # biXPelsPerMeter, biYPelsPerMeter
        0, 0,        # biClrUsed, biClrImportant
    )

    # ICO 파일 구조
    image_data = bmp_header + bytes(pixels) + and_mask
    ico_dir = struct.pack("<HHH", 0, 1, 1)  # Reserved, Type=1(ICO), Count=1
    ico_entry = struct.pack(
        "<BBBBHHII",
        size,         # Width
        size,         # Height
        0,            # ColorCount
        0,            # Reserved
        1,            # Planes
        32,           # BitCount
        len(image_data),  # BytesInRes
        6 + 16,       # ImageOffset (header=6 + entry=16)
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(ico_dir + ico_entry + image_data)

    print(f"  아이콘 생성 완료: {output_path}")


if __name__ == "__main__":
    icon_path = Path(__file__).parent / "icon.ico"
    create_simple_ico(icon_path)
