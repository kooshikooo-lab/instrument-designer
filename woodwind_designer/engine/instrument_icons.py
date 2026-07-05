"""
SVG instrument silhouettes rendered as QPixmap icons.
Each type_label maps to a distinct stylized vector drawing.
"""

from PySide6.QtGui import QPixmap, QPainter, QColor
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtCore import QByteArray, Qt
from io import BytesIO


# Each SVG is a viewBox="0 0 120 80" silhouette on transparent bg

_FLUTE_SVG = b"""<svg viewBox="0 0 120 80" xmlns="http://www.w3.org/2000/svg">
  <defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0%" stop-color="#C99B5C"/><stop offset="100%" stop-color="#8B5E3C"/>
  </linearGradient></defs>
  <rect x="8" y="28" rx="6" ry="6" width="104" height="16" fill="url(#g)" stroke="#D4A76A" stroke-width="1"/>
  <rect x="8" y="24" rx="3" ry="3" width="20" height="24" fill="#2a1f10" stroke="#D4A76A" stroke-width="1"/>
  <circle cx="40" cy="36" r="2.5" fill="#1a1a1a" stroke="#D4A76A" stroke-width="0.8"/>
  <circle cx="52" cy="36" r="2.5" fill="#1a1a1a" stroke="#D4A76A" stroke-width="0.8"/>
  <circle cx="64" cy="36" r="2.5" fill="#1a1a1a" stroke="#D4A76A" stroke-width="0.8"/>
  <circle cx="76" cy="36" r="2.5" fill="#1a1a1a" stroke="#D4A76A" stroke-width="0.8"/>
  <circle cx="88" cy="36" r="2.5" fill="#1a1a1a" stroke="#D4A76A" stroke-width="0.8"/>
  <rect x="100" y="30" rx="2" ry="2" width="12" height="4" fill="#6B4E2C"/>
  <rect x="100" y="38" rx="2" ry="2" width="12" height="4" fill="#6B4E2C"/>
</svg>"""

_SINGLE_REED_SVG = b"""<svg viewBox="0 0 120 80" xmlns="http://www.w3.org/2000/svg">
  <defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0%" stop-color="#C99B5C"/><stop offset="100%" stop-color="#8B5E3C"/>
  </linearGradient></defs>
  <rect x="10" y="26" rx="4" ry="4" width="100" height="18" fill="url(#g)" stroke="#D4A76A" stroke-width="1"/>
  <rect x="8" y="22" rx="2" ry="2" width="14" height="26" fill="#2a1f10" stroke="#D4A76A" stroke-width="1"/>
  <polygon points="8,22 15,12 22,22" fill="#2a1f10" stroke="#D4A76A" stroke-width="1"/>
  <circle cx="38" cy="35" r="2.5" fill="#1a1a1a" stroke="#D4A76A" stroke-width="0.8"/>
  <circle cx="50" cy="35" r="2.5" fill="#1a1a1a" stroke="#D4A76A" stroke-width="0.8"/>
  <circle cx="62" cy="35" r="2.5" fill="#1a1a1a" stroke="#D4A76A" stroke-width="0.8"/>
  <circle cx="74" cy="35" r="2.5" fill="#1a1a1a" stroke="#D4A76A" stroke-width="0.8"/>
  <circle cx="86" cy="35" r="2.5" fill="#1a1a1a" stroke="#D4A76A" stroke-width="0.8"/>
  <rect x="96" y="28" rx="4" ry="4" width="14" height="14" fill="#6B4E2C" stroke="#D4A76A" stroke-width="0.8"/>
  <ellipse cx="103" cy="35" rx="3" ry="5" fill="#1a1a1a"/>
</svg>"""

_DOUBLE_REED_SVG = b"""<svg viewBox="0 0 120 80" xmlns="http://www.w3.org/2000/svg">
  <defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0%" stop-color="#C99B5C"/><stop offset="100%" stop-color="#8B5E3C"/>
  </linearGradient></defs>
  <rect x="10" y="26" rx="4" ry="4" width="98" height="18" fill="url(#g)" stroke="#D4A76A" stroke-width="1"/>
  <path d="M8 30 Q4 26 2 30 Q4 34 8 34" fill="#2a1f10" stroke="#D4A76A" stroke-width="1"/>
  <path d="M8 36 Q4 39 2 36 Q4 32 8 36" fill="#2a1f10" stroke="#D4A76A" stroke-width="1"/>
  <ellipse cx="6" cy="35" rx="3" ry="8" fill="#2a1f10" stroke="#D4A76A" stroke-width="0.8"/>
  <path d="M65 26 L65 44" stroke="#6B4E2C" stroke-width="2"/>
  <circle cx="34" cy="35" r="2.5" fill="#1a1a1a" stroke="#D4A76A" stroke-width="0.8"/>
  <circle cx="44" cy="35" r="2.5" fill="#1a1a1a" stroke="#D4A76A" stroke-width="0.8"/>
  <circle cx="54" cy="35" r="2.5" fill="#1a1a1a" stroke="#D4A76A" stroke-width="0.8"/>
  <circle cx="76" cy="33" r="1.8" fill="#1a1a1a" stroke="#D4A76A" stroke-width="0.8"/>
  <circle cx="86" cy="31" r="1.8" fill="#1a1a1a" stroke="#D4A76A" stroke-width="0.8"/>
  <circle cx="96" cy="29" r="1.8" fill="#1a1a1a" stroke="#D4A76A" stroke-width="0.8"/>
  <rect x="98" y="28" rx="8" ry="4" width="12" height="14" fill="#6B4E2C" stroke="#D4A76A" stroke-width="0.8"/>
</svg>"""

_SLIT_REED_SVG = b"""<svg viewBox="0 0 120 80" xmlns="http://www.w3.org/2000/svg">
  <defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0%" stop-color="#C99B5C"/><stop offset="100%" stop-color="#8B5E3C"/>
  </linearGradient></defs>
  <rect x="10" y="24" rx="4" ry="4" width="100" height="20" fill="url(#g)" stroke="#D4A76A" stroke-width="1"/>
  <polygon points="10,24 10,44 6,44 3,34 6,24" fill="#2a1f10" stroke="#D4A76A" stroke-width="1"/>
  <rect x="18" y="30" rx="1" ry="1" width="60" height="8" fill="#1a1a1a" stroke="#C99B5C" stroke-width="0.8"/>
  <line x1="18" y1="34" x2="78" y2="34" stroke="#C99B5C" stroke-width="0.5"/>
  <circle cx="86" cy="34" r="2" fill="#1a1a1a" stroke="#D4A76A" stroke-width="0.8"/>
  <circle cx="96" cy="34" r="2" fill="#1a1a1a" stroke="#D4A76A" stroke-width="0.8"/>
  <rect x="100" y="28" rx="3" ry="3" width="10" height="12" fill="#6B4E2C" stroke="#D4A76A" stroke-width="0.8"/>
</svg>"""

_GENERIC_SVG = b"""<svg viewBox="0 0 120 80" xmlns="http://www.w3.org/2000/svg">
  <defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0%" stop-color="#C99B5C"/><stop offset="100%" stop-color="#8B5E3C"/>
  </linearGradient></defs>
  <rect x="20" y="20" rx="6" ry="6" width="80" height="30" fill="url(#g)" stroke="#D4A76A" stroke-width="1"/>
  <text x="60" y="42" text-anchor="middle" fill="#1a1a1a" font-size="8" font-family="sans-serif">INSTRUMENT</text>
</svg>"""


_PAN_FLUTE_SVG = b"""<svg viewBox="0 0 120 80" xmlns="http://www.w3.org/2000/svg">
  <defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0%" stop-color="#C99B5C"/><stop offset="100%" stop-color="#8B5E3C"/>
  </linearGradient></defs>
  <rect x="20" y="10" rx="2" ry="2" width="6" height="50" fill="url(#g)" stroke="#D4A76A" stroke-width="0.8"/>
  <rect x="30" y="12" rx="2" ry="2" width="6" height="48" fill="url(#g)" stroke="#D4A76A" stroke-width="0.8"/>
  <rect x="40" y="15" rx="2" ry="2" width="6" height="45" fill="url(#g)" stroke="#D4A76A" stroke-width="0.8"/>
  <rect x="50" y="18" rx="2" ry="2" width="6" height="42" fill="url(#g)" stroke="#D4A76A" stroke-width="0.8"/>
  <rect x="60" y="22" rx="2" ry="2" width="6" height="38" fill="url(#g)" stroke="#D4A76A" stroke-width="0.8"/>
  <rect x="70" y="26" rx="2" ry="2" width="6" height="34" fill="url(#g)" stroke="#D4A76A" stroke-width="0.8"/>
  <rect x="80" y="30" rx="2" ry="2" width="6" height="30" fill="url(#g)" stroke="#D4A76A" stroke-width="0.8"/>
  <rect x="90" y="35" rx="2" ry="2" width="6" height="25" fill="url(#g)" stroke="#D4A76A" stroke-width="0.8"/>
  <line x1="18" y1="62" x2="98" y2="62" stroke="#6B4E2C" stroke-width="1.5"/>
</svg>"""

_BRASS_SVG = b"""<svg viewBox="0 0 120 80" xmlns="http://www.w3.org/2000/svg">
  <defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0%" stop-color="#E8B84B"/><stop offset="100%" stop-color="#B8860B"/>
  </linearGradient></defs>
  <rect x="10" y="30" rx="4" ry="4" width="70" height="12" fill="url(#g)" stroke="#DAA520" stroke-width="1"/>
  <rect x="10" y="26" rx="2" ry="2" width="12" height="20" fill="#2a1f10" stroke="#D4A76A" stroke-width="1"/>
  <circle cx="20" cy="36" r="2" fill="#1a1a1a" stroke="#D4A76A" stroke-width="0.6"/>
  <circle cx="28" cy="36" r="2" fill="#1a1a1a" stroke="#D4A76A" stroke-width="0.6"/>
  <circle cx="36" cy="36" r="2" fill="#1a1a1a" stroke="#D4A76A" stroke-width="0.6"/>
  <path d="M80 30 Q100 20 118 25 Q110 36 80 42" fill="url(#g)" stroke="#DAA520" stroke-width="1"/>
  <rect x="80" y="30" rx="2" ry="2" width="8" height="12" fill="#6B4E2C"/>
</svg>"""

_TRANSVERSE_FLUTE_SVG = b"""<svg viewBox="0 0 120 80" xmlns="http://www.w3.org/2000/svg">
  <defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0%" stop-color="#C99B5C"/><stop offset="100%" stop-color="#8B5E3C"/>
  </linearGradient></defs>
  <rect x="8" y="34" rx="4" ry="4" width="104" height="12" fill="url(#g)" stroke="#D4A76A" stroke-width="1"/>
  <ellipse cx="14" cy="34" rx="6" ry="4" fill="#2a1f10" stroke="#D4A76A" stroke-width="0.8"/>
  <circle cx="14" cy="34" r="2.5" fill="#1a1a1a"/>
  <circle cx="34" cy="40" r="2" fill="#1a1a1a" stroke="#D4A76A" stroke-width="0.8"/>
  <circle cx="46" cy="40" r="2" fill="#1a1a1a" stroke="#D4A76A" stroke-width="0.8"/>
  <circle cx="58" cy="40" r="2" fill="#1a1a1a" stroke="#D4A76A" stroke-width="0.8"/>
  <circle cx="70" cy="40" r="2" fill="#1a1a1a" stroke="#D4A76A" stroke-width="0.8"/>
  <circle cx="82" cy="40" r="2" fill="#1a1a1a" stroke="#D4A76A" stroke-width="0.8"/>
  <circle cx="94" cy="40" r="2" fill="#1a1a1a" stroke="#D4A76A" stroke-width="0.8"/>
  <rect x="106" y="32" rx="2" ry="2" width="6" height="16" fill="#6B4E2C"/>
  <line x1="14" y1="34" x2="14" y2="22" stroke="#6B4E2C" stroke-width="1.5"/>
</svg>"""

_VESSEL_FLUTE_SVG = b"""<svg viewBox="0 0 120 80" xmlns="http://www.w3.org/2000/svg">
  <defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0%" stop-color="#C99B5C"/><stop offset="100%" stop-color="#8B5E3C"/>
  </linearGradient></defs>
  <ellipse cx="55" cy="40" rx="35" ry="25" fill="url(#g)" stroke="#D4A76A" stroke-width="1.5"/>
  <rect x="18" y="35" rx="3" ry="3" width="18" height="10" fill="#2a1f10" stroke="#D4A76A" stroke-width="0.8"/>
  <circle cx="40" cy="32" r="1.8" fill="#1a1a1a" stroke="#D4A76A" stroke-width="0.6"/>
  <circle cx="40" cy="42" r="1.8" fill="#1a1a1a" stroke="#D4A76A" stroke-width="0.6"/>
  <circle cx="50" cy="28" r="1.8" fill="#1a1a1a" stroke="#D4A76A" stroke-width="0.6"/>
  <circle cx="50" cy="52" r="1.8" fill="#1a1a1a" stroke="#D4A76A" stroke-width="0.6"/>
  <circle cx="60" cy="32" r="1.8" fill="#1a1a1a" stroke="#D4A76A" stroke-width="0.6"/>
  <circle cx="60" cy="48" r="1.8" fill="#1a1a1a" stroke="#D4A76A" stroke-width="0.6"/>
  <circle cx="70" cy="40" r="1.8" fill="#1a1a1a" stroke="#D4A76A" stroke-width="0.6"/>
  <circle cx="80" cy="28" r="1.5" fill="#1a1a1a" stroke="#D4A76A" stroke-width="0.6"/>
  <circle cx="80" cy="52" r="1.5" fill="#1a1a1a" stroke="#D4A76A" stroke-width="0.6"/>
  <ellipse cx="55" cy="65" rx="15" ry="3" fill="#6B4E2C" stroke="#D4A76A" stroke-width="0.6"/>
</svg>"""

_SLIDE_WHISTLE_SVG = b"""<svg viewBox="0 0 120 80" xmlns="http://www.w3.org/2000/svg">
  <defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0%" stop-color="#C99B5C"/><stop offset="100%" stop-color="#8B5E3C"/>
  </linearGradient></defs>
  <rect x="10" y="30" rx="4" ry="4" width="100" height="14" fill="url(#g)" stroke="#D4A76A" stroke-width="1"/>
  <rect x="8" y="26" rx="2" ry="2" width="12" height="22" fill="#2a1f10" stroke="#D4A76A" stroke-width="1"/>
  <rect x="40" y="28" rx="3" ry="3" width="50" height="18" fill="#3a3a3a" stroke="#D4A76A" stroke-width="1" stroke-dasharray="3,2"/>
  <rect x="85" y="26" rx="3" ry="3" width="14" height="22" fill="#8B5E3C" stroke="#D4A76A" stroke-width="1"/>
  <circle cx="28" cy="37" r="2" fill="#1a1a1a" stroke="#D4A76A" stroke-width="0.6"/>
  <circle cx="36" cy="37" r="2" fill="#1a1a1a" stroke="#D4A76A" stroke-width="0.6"/>
  <line x1="40" y1="37" x2="85" y2="37" stroke="#C99B5C" stroke-width="0.5"/>
</svg>"""

_DRONE_SVG = b"""<svg viewBox="0 0 120 80" xmlns="http://www.w3.org/2000/svg">
  <defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0%" stop-color="#C99B5C"/><stop offset="100%" stop-color="#8B5E3C"/>
  </linearGradient></defs>
  <rect x="8" y="28" rx="8" ry="8" width="104" height="16" fill="url(#g)" stroke="#D4A76A" stroke-width="1"/>
  <rect x="8" y="22" rx="3" ry="3" width="18" height="28" fill="#2a1f10" stroke="#D4A76A" stroke-width="1"/>
  <rect x="50" y="24" rx="2" ry="2" width="30" height="24" fill="#3a3a3a" stroke="#D4A76A" stroke-width="0.8" stroke-dasharray="4,2"/>
  <ellipse cx="110" cy="36" rx="6" ry="10" fill="url(#g)" stroke="#D4A76A" stroke-width="1"/>
  <path d="M26 32 Q28 24 34 24 L50 24 L50 44 L34 44 Q28 44 26 36" fill="none" stroke="#6B4E2C" stroke-width="0.8"/>
</svg>"""

_FREE_REED_SVG = b"""<svg viewBox="0 0 120 80" xmlns="http://www.w3.org/2000/svg">
  <defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0%" stop-color="#C99B5C"/><stop offset="100%" stop-color="#8B5E3C"/>
  </linearGradient></defs>
  <rect x="20" y="24" rx="6" ry="6" width="80" height="26" fill="url(#g)" stroke="#D4A76A" stroke-width="1"/>
  <rect x="35" y="26" rx="2" ry="2" width="50" height="22" fill="#1a1a1a" stroke="#D4A76A" stroke-width="0.8"/>
  <rect x="30" y="32" rx="1" ry="1" width="8" height="10" fill="#C99B5C"/>
  <rect x="82" y="32" rx="1" ry="1" width="8" height="10" fill="#C99B5C"/>
  <line x1="42" y1="37" x2="78" y2="37" stroke="#D4A76A" stroke-width="0.8"/>
  <circle cx="60" cy="37" r="3" fill="#2a1f10" stroke="#D4A76A" stroke-width="0.6"/>
</svg>"""

_MOUTHPIECE_SVG = b"""<svg viewBox="0 0 120 80" xmlns="http://www.w3.org/2000/svg">
  <defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0%" stop-color="#C99B5C"/><stop offset="100%" stop-color="#8B5E3C"/>
  </linearGradient></defs>
  <rect x="20" y="22" rx="6" ry="6" width="40" height="14" fill="url(#g)" stroke="#D4A76A" stroke-width="1"/>
  <rect x="16" y="24" rx="2" ry="2" width="12" height="10" fill="#2a1f10" stroke="#D4A76A" stroke-width="0.8"/>
  <path d="M60 24 Q72 18 85 20 Q90 22 90 28 Q90 34 85 36 Q72 38 60 32" fill="url(#g)" stroke="#D4A76A" stroke-width="1"/>
  <rect x="90" y="26" rx="2" ry="2" width="14" height="4" fill="#6B4E2C"/>
  <rect x="90" y="32" rx="2" ry="2" width="14" height="4" fill="#6B4E2C"/>
  <polygon points="16,24 12,20 20,20" fill="#2a1f10" stroke="#D4A76A" stroke-width="0.6"/>
</svg>"""

_BARREL_SVG = b"""<svg viewBox="0 0 120 80" xmlns="http://www.w3.org/2000/svg">
  <defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0%" stop-color="#C99B5C"/><stop offset="100%" stop-color="#8B5E3C"/>
  </linearGradient></defs>
  <rect x="50" y="20" rx="4" ry="4" width="20" height="40" fill="url(#g)" stroke="#D4A76A" stroke-width="1"/>
  <rect x="48" y="18" rx="2" ry="2" width="24" height="6" fill="#6B4E2C" stroke="#D4A76A" stroke-width="0.6"/>
  <rect x="48" y="56" rx="2" ry="2" width="24" height="6" fill="#6B4E2C" stroke="#D4A76A" stroke-width="0.6"/>
  <circle cx="55" cy="28" r="1.5" fill="#1a1a1a"/>
  <circle cx="65" cy="28" r="1.5" fill="#1a1a1a"/>
  <circle cx="55" cy="40" r="1.5" fill="#1a1a1a"/>
  <circle cx="65" cy="40" r="1.5" fill="#1a1a1a"/>
  <circle cx="55" cy="52" r="1.5" fill="#1a1a1a"/>
  <circle cx="65" cy="52" r="1.5" fill="#1a1a1a"/>
</svg>"""

_REED_ICON_SVG = b"""<svg viewBox="0 0 120 80" xmlns="http://www.w3.org/2000/svg">
  <defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0%" stop-color="#E8C88A"/><stop offset="100%" stop-color="#A0713A"/>
  </linearGradient></defs>
  <rect x="54" y="8" rx="2" ry="2" width="12" height="64" fill="url(#g)" stroke="#D4A76A" stroke-width="1"/>
  <path d="M54 8 Q48 20 48 30 Q48 40 54 50" fill="url(#g)" stroke="#D4A76A" stroke-width="1" stroke-linecap="round"/>
  <rect x="48" y="50" rx="2" ry="2" width="24" height="6" fill="#6B4E2C" stroke="#D4A76A" stroke-width="0.6"/>
  <line x1="60" y1="8" x2="60" y2="72" stroke="#8B5E3C" stroke-width="0.5"/>
</svg>"""

_LIGATURE_SVG = b"""<svg viewBox="0 0 120 80" xmlns="http://www.w3.org/2000/svg">
  <defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0%" stop-color="#C99B5C"/><stop offset="100%" stop-color="#8B5E3C"/>
  </linearGradient></defs>
  <rect x="20" y="28" rx="6" ry="6" width="80" height="16" fill="url(#g)" stroke="#D4A76A" stroke-width="1"/>
  <rect x="24" y="32" rx="2" ry="2" width="72" height="8" fill="#1a1a1a" stroke="#D4A76A" stroke-width="0.6"/>
  <rect x="30" y="26" rx="2" ry="2" width="60" height="4" fill="#6B4E2C"/>
  <rect x="30" y="42" rx="2" ry="2" width="60" height="4" fill="#6B4E2C"/>
  <circle cx="26" cy="36" r="2" fill="#2a1f10" stroke="#D4A76A" stroke-width="0.6"/>
  <circle cx="94" cy="36" r="2" fill="#2a1f10" stroke="#D4A76A" stroke-width="0.6"/>
</svg>"""

_TOOL_SVG = b"""<svg viewBox="0 0 120 80" xmlns="http://www.w3.org/2000/svg">
  <defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0%" stop-color="#C99B5C"/><stop offset="100%" stop-color="#8B5E3C"/>
  </linearGradient></defs>
  <rect x="30" y="16" rx="3" ry="3" width="60" height="8" fill="url(#g)" stroke="#D4A76A" stroke-width="1"/>
  <rect x="36" y="24" rx="2" ry="2" width="8" height="40" fill="url(#g)" stroke="#D4A76A" stroke-width="1"/>
  <rect x="76" y="24" rx="2" ry="2" width="8" height="40" fill="url(#g)" stroke="#D4A76A" stroke-width="1"/>
  <rect x="36" y="24" rx="2" ry="2" width="48" height="8" fill="#6B4E2C" stroke="#D4A76A" stroke-width="0.6"/>
  <rect x="42" y="34" rx="2" ry="2" width="36" height="6" fill="#3a3a3a" stroke="#D4A76A" stroke-width="0.6"/>
  <rect x="44" y="44" rx="2" ry="2" width="32" height="6" fill="#3a3a3a" stroke="#D4A76A" stroke-width="0.6"/>
  <rect x="50" y="56" rx="2" ry="2" width="20" height="4" fill="#3a3a3a" stroke="#D4A76A" stroke-width="0.6"/>
</svg>"""


_ICON_MAP = {
    "Fipple Flute": _FLUTE_SVG,
    "Single Reed": _SINGLE_REED_SVG,
    "Double Reed": _DOUBLE_REED_SVG,
    "Single Reed + Slit": _SLIT_REED_SVG,
    "Pan Flute": _PAN_FLUTE_SVG,
    "Brass": _BRASS_SVG,
    "Transverse Flute": _TRANSVERSE_FLUTE_SVG,
    "Vessel Flute": _VESSEL_FLUTE_SVG,
    "Slide Whistle": _SLIDE_WHISTLE_SVG,
    "Drone": _DRONE_SVG,
    "Free Reed": _FREE_REED_SVG,
    "Mouthpiece": _MOUTHPIECE_SVG,
    "Barrel": _BARREL_SVG,
    "Reed": _REED_ICON_SVG,
    "Ligature": _LIGATURE_SVG,
    "Tool": _TOOL_SVG,
}


def get_svg_bytes(type_label: str) -> bytes:
    return _ICON_MAP.get(type_label, _GENERIC_SVG)


def render_icon(type_label: str, width: int = 60, height: int = 40) -> QPixmap:
    svg_data = get_svg_bytes(type_label)
    renderer = QSvgRenderer(QByteArray(svg_data))
    pixmap = QPixmap(width, height)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return pixmap


def render_large(type_label: str, width: int = 240, height: int = 160) -> QPixmap:
    svg_data = get_svg_bytes(type_label)
    renderer = QSvgRenderer(QByteArray(svg_data))
    pixmap = QPixmap(width, height)
    pixmap.fill(QColor("#1e1e1e"))
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return pixmap
