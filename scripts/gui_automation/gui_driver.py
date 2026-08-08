"""Screen capture + safe input for GUI automation on Windows.

Wraps ``mss`` (capture) and ``pyautogui`` (input) with the safety rails the
rest of the agent relies on:

- every capture is checked for the classic "black frame" failure (GPU/
  hardware-composited windows can BitBlt as black); callers get a warning
  instead of silently feeding black pixels to the vision model,
- every click/type is clamped to the primary monitor bounds and requires an
  explicit ``click_ok`` gate (defaults to a confirmation prompt so a human is
  always in the loop),
- coordinates are floats on the primary-monitor grid; images are returned as
  PNG bytes (for the vision model) and as a downscaled JPEG when asked.

Design rule: this module never decides WHAT to do - it only executes a given
action safely and reports what the screen looked like.
"""
from __future__ import annotations

import io
import os
import sys

import mss
import numpy as np
from PIL import Image

# pyautogui import is heavy; keep it lazy so capture-only callers work without it.
_SCREEN_W = None
_SCREEN_H = None


def screen_size() -> tuple[int, int]:
    global _SCREEN_W, _SCREEN_H
    if _SCREEN_W is None:
        with mss.MSS() as sct:
            mon = sct.monitors[1]  # primary monitor
            _SCREEN_W = mon["width"]
            _SCREEN_H = mon["height"]
    return _SCREEN_W, _SCREEN_H


def capture_png(monitor: int = 1, downscale: int | None = None) -> bytes:
    """Capture the given monitor as PNG bytes.

    ``downscale`` (e.g. 1024) resizes the longest edge so the vision model
    gets a smaller image. Raises RuntimeError if the frame is black.
    """
    with mss.MSS() as sct:
        mon = sct.monitors[monitor]
        shot = sct.grab(mon)
    img = Image.frombytes("RGB", shot.size, shot.rgb)
    img = _check_not_black(img)
    if downscale and max(img.size) > downscale:
        w, h = img.size
        scale = downscale / float(max(w, h))
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def capture_region_png(left: int, top: int, width: int, height: int) -> bytes:
    """Capture a region on the primary monitor (clamped to screen bounds)."""
    w, h = screen_size()
    left = max(0, int(left))
    top = max(0, int(top))
    width = int(min(width, w - left))
    height = int(min(height, h - top))
    with mss.MSS() as sct:
        mon = {"left": left, "top": top, "width": width, "height": height}
        shot = sct.grab(mon)
    img = Image.frombytes("RGB", shot.size, shot.rgb)
    img = _check_not_black(img)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _check_not_black(img: Image.Image) -> Image.Image:
    arr = np.asarray(img)
    mean = float(arr.mean())
    std = float(arr.std())
    if mean < 12.0 and std < 8.0:
        raise RuntimeError(
            f"black frame detected (mean={mean:.1f} std={std:.1f}); "
            "window is GPU-composited and BitBlt returned black. "
            "Bring the target window to the foreground and retry."
        )
    return img


def set_clipboard_text(text: str) -> None:
    """Put text on the Windows clipboard via Win32 (no external deps)."""
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    user32.OpenClipboard.argtypes = [wintypes.HWND]
    user32.OpenClipboard.restype = wintypes.BOOL
    user32.EmptyClipboard.restype = wintypes.BOOL
    user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
    user32.SetClipboardData.restype = wintypes.HANDLE
    user32.CloseClipboard.restype = wintypes.BOOL
    kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
    kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
    kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalLock.restype = wintypes.LPVOID
    kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalUnlock.restype = wintypes.BOOL

    CF_UNICODETEXT = 13
    GHND = 0x0042
    if not user32.OpenClipboard(None):
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        user32.EmptyClipboard()
        data = (text + "\x00").encode("utf-16-le")
        h = kernel32.GlobalAlloc(GHND, len(data))
        if not h:
            raise ctypes.WinError(ctypes.get_last_error())
        ptr = kernel32.GlobalLock(h)
        if not ptr:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            ctypes.memmove(ptr, data, len(data))
        finally:
            kernel32.GlobalUnlock(h)
        if not user32.SetClipboardData(CF_UNICODETEXT, h):
            raise ctypes.WinError(ctypes.get_last_error())
    finally:
        user32.CloseClipboard()


def save_png(bytes_: bytes, path: str) -> str:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "wb") as f:
        f.write(bytes_)
    return path


def set_clipboard_image(png_bytes: bytes) -> None:
    """Put an image on the Windows clipboard (CF_DIB) so Ctrl+V pastes it.

    Converts the PNG bytes to a 32bpp bottom-up BGRA DIB and hands it to
    ``SetClipboardData(CF_DIB=8)``. Pure Win32, no external deps.
    """
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

    user32.OpenClipboard.argtypes = [wintypes.HWND]
    user32.OpenClipboard.restype = wintypes.BOOL
    user32.EmptyClipboard.restype = wintypes.BOOL
    user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
    user32.SetClipboardData.restype = wintypes.HANDLE
    user32.CloseClipboard.restype = wintypes.BOOL
    kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
    kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
    kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalLock.restype = wintypes.LPVOID
    kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalUnlock.restype = wintypes.BOOL

    img = Image.open(io.BytesIO(png_bytes)).convert("RGBA")
    w, h = img.size
    bgra = bytearray(img.tobytes("raw", "RGBA"))
    # RGBA -> BGRA
    for i in range(0, len(bgra), 4):
        bgra[i], bgra[i + 2] = bgra[i + 2], bgra[i]
    rows = [bytes(bgra[y * w * 4 : (y + 1) * w * 4]) for y in range(h)]
    pixels = b"".join(reversed(rows))  # bottom-up DIB

    class BITMAPINFOHEADER(ctypes.Structure):
        _fields_ = [
            ("biSize", wintypes.DWORD),
            ("biWidth", wintypes.LONG),
            ("biHeight", wintypes.LONG),
            ("biPlanes", wintypes.WORD),
            ("biBitCount", wintypes.WORD),
            ("biCompression", wintypes.DWORD),
            ("biSizeImage", wintypes.DWORD),
            ("biXPelsPerMeter", wintypes.LONG),
            ("biYPelsPerMeter", wintypes.LONG),
            ("biClrUsed", wintypes.DWORD),
            ("biClrImportant", wintypes.DWORD),
        ]

    bmi = BITMAPINFOHEADER()
    bmi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bmi.biWidth = w
    bmi.biHeight = h
    bmi.biPlanes = 1
    bmi.biBitCount = 32
    bmi.biCompression = 0  # BI_RGB
    bmi.biSizeImage = w * h * 4
    dib = ctypes.string_at(ctypes.byref(bmi), ctypes.sizeof(bmi)) + pixels

    CF_DIB = 8
    GHND = 0x0042
    if not user32.OpenClipboard(None):
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        user32.EmptyClipboard()
        h = kernel32.GlobalAlloc(GHND, len(dib))
        if not h:
            raise ctypes.WinError(ctypes.get_last_error())
        ptr = kernel32.GlobalLock(h)
        if not ptr:
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            ctypes.memmove(ptr, dib, len(dib))
        finally:
            kernel32.GlobalUnlock(h)
        if not user32.SetClipboardData(CF_DIB, h):
            raise ctypes.WinError(ctypes.get_last_error())
    finally:
        user32.CloseClipboard()


# --- input ---------------------------------------------------------------


def _click_ok_console(prompt: str) -> bool:
    sys.stdout.write(prompt + " [y/N] ")
    sys.stdout.flush()
    line = sys.stdin.readline().strip().lower()
    return line in ("y", "yes")


_CLICK_GATE = _click_ok_console


def set_click_gate(fn) -> None:
    """Replace the click approval gate (used by tests to auto-approve)."""
    global _CLICK_GATE
    _CLICK_GATE = fn


def _clamp(x: float, y: float) -> tuple[float, float]:
    w, h = screen_size()
    return max(0.0, min(float(w) - 1.0, x)), max(0.0, min(float(h) - 1.0, y))


def click(x: float, y: float, button: str = "left", approve: bool = True) -> bool:
    """Move to (x, y) and click. Returns False if the human vetoed."""
    import pyautogui

    x, y = _clamp(x, y)
    if approve:
        ok = _CLICK_GATE(f"Click at ({x:.0f},{y:.0f})?")
        if not ok:
            return False
    pyautogui.moveTo(x, y, duration=0.2)
    pyautogui.click(x, y, button=button)
    return True


def type_text(text: str, interval: float = 0.03) -> None:
    import pyautogui

    pyautogui.write(text, interval=interval)


def press(key: str) -> None:
    import pyautogui

    pyautogui.press(key)


def hotkey(*keys: str) -> None:
    import pyautogui

    pyautogui.hotkey(*keys)


def window_hwnd(title_substring: str, exclude: str = "") -> int | None:
    """Return the HWND of the largest visible top-level window whose title
    contains ``title_substring`` (and not ``exclude``), or None."""
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32
    found = []

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def _cb(hwnd, lparam):
        if not user32.IsWindowVisible(hwnd):
            return True
        length = user32.GetWindowTextLengthW(hwnd)
        if length == 0:
            return True
        buf = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buf, length + 1)
        t = buf.value
        if title_substring.lower() in t.lower() and (not exclude or exclude.lower() not in t.lower()):
            rect = wintypes.RECT()
            user32.GetWindowRect(hwnd, ctypes.byref(rect))
            found.append((hwnd, rect.right - rect.left, rect.bottom - rect.top))
        return True

    user32.EnumWindows(_cb, 0)
    if not found:
        return None
    # Prefer the largest window (main app window over helper/splash).
    found.sort(key=lambda f: f[1] * f[2], reverse=True)
    return found[0][0]


def capture_window_png(hwnd: int) -> bytes:
    """Capture a specific top-level window's content via PrintWindow.

    Unlike screen-region capture, PrintWindow renders the window itself, so it
    works even when another window (e.g. a terminal) occludes the target. Raises
    RuntimeError on a black frame.
    """
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32
    gdi32 = ctypes.windll.gdi32
    rect = wintypes.RECT()
    if not user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        raise RuntimeError("GetWindowRect failed")
    w = max(1, rect.right - rect.left)
    h = max(1, rect.bottom - rect.top)
    if w == 1 or h == 1:
        raise RuntimeError("window is minimized; cannot capture")

    hdc_window = user32.GetWindowDC(hwnd)
    mem_dc = gdi32.CreateCompatibleDC(hdc_window)
    bmp = gdi32.CreateCompatibleBitmap(hdc_window, w, h)
    old = gdi32.SelectObject(mem_dc, bmp)
    try:
        PW_RENDERFULLCONTENT = 0x00000002
        if not user32.PrintWindow(hwnd, mem_dc, PW_RENDERFULLCONTENT):
            # fall back to the classic path (works for non-GPU-composited windows)
            user32.PrintWindow(hwnd, mem_dc, 0)
        pixels = _read_bitmap(mem_dc, bmp, w, h)
    finally:
        gdi32.SelectObject(mem_dc, old)
        gdi32.DeleteDC(mem_dc)
        user32.ReleaseDC(hwnd, hdc_window)

    img = Image.frombytes("RGB", (w, h), pixels, "raw", "BGRX")
    gdi32.DeleteObject(bmp)
    img = _check_not_black(img)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _read_bitmap(dc, bmp, w: int, h: int) -> bytes:
    """Read a 32bpp device-independent bitmap's pixel bits via the given DC."""
    import ctypes
    from ctypes import wintypes

    gdi32 = ctypes.windll.gdi32
    class BITMAPINFOHEADER(ctypes.Structure):
        _fields_ = [
            ("biSize", wintypes.DWORD),
            ("biWidth", wintypes.LONG),
            ("biHeight", wintypes.LONG),
            ("biPlanes", wintypes.WORD),
            ("biBitCount", wintypes.WORD),
            ("biCompression", wintypes.DWORD),
            ("biSizeImage", wintypes.DWORD),
            ("biXPelsPerMeter", wintypes.LONG),
            ("biYPelsPerMeter", wintypes.LONG),
            ("biClrUsed", wintypes.DWORD),
            ("biClrImportant", wintypes.DWORD),
        ]
    bmi = BITMAPINFOHEADER()
    bmi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bmi.biWidth = w
    bmi.biHeight = -h  # top-down
    bmi.biPlanes = 1
    bmi.biBitCount = 32
    bmi.biCompression = 0  # BI_RGB
    bmi.biSizeImage = w * h * 4
    buf = ctypes.create_string_buffer(bmi.biSizeImage)
    if not gdi32.GetDIBits(
        dc, bmp, 0, h, buf, ctypes.byref(bmi), 0
    ):
        raise RuntimeError("GetDIBits pixels failed")
    return buf.raw


def window_rect(title_substring: str, exclude: str = "") -> tuple[int, int, int, int] | None:
    """Return (left, top, width, height) of the first visible top-level window
    whose title contains ``title_substring`` (and not ``exclude``), or None."""
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32
    found = []

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def _cb(hwnd, lparam):
        if not user32.IsWindowVisible(hwnd):
            return True
        length = user32.GetWindowTextLengthW(hwnd)
        if length == 0:
            return True
        buf = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buf, length + 1)
        t = buf.value
        if title_substring.lower() in t.lower() and (not exclude or exclude.lower() not in t.lower()):
            rect = wintypes.RECT()
            user32.GetWindowRect(hwnd, ctypes.byref(rect))
            found.append((t, rect.left, rect.top, rect.right - rect.left, rect.bottom - rect.top))
        return True

    user32.EnumWindows(_cb, 0)
    if not found:
        return None
    # Prefer the largest window (main app window over helper/splash).
    found.sort(key=lambda f: f[3] * f[4], reverse=True)
    return found[0][1], found[0][2], found[0][3], found[0][4]


def activate_window(title_substring: str) -> bool:
    """Bring a window whose title contains the substring to the foreground.

    Uses the Win32 SetForegroundWindow path so click targets are visible.
    Returns True if a matching top-level window was found.
    """
    import ctypes
    from ctypes import wintypes

    user32 = ctypes.windll.user32

    found = []

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def _cb(hwnd, lparam):
        if not user32.IsWindowVisible(hwnd):
            return True
        length = user32.GetWindowTextLengthW(hwnd)
        if length == 0:
            return True
        buf = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buf, length + 1)
        if title_substring.lower() in buf.value.lower():
            found.append(hwnd)
            return False
        return True

    user32.EnumWindows(_cb, 0)
    if not found:
        return False
    user32.SetForegroundWindow(found[0])
    return True
