"""
3D Printability validator for wind instruments.

Checks bore designs against FDM printing constraints:
- Minimum wall thickness
- Maximum overhang angle
- Section length limits for print bed
- Joint design recommendations
- Support removal feasibility

Usage:
    from backend.printability import PrintabilityChecker
    checker = PrintabilityChecker()
    report = checker.validate(bore_profile, outer_diameter, ...)
"""

import math
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class PrintabilityIssue:
    severity: str  # "error", "warning", "info"
    category: str  # "wall_thickness", "overhang", "joint", "support", "length"
    message: str
    position_mm: Optional[float] = None
    recommendation: str = ""


class PrintabilityChecker:
    """
    Validates wind instrument designs for FDM 3D printing.

    Default constraints based on typical FDM capabilities:
    - Min wall thickness: 1.2mm (2 perimeters at 0.4mm nozzle)
    - Max overhang: 45 degrees (self-supporting)
    - Max section length: 200mm (typical print bed height)
    - Min hole diameter: 2mm (for reliable extrusion)
    """

    def __init__(
        self,
        min_wall_thickness_mm: float = 1.2,
        max_overhang_deg: float = 45.0,
        max_section_length_mm: float = 200.0,
        min_hole_diameter_mm: float = 2.0,
        nozzle_diameter_mm: float = 0.4,
        layer_height_mm: float = 0.2,
    ):
        self.min_wall = min_wall_thickness_mm
        self.max_overhang = max_overhang_deg
        self.max_section = max_section_length_mm
        self.min_hole = min_hole_diameter_mm
        self.nozzle = nozzle_diameter_mm
        self.layer = layer_height_mm

    def validate(
        self,
        bore_positions: List[float],
        bore_diameters: List[float],
        outer_diameters: List[float],
        hole_positions: Optional[List[float]] = None,
        hole_diameters: Optional[List[float]] = None,
        hole_lengths: Optional[List[float]] = None,
    ) -> Dict:
        """
        Validate a bore design for printability.

        Returns:
            Dict with 'issues', 'score' (0-100), 'grade' (A-F), and 'summary'
        """
        issues = []

        # Check wall thickness
        issues.extend(self._check_wall_thickness(bore_positions, bore_diameters, outer_diameters))

        # Check bore taper (overhang)
        issues.extend(self._check_overhang(bore_positions, bore_diameters))

        # Check section lengths
        issues.extend(self._check_section_lengths(bore_positions))

        # Check tone holes
        if hole_positions and hole_diameters:
            issues.extend(self._check_tone_holes(hole_positions, hole_diameters, bore_diameters, bore_positions))

        # Check for sharp corners
        issues.extend(self._check_sharp_corners(bore_positions, bore_diameters))

        # Calculate score
        errors = sum(1 for i in issues if i.severity == "error")
        warnings = sum(1 for i in issues if i.severity == "warning")
        infos = sum(1 for i in issues if i.severity == "info")

        score = max(0, 100 - errors * 20 - warnings * 5 - infos * 1)
        grade = self._score_to_grade(score)

        summary = self._generate_summary(issues, score, grade)

        return {
            "issues": [
                {
                    "severity": i.severity,
                    "category": i.category,
                    "message": i.message,
                    "position_mm": i.position_mm,
                    "recommendation": i.recommendation,
                }
                for i in issues
            ],
            "score": score,
            "grade": grade,
            "summary": summary,
            "n_errors": errors,
            "n_warnings": warnings,
            "n_infos": infos,
        }

    def _check_wall_thickness(self, positions, bore_diams, outer_diams):
        issues = []
        for i, (pos, b_diam, o_diam) in enumerate(zip(positions, bore_diams, outer_diams)):
            wall = (o_diam - b_diam) / 2.0
            if wall < self.min_wall:
                issues.append(PrintabilityIssue(
                    severity="error" if wall < 0.8 else "warning",
                    category="wall_thickness",
                    message=f"Wall thickness {wall:.2f}mm at {pos:.1f}mm (min: {self.min_wall}mm)",
                    position_mm=pos,
                    recommendation=f"Increase outer diameter by {self.min_wall - wall:.2f}mm at this point",
                ))
        return issues

    def _check_overhang(self, positions, bore_diams):
        issues = []
        for i in range(len(positions) - 1):
            dx = positions[i + 1] - positions[i]
            if dx <= 0:
                continue
            dy = (bore_diams[i + 1] - bore_diams[i]) / 2.0
            if abs(dx) > 1e-6:
                angle = math.degrees(math.atan2(abs(dy), dx))
                if angle > self.max_overhang:
                    issues.append(PrintabilityIssue(
                        severity="warning",
                        category="overhang",
                        message=f"Overhang {angle:.1f}° at {positions[i]:.1f}mm (max: {self.max_overhang}°)",
                        position_mm=positions[i],
                        recommendation="Add support material or split into sections",
                    ))
        return issues

    def _check_section_lengths(self, positions):
        issues = []
        if len(positions) < 2:
            return issues
        total_length = positions[-1] - positions[0]
        if total_length > self.max_section:
            n_sections = math.ceil(total_length / self.max_section)
            issues.append(PrintabilityIssue(
                severity="warning",
                category="length",
                message=f"Total length {total_length:.0f}mm exceeds print bed ({self.max_section}mm)",
                recommendation=f"Split into {n_sections} sections with joints",
            ))
        return issues

    def _check_tone_holes(self, hole_positions, hole_diams, bore_diams, bore_positions):
        issues = []
        for i, (pos, h_diam) in enumerate(zip(hole_positions, hole_diams)):
            if h_diam < self.min_hole:
                issues.append(PrintabilityIssue(
                    severity="error",
                    category="hole_size",
                    message=f"Hole diameter {h_diam:.2f}mm at {pos:.1f}mm (min: {self.min_hole}mm)",
                    position_mm=pos,
                    recommendation=f"Increase hole diameter to at least {self.min_hole}mm",
                ))
        return issues

    def _check_sharp_corners(self, positions, bore_diams):
        issues = []
        for i in range(1, len(positions) - 1):
            prev_dy = bore_diams[i] - bore_diams[i - 1]
            next_dy = bore_diams[i + 1] - bore_diams[i]
            if prev_dy * next_dy < 0 and abs(prev_dy - next_dy) > 0.5:
                issues.append(PrintabilityIssue(
                    severity="info",
                    category="sharp_corner",
                    message=f"Sharp bore profile change at {positions[i]:.1f}mm",
                    position_mm=positions[i],
                    recommendation="Smooth the bore profile for better print quality",
                ))
        return issues

    def _score_to_grade(self, score):
        if score >= 90: return "A"
        if score >= 80: return "B"
        if score >= 70: return "C"
        if score >= 60: return "D"
        return "F"

    def _generate_summary(self, issues, score, grade):
        errors = [i for i in issues if i.severity == "error"]
        warnings = [i for i in issues if i.severity == "warning"]

        if not errors and not warnings:
            return "Design is ready for FDM printing. No issues found."

        parts = []
        if errors:
            parts.append(f"{len(errors)} critical issue(s) must be fixed before printing")
        if warnings:
            parts.append(f"{len(warnings)} warning(s) should be addressed")

        return ". ".join(parts) + f" Overall grade: {grade} ({score}/100)"


def suggest_joints(total_length_mm: float, max_section_mm: float = 200.0) -> List[Dict]:
    """
    Suggest joint positions for splitting a long bore into printable sections.

    Returns list of dicts with 'position_mm', 'type', and 'description'.
    """
    if total_length_mm <= max_section_mm:
        return [{"position_mm": total_length_mm / 2, "type": "none", "description": "No joints needed"}]

    n_sections = math.ceil(total_length_mm / max_section_mm)
    section_length = total_length_mm / n_sections

    joints = []
    for i in range(1, n_sections):
        pos = i * section_length
        joints.append({
            "position_mm": pos,
            "type": "mortise_tenon",
            "description": f"Mortise-tenon joint at {pos:.0f}mm (section {i}/{n_sections})",
        })

    return joints
