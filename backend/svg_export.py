"""
svg_export.py — Generate SVG from bore profile data.

Produces two views:
1. Cross-section: axial view showing bore taper with hole positions
2. Side profile: bore diameter along length with annotations

Usage:
    from backend.svg_export import bore_to_svg
    svg = bore_to_svg(bore_profile, hole_positions, hole_diameters, title="My Instrument")
"""

from typing import Optional


def bore_to_svg(
    bore_profile: list[list[float]],
    title: str = "Instrument Bore Profile",
    hole_positions: Optional[list[float]] = None,
    hole_diameters: Optional[list[float]] = None,
    bore_length: Optional[float] = None,
    svg_width: int = 800,
    svg_height: int = 500,
) -> str:
    """Generate SVG string from bore profile.

    Args:
        bore_profile: List of [position_m, radius_m] pairs
        title: Title text for the SVG
        hole_positions: List of hole center positions along bore (meters)
        hole_diameters: List of hole diameters (meters)
        bore_length: Total bore length override (meters)
    Returns:
        SVG string
    """
    if not bore_profile or len(bore_profile) < 2:
        return _empty_svg("No bore profile data")

    positions = [p[0] for p in bore_profile]
    radii = [p[1] for p in bore_profile]

    if bore_length is None:
        bore_length = max(positions) if positions[-1] > 0 else 1.0

    max_radius = max(radii) if radii else 0.01
    min_radius = min(radii) if radii else 0.005

    margin_l, margin_r, margin_t, margin_b = 80, 40, 60, 80
    plot_w = svg_width - margin_l - margin_r
    plot_h = svg_height - margin_t - margin_b

    scale_x = plot_w / bore_length if bore_length > 0 else 1.0
    scale_y = plot_h / (max_radius * 2.2) if max_radius > 0 else 1.0

    def to_svg_x(pos_m):
        return margin_l + pos_m * scale_x

    def to_svg_y_top(radius_m):
        return margin_t + plot_h / 2 - radius_m * scale_y

    def to_svg_y_bot(radius_m):
        return margin_t + plot_h / 2 + radius_m * scale_y

    svg_lines = []
    svg_lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{svg_width}" height="{svg_height}" viewBox="0 0 {svg_width} {svg_height}">')
    svg_lines.append(f'<rect width="100%" height="100%" fill="#1a1a2e"/>')

    svg_lines.append(f'<text x="{svg_width/2}" y="30" text-anchor="middle" fill="#e0e0e0" font-family="monospace" font-size="16" font-weight="bold">{title}</text>')

    top_pts = []
    bot_pts = []
    for i, (pos, r) in enumerate(bore_profile):
        sx = to_svg_x(pos)
        top_pts.append(f"{sx:.1f},{to_svg_y_top(r):.1f}")
        bot_pts.append(f"{sx:.1f},{to_svg_y_bot(r):.1f}")

    bot_pts.reverse()
    all_pts = top_pts + bot_pts

    svg_lines.append(f'<polygon points="{" ".join(all_pts)}" fill="#16213e" stroke="#0f3460" stroke-width="1.5" opacity="0.9"/>')

    top_line = " ".join(top_pts)
    bot_line = " ".join(bot_pts)
    svg_lines.append(f'<polyline points="{top_line}" fill="none" stroke="#00d4ff" stroke-width="2"/>')
    svg_lines.append(f'<polyline points="{bot_line}" fill="none" stroke="#00d4ff" stroke-width="2"/>')

    if hole_positions and hole_diameters:
        for hp, hd in zip(hole_positions, hole_diameters):
            if hp <= bore_length:
                hx = to_svg_x(hp)
                hr = hd / 2 if hd else 0.002
                hole_vis_r = max(hr * scale_y, 3)
                svg_lines.append(f'<line x1="{hx:.1f}" y1="{margin_t + plot_h/2 - hole_vis_r:.1f}" x2="{hx:.1f}" y2="{margin_t + plot_h/2 + hole_vis_r:.1f}" stroke="#ff6b6b" stroke-width="2" stroke-dasharray="4,2"/>')
                svg_lines.append(f'<circle cx="{hx:.1f}" cy="{margin_t + plot_h/2:.1f}" r="{hole_vis_r:.1f}" fill="none" stroke="#ff6b6b" stroke-width="1.5" opacity="0.7"/>')
                svg_lines.append(f'<text x="{hx:.1f}" y="{margin_t + plot_h/2 + hole_vis_r + 14:.1f}" text-anchor="middle" fill="#ff6b6b" font-family="monospace" font-size="9">{hp*1000:.0f}mm</text>')

    svg_lines.append(f'<line x1="{margin_l}" y1="{margin_t + plot_h/2:.1f}" x2="{margin_l + plot_w}" y2="{margin_t + plot_h/2:.1f}" stroke="#333355" stroke-width="0.5" stroke-dasharray="5,5"/>')

    n_ticks = 8
    for i in range(n_ticks + 1):
        frac = i / n_ticks
        pos_m = frac * bore_length
        sx = to_svg_x(pos_m)
        svg_lines.append(f'<line x1="{sx:.1f}" y1="{margin_t + plot_h + 5:.1f}" x2="{sx:.1f}" y2="{margin_t + plot_h + 15:.1f}" stroke="#666" stroke-width="1"/>')
        svg_lines.append(f'<text x="{sx:.1f}" y="{margin_t + plot_h + 28:.1f}" text-anchor="middle" fill="#999" font-family="monospace" font-size="9">{pos_m*1000:.0f}</text>')

    svg_lines.append(f'<text x="{margin_l + plot_w/2}" y="{svg_height - 20:.0f}" text-anchor="middle" fill="#999" font-family="monospace" font-size="10">Position (mm)</text>')

    svg_lines.append(f'<text x="15" y="{margin_t + plot_h/2 - 5:.1f}" text-anchor="middle" fill="#00d4ff" font-family="monospace" font-size="9" transform="rotate(-90,15,{margin_t + plot_h/2:.1f})">Radius (mm)</text>')

    info_y = margin_t + 15
    svg_lines.append(f'<text x="{svg_width - margin_r - 5:.0f}" y="{info_y}" text-anchor="end" fill="#888" font-family="monospace" font-size="9">Length: {bore_length*1000:.0f}mm</text>')
    svg_lines.append(f'<text x="{svg_width - margin_r - 5:.0f}" y="{info_y + 14}" text-anchor="end" fill="#888" font-family="monospace" font-size="9">R_in: {min_radius*1000:.1f}mm  R_out: {max_radius*1000:.1f}mm</text>')
    if hole_positions:
        svg_lines.append(f'<text x="{svg_width - margin_r - 5:.0f}" y="{info_y + 28}" text-anchor="end" fill="#888" font-family="monospace" font-size="9">Holes: {len(hole_positions)}</text>')

    svg_lines.append("</svg>")
    return "\n".join(svg_lines)


def bore_to_cross_section_svg(
    bore_profile: list[list[float]],
    title: str = "Bore Cross-Section",
    hole_positions: Optional[list[float]] = None,
    svg_width: int = 600,
    svg_height: int = 400,
) -> str:
    """Generate axial cross-section SVG (looking down the bore)."""
    if not bore_profile or len(bore_profile) < 2:
        return _empty_svg("No bore profile data")

    cx = svg_width / 2
    cy = svg_height / 2
    max_pos = max(p[0] for p in bore_profile)
    max_r = max(p[1] for p in bore_profile)

    scale = min((svg_width - 100) / max_pos, (svg_height - 100) / (max_r * 2)) if max_pos > 0 and max_r > 0 else 1.0

    svg_lines = []
    svg_lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{svg_width}" height="{svg_height}" viewBox="0 0 {svg_width} {svg_height}">')
    svg_lines.append(f'<rect width="100%" height="100%" fill="#1a1a2e"/>')
    svg_lines.append(f'<text x="{cx}" y="25" text-anchor="middle" fill="#e0e0e0" font-family="monospace" font-size="14" font-weight="bold">{title}</text>')

    svg_lines.append(f'<line x1="50" y1="{cy}" x2="{svg_width-50}" y2="{cy}" stroke="#333355" stroke-width="0.5" stroke-dasharray="5,5"/>')

    top_pts = []
    bot_pts = []
    for pos, r in bore_profile:
        sx = 50 + pos * scale
        sy_top = cy - r * scale
        sy_bot = cy + r * scale
        top_pts.append(f"{sx:.1f},{sy_top:.1f}")
        bot_pts.append(f"{sx:.1f},{sy_bot:.1f}")

    svg_lines.append(f'<polyline points="{" ".join(top_pts)}" fill="none" stroke="#00d4ff" stroke-width="2"/>')
    svg_lines.append(f'<polyline points="{" ".join(bot_pts)}" fill="none" stroke="#00d4ff" stroke-width="2"/>')

    if hole_positions:
        for hp in hole_positions:
            if hp <= max_pos:
                hx = 50 + hp * scale
                svg_lines.append(f'<circle cx="{hx:.1f}" cy="{cy:.1f}" r="4" fill="#ff6b6b" opacity="0.8"/>')
                svg_lines.append(f'<text x="{hx:.1f}" y="{cy+18:.1f}" text-anchor="middle" fill="#ff6b6b" font-family="monospace" font-size="8">{hp*1000:.0f}</text>')

    svg_lines.append(f'<text x="{cx}" y="{svg_height - 15}" text-anchor="middle" fill="#999" font-family="monospace" font-size="10">Position along bore (mm)</text>')
    svg_lines.append("</svg>")
    return "\n".join(svg_lines)


def _empty_svg(msg: str) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="400" height="200">
  <rect width="100%" height="100%" fill="#1a1a2e"/>
  <text x="200" y="100" text-anchor="middle" fill="#666" font-family="monospace" font-size="14">{msg}</text>
</svg>'''
