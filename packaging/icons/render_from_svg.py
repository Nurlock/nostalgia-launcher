#!/usr/bin/env python
"""Render the app icon from the vector source of truth.

Source: ``NostalgiaLauncher-IconNoText.svg`` (repo root).
Produces: ``packaging/icons/NostalgiaLauncher.png`` (256x256) and
``NostalgiaLauncher.ico`` (single-frame PNG-in-ICO, Win Vista+).

Run: ``QT_QPA_PLATFORM=offscreen uv run python packaging/icons/render_from_svg.py``
"""

import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SVG_PATH = os.path.join(ROOT, "NostalgiaLauncher-IconNoText.svg")
PNG_PATH = os.path.join(HERE, "NostalgiaLauncher.png")
ICO_PATH = os.path.join(ROOT, "NostalgiaLauncher.ico")
SIZE = 256


def main() -> None:
    from PySide6.QtCore import (
        QBuffer,
        QByteArray,
        QIODevice,
        QRectF,
        Qt,
    )
    from PySide6.QtGui import QImage, QPainter
    from PySide6.QtSvg import QSvgRenderer
    from PySide6.QtWidgets import QApplication

    QApplication.setAttribute(Qt.AA_UseSoftwareOpenGL, True)
    app = QApplication([])

    renderer = QSvgRenderer(SVG_PATH)
    if not renderer.isValid():
        sys.exit(f"cannot load {SVG_PATH}")

    img = QImage(SIZE, SIZE, QImage.Format_ARGB32)
    img.fill(Qt.transparent)
    painter = QPainter(img)
    target = renderer.defaultSize()
    target.scale(SIZE, SIZE, Qt.KeepAspectRatio)
    x = (SIZE - target.width()) // 2
    y = (SIZE - target.height()) // 2
    renderer.render(painter, QRectF(x, y, target.width(), target.height()))
    painter.end()

    byte_array = QByteArray()
    buf = QBuffer(byte_array)
    buf.open(QIODevice.WriteOnly)
    if not img.save(buf, "PNG"):
        sys.exit("failed to encode PNG")
    buf.close()
    png_bytes = bytes(byte_array.data())

    with open(PNG_PATH, "wb") as fh:
        fh.write(png_bytes)
    header = struct.pack("<HHH", 0, 1, 1)
    entry = struct.pack("<BBBBHHII", 0, 0, 0, 0, 1, 32, len(png_bytes), 6 + 16)
    with open(ICO_PATH, "wb") as fh:
        fh.write(header)
        fh.write(entry)
        fh.write(png_bytes)

    print(f"wrote {PNG_PATH} ({len(png_bytes)} bytes) + {ICO_PATH}")
    app.quit()


if __name__ == "__main__":
    main()
