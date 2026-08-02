"""
Fixture importers for cross-software validation (V2 benchmarking).
===================================================================

Imports reference instruments from:
- chalumier .chal files (custom DSL format)
- demakein example designs
- WIDesigner XML instrument definitions

These serve as regression fixtures for V2 cross-software validation.
"""

import os
import re
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field


@dataclass
class FixtureInstrument:
    """Standardized fixture instrument representation."""
    name: str
    family: str
    subcategory: str
    bore_profile: List[tuple]  # [(position_mm, radius_mm), ...]
    holes: List[Dict[str, Any]]  # [{"position": mm, "diameter": mm, "length": mm}, ...]
    closed_top: bool
    targets: List[float]  # Target frequencies in Hz
    fingerings: List[List[str]]  # List of fingerings per note
    source: str  # "chalumier", "demakein", "widesigner", "manual"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FixtureRegistry:
    """Registry of all reference instruments for benchmarking."""
    
    fixtures: Dict[str, "FixtureInstrument"] = field(default_factory=dict)
    
    def add(self, fixture: "FixtureInstrument"):
        """Add a fixture to the registry."""
        self.fixtures[fixture.name] = fixture
    
    def get(self, name: str) -> Optional["FixtureInstrument"]:
        """Get a fixture by name."""
        return self.fixtures.get(name)
    
    def list_all(self) -> List[str]:
        """List all fixture names."""
        return list(self.fixtures.keys())


# Global fixture registry
FIXTURE_REGISTRY = FixtureRegistry()


def parse_chalumier_chal(filepath: str) -> "FixtureInstrument":
    """
    Parse a chalumier .chal file into a FixtureInstrument.
    
    .chal files use a custom DSL format similar to HOCON with some differences:
    - Key-value pairs: key = value
    - Lists: [item1, item2, ...]
    - Tuples: (Pair: val1, val2) or (val1, val2)
    - Nested objects: { key = value, ... }
    - Comments start with #
    - Keywords: true, false, null
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    data = parse_chal_dsl(content)
    return parse_chal_data(data, filepath)


def parse_chal_dsl(content: str) -> Dict[str, Any]:
    """Parse chalumier DSL format into a Python dict.
    
    Handles the custom DSL format used in .chal files:
    - Key-value pairs: key = value
    - Lists: [item1, item2, ...]
    - Tuples: (Pair: val1, val2) or (val1, val2)
    - Nested objects: { key = value, ... }
    - Comments: # comment
    - Keywords: true, false, null
    - Strings can be quoted or unquoted
    """
    # Remove comments
    content = re.sub(r'#.*', '', content)
    
    # Remove trailing commas before closing braces/brackets
    content = re.sub(r',\s*([}\]])', r'\1', content)
    
    # Convert to valid JSON-like format for parsing
    # This is a simplified approach - a full parser would be more robust
    
    # Convert chalumier DSL to JSON-like format
    json_like = content
    
    # Convert (Pair: x, y) to [x, y]
    json_like = re.sub(r'\(Pair:\s*([^,\s]+)\s*,\s*([^,\s\)]+)\s*\)', r'[\1, \2]', json_like)
    
    # Convert (x, y) to [x, y] for simple tuples
    json_like = re.sub(r'\(\s*([0-9\.\-]+)\s*,\s*([0-9\.\-]+)\s*\)', r'[\1, \2]', json_like)
    
    # Convert key = value to "key": value
    json_like = re.sub(r'(\w+)\s*=', r'"\1":', json_like)
    
    # Convert unquoted strings to quoted strings (but not numbers, booleans, null)
    def quote_unquoted_strings(match):
        key = match.group(1)
        value = match.group(2).strip()
        # Check if value needs quoting
        if (value.lower() in ('true', 'false', 'null') or 
            value.startswith('[') or value.startswith('{') or
            value.startswith('"') or value.startswith("'") or
            re.match(r'^[\d\.\-]+$', value) or
            value.startswith('null') or value.startswith('true') or value.startswith('false')):
            return f'{key}: {value}'
        return f'{key}: "{value}"'
    
    # Handle key-value pairs at top level
    json_like = re.sub(r'"(\w+)"\s*:\s*([^,\{\[\}]+)(?=,|\s*[}\]])', quote_unquoted_strings, json_like)
    
# Handle nested objects
    # This is a best-effort conversion
    
    try:
        return json.loads(json_like)
    except json.JSONDecodeError as e:
        return {"_parse_error": str(e), "_raw_content": content[:500]}


# Global fixture registry
FIXTURE_REGISTRY = FixtureRegistry()


def load_chalumier_fixtures(directory: str) -> List["FixtureInstrument"]:
    """Load all .chal files from a directory."""
    fixtures = []
    for filepath in Path(directory).glob("*.chal"):
        try:
            fixture = parse_chalumier_chal(str(filepath))
            fixtures.append(fixture)
            FIXTURE_REGISTRY.add(fixture)
        except Exception as e:
            print(f"Failed to parse {filepath}: {e}")
    return fixtures


def load_demakein_fixtures(directory: str) -> List["FixtureInstrument"]:
    """Load all demakein example files from a directory."""
    fixtures = []
    for filepath in Path(directory).glob("*example*.py"):
        try:
            fixture = parse_demakein_example(str(filepath))
            fixtures.append(fixture)
            FIXTURE_REGISTRY.add(fixture)
        except Exception as e:
            print(f"Failed to parse {filepath}: {e}")
    return fixtures


def load_widesigner_fixtures(directory: str) -> List["FixtureInstrument"]:
    """Load all WIDesigner XML files from a directory."""
    fixtures = []
    for filepath in Path(directory).glob("*.xml"):
        try:
            fixture = parse_widesigner_xml(str(filepath))
            fixtures.append(fixture)
            FIXTURE_REGISTRY.add(fixture)
        except Exception as e:
            print(f"Failed to parse {filepath}: {e}")
    return fixtures


def load_all_fixtures() -> FixtureRegistry:
    """
    Load all available fixtures from known locations.
    """
    base_dir = Path(__file__).parent.parent
    
    # Chalumier examples
    chalumier_dir = base_dir / "chalumier" / "examples"
    if chalumier_dir.exists():
        load_chalumier_fixtures(str(chalumier_dir))
    
    # Demakein examples (if available)
    demakein_dir = base_dir / "demakein" / "examples"
    if demakein_dir.exists():
        load_demakein_fixtures(str(demakein_dir))
    
    # WIDesigner examples
    widesigner_dir = base_dir / "widesigner" / "examples"
    if widesigner_dir.exists():
        load_widesigner_fixtures(str(widesigner_dir))
    
    return FIXTURE_REGISTRY


# Built-in reference fixtures (always available)
def register_builtin_fixtures():
    """Register built-in reference fixtures that are always available."""
    
    # Inria 2026 benchmark cylinders and cones
    FIXTURE_REGISTRY.add(FixtureInstrument(
        name="Inria Cylinder 14mm Open-Open",
        family="Flutes",
        subcategory="End-Blown Flutes",
        bore_profile=[(0, 7.0), (180, 7.0)],
        holes=[],
        closed_top=False,
        targets=[480.0, 960.0, 1440.0, 1920.0, 2400.0, 2880.0, 3360.0, 3840.0, 4320.0, 4800.0],
        fingerings=[[]],
        source="inria_2026_benchmark",
        metadata={"paper": "Ernoult et al. 2026, Acta Acustica 10:51"}
    ))
    
    FIXTURE_REGISTRY.add(FixtureInstrument(
        name="Inria Cylinder 14mm Open-Closed",
        family="Woodwinds",
        subcategory="Clarinets",
        bore_profile=[(0, 7.0), (180, 7.0)],
        holes=[],
        closed_top=True,
        targets=[240.0, 720.0, 1200.0, 1680.0, 2160.0, 2640.0, 3120.0, 3600.0, 4080.0, 4560.0],
        fingerings=[[]],
        source="inria_2026_benchmark",
        metadata={"paper": "Ernoult et al. 2026, Acta Acustica 10:51"}
    ))
    
    # Bowen 1910 Heckel Bass Clarinet
    FIXTURE_REGISTRY.add(FixtureInstrument(
        name="Bowen 1910 Heckel Bass Clarinet in A",
        family="Woodwinds",
        subcategory="Clarinets",
        bore_profile=[],
        holes=[],
        closed_top=True,
        targets=[58.27, 174.61, 232.96, 291.36, 349.23, 415.30, 466.16, 493.88, 554.37, 587.33],
        fingerings=[[True]*8 for _ in range(10)],
        source="bowen_2019",
        metadata={"paper": "Bowen et al. 2019, Applied Acoustics 143:84-99, DOI 10.1016/j.apacoust.2018.08.028"}
    ))
    
    # UNSW Boehm Flute
    FIXTURE_REGISTRY.add(FixtureInstrument(
        name="UNSW Boehm Flute C-foot",
        family="Flutes",
        subcategory="Transverse Flutes",
        bore_profile=[],
        holes=[],
        closed_top=False,
        targets=[261.63, 277.18, 293.66, 311.13, 329.63, 349.23, 369.99, 392.00, 415.30, 440.00],
        fingerings=[[False]*11 for _ in range(10)],
        source="unsw_flute_acoustics",
        metadata={"url": "https://www.phys.unsw.edu.au/music/flute/"}
    ))


# Initialize built-in fixtures on module load
register_builtin_fixtures()


def load_all_fixtures() -> FixtureRegistry:
    """
    Load all available fixtures from known locations.
    """
    base_dir = Path(__file__).parent.parent
    
    # Chalumier examples
    chalumier_dir = base_dir / "chalumier" / "examples"
    if chalumier_dir.exists():
        load_chalumier_fixtures(str(chalumier_dir))
    
    # Demakein examples (if available)
    demakein_dir = base_dir / "demakein" / "examples"
    if demakein_dir.exists():
        load_demakein_fixtures(str(demakein_dir))
    
    # WIDesigner examples
    widesigner_dir = base_dir / "widesigner" / "examples"
    if widesigner_dir.exists():
        load_widesigner_fixtures(str(widesigner_dir))
    
    return FIXTURE_REGISTRY


def parse_chal_data(data: Dict[str, Any], filepath: str) -> "FixtureInstrument":
    """Parse parsed chal data into FixtureInstrument."""
    name = data.get("name", Path(filepath).stem)
    
    # Determine family and subcategory
    family = "Woodwind"
    instrument_type = str(data.get("instrument_type", "")).lower()
    if "clarinet" in instrument_type:
        subcategory = "Clarinets"
    elif "saxophone" in instrument_type:
        subcategory = "Saxophones"
    elif "flute" in instrument_type and "recorder" not in instrument_type:
        subcategory = "Flutes"
    elif "oboe" in instrument_type or "shawm" in instrument_type:
        subcategory = "Oboes"
    elif "bassoon" in instrument_type:
        subcategory = "Bassoons"
    elif "recorder" in instrument_type:
        subcategory = "Recorders"
    elif "whistle" in instrument_type:
        subcategory = "Whistles"
    elif "drone" in instrument_type:
        subcategory = "Drone"
    else:
        subcategory = "Woodwinds"
    
    # Extract bore profile from innerDiameters
    bore_profile = []
    inner_diameters = data.get("innerDiameters", [])
    length = data.get("length", 0)
    if inner_diameters:
        n = len(inner_diameters)
        for i, pair in enumerate(inner_diameters):
            pos = (i / (n - 1)) * length if n > 1 else 0
            if isinstance(pair, (list, tuple)) and len(pair) >= 2:
                radius = pair[0] / 2
            else:
                radius = float(pair) / 2
            bore_profile.append((pos, radius))
    
    # Extract holes
    holes = []
    hole_positions = data.get("initialHoleFractions", [])
    hole_diameters = data.get("minHoleDiameters", [])
    hole_lengths = data.get("holeLengths", []) if "holeLengths" in data else []
    for i, frac in enumerate(hole_positions):
        holes.append({
            "position": frac * length,
            "diameter": hole_diameters[i] if i < len(hole_diameters) else 0,
            "length": hole_lengths[i] if i < len(hole_lengths) else 0
        })
    
    # Extract fingerings
    fingerings = []
    for fingering in data.get("fingerings", []):
        fingers = fingering.get("fingers", [])
        fingerings.append([str(f) for f in fingers])
    
    closed_top = data.get("closedTop", False)
    
    # Determine subcategory from instrument type
    name = data.get("name", "")
    instrument_type = str(data.get("instrument_type", "")).lower()
    if "clarinet" in instrument_type:
        subcategory = "Clarinets"
    elif "saxophone" in instrument_type:
        subcategory = "Saxophones"
    elif "flute" in instrument_type and "recorder" not in instrument_type:
        subcategory = "Flutes"
    elif "oboe" in instrument_type or "shawm" in instrument_type:
        subcategory = "Oboes"
    elif "bassoon" in instrument_type:
        subcategory = "Bassoons"
    elif "recorder" in instrument_type:
        subcategory = "Recorders"
    elif "whistle" in instrument_type:
        subcategory = "Whistles"
    elif "drone" in instrument_type:
        subcategory = "Drone"
    else:
        subcategory = "Woodwinds"
    
    return FixtureInstrument(
        name=data.get("name", "Unknown"),
        family="Woodwind",
        subcategory=subcategory,
        bore_profile=bore_profile,
        holes=[{"position": h["position"], "diameter": h["diameter"], "length": h["length"]} 
               for h in holes],
        closed_top=data.get("closedTop", False),
        targets=[],  # Would need note frequencies
        fingerings=[[str(f) for f in fingering.get("fingers", [])] 
                    for fingering in data.get("fingerings", [])],
        source="chalumier",
        metadata={"source_file": str(Path(filepath).name)}
    )


def parse_chalumier_chal(filepath: str) -> "FixtureInstrument":
    """
    Parse a chalumier .chal file into a FixtureInstrument.
    
    .chal files use a custom DSL format similar to HOCON:
    - Key-value pairs: key = value
    - Lists: [item1, item2, ...]
    - Tuples: (Pair: val1, val2) or (val1, val2)
    - Nested objects: { key = value, ... }
    - Comments start with #
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    data = parse_chal_dsl(content)
    return parse_chal_data(data, filepath)


def parse_chal_dsl(content: str) -> Dict[str, Any]:
    """Parse chalumier DSL format into a Python dict."""
    # Remove comments
    content = re.sub(r'#.*', '', content)
    
    # Remove trailing commas before closing braces/brackets
    content = re.sub(r',\s*([}\]])', r'\1', content)
    
    # Convert to JSON-like format
    json_like = content
    
    # Convert (Pair: x, y) to [x, y]
    json_like = re.sub(r'\(Pair:\s*([^,\s]+)\s*,\s*([^,\s\)]+)\s*\)', r'[\1, \2]', json_like)
    
    # Convert (x, y) tuples
    json_like = re.sub(r'\(\s*([0-9\.\-]+)\s*,\s*([0-9\.\-]+)\s*\)', r'[\1, \2]', json_like)
    
    # Convert key = value to "key": value
    json_like = re.sub(r'(\w+)\s*=', r'"\1":', json_like)
    
    # Handle unquoted strings
    def quote_unquoted_strings(match):
        key = match.group(1)
        value = match.group(2).strip()
        if (value.lower() in ('true', 'false', 'null') or 
            value.startswith('[') or value.startswith('{') or
            value.startswith('"') or value.startswith("'") or
            re.match(r'^[\d\.\-]+$', value) or
            value.startswith('null') or value.startswith('true') or value.startswith('false')):
            return f'{key}: {value}'
        return f'{key}: "{value}"'
    
    # Handle top-level key-value pairs
    json_like = re.sub(r'"(\w+)"\s*:\s*([^,\{\[\}]+)(?=,|\s*[}\]])', quote_unquoted_strings, json_like)
    
    try:
        return json.loads(json_like)
    except json.JSONDecodeError as e:
        return {"_parse_error": str(e), "_raw_content": content[:500]}


def parse_chal_data(data: Dict[str, Any], filepath: str) -> "FixtureInstrument":
    """Parse parsed chal data into FixtureInstrument."""
    name = data.get("name", Path(filepath).stem)
    
    # Determine family and subcategory
    family = "Woodwind"
    instrument_type = str(data.get("instrument_type", "")).lower()
    if "clarinet" in instrument_type:
        subcategory = "Clarinets"
    elif "saxophone" in instrument_type:
        subcategory = "Saxophones"
    elif "flute" in instrument_type and "recorder" not in instrument_type:
        subcategory = "Flutes"
    elif "oboe" in instrument_type or "shawm" in instrument_type:
        subcategory = "Oboes"
    elif "bassoon" in instrument_type:
        subcategory = "Bassoons"
    elif "recorder" in instrument_type:
        subcategory = "Recorders"
    elif "whistle" in instrument_type:
        subcategory = "Whistles"
    elif "drone" in instrument_type:
        subcategory = "Drone"
    else:
        subcategory = "Woodwinds"
    
    # Extract bore profile from innerDiameters
    bore_profile = []
    inner_diameters = data.get("innerDiameters", [])
    length = data.get("length", 0)
    if inner_diameters:
        n = len(inner_diameters)
        for i, pair in enumerate(inner_diameters):
            pos = (i / (n - 1)) * length if n > 1 else 0
            if isinstance(pair, (list, tuple)) and len(pair) >= 2:
                radius = pair[0] / 2
            else:
                radius = float(pair) / 2
            bore_profile.append((pos, radius))
    
    # Extract holes
    holes = []
    hole_positions = data.get("initialHoleFractions", [])
    hole_diameters = data.get("minHoleDiameters", [])
    hole_lengths = data.get("holeLengths", []) if "holeLengths" in data else []
    for i, frac in enumerate(hole_positions):
        holes.append({
            "position": frac * length,
            "diameter": hole_diameters[i] if i < len(hole_diameters) else 0,
            "length": hole_lengths[i] if i < len(hole_lengths) else 0
        })
    
    # Extract fingerings
    fingerings = []
    for fingering in data.get("fingerings", []):
        fingers = fingering.get("fingers", [])
        fingerings.append([str(f) for f in fingers])
    
    closed_top = data.get("closedTop", False)
    
    # Determine subcategory from instrument type
    name = data.get("name", "")
    instrument_type = str(data.get("instrument_type", "")).lower()
    if "clarinet" in instrument_type:
        subcategory = "Clarinets"
    elif "saxophone" in instrument_type:
        subcategory = "Saxophones"
    elif "flute" in instrument_type and "recorder" not in instrument_type:
        subcategory = "Flutes"
    elif "oboe" in instrument_type or "shawm" in instrument_type:
        subcategory = "Oboes"
    elif "bassoon" in instrument_type:
        subcategory = "Bassoons"
    elif "recorder" in instrument_type:
        subcategory = "Recorders"
    elif "whistle" in instrument_type:
        subcategory = "Whistles"
    elif "drone" in instrument_type:
        subcategory = "Drone"
    else:
        subcategory = "Woodwinds"
    
    return FixtureInstrument(
        name=data.get("name", Path(filepath).stem),
        family="Woodwind",
        subcategory=subcategory,
        bore_profile=bore_profile,
        holes=[{"position": h["position"], "diameter": h["diameter"], "length": h["length"]} 
               for h in holes],
        closed_top=data.get("closedTop", False),
        targets=[],  # Would need note frequencies
        fingerings=[[str(f) for f in fingering.get("fingers", [])] 
                    for fingering in data.get("fingerings", [])],
        source="chalumier",
        metadata={"source_file": str(Path(filepath).name)}
    )


def parse_chalumier_chal(filepath: str) -> "FixtureInstrument":
    """
    Parse a chalumier .chal file into a FixtureInstrument.
    
    .chal files use a custom DSL format similar to HOCON:
    - Key-value pairs: key = value
    - Lists: [item1, item2, ...]
    - Tuples: (Pair: val1, val2) or (val1, val2)
    - Nested objects: { key = value, ... }
    - Comments start with #
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    data = parse_chal_dsl(content)
    return parse_chal_data(data, filepath)


def parse_chal_dsl(content: str) -> Dict[str, Any]:
    """Parse chalumier DSL format into a Python dict.
    
    Handles the custom DSL format used in .chal files:
    - Key-value pairs: key = value
    - Lists: [item1, item2, ...]
    - Tuples: (Pair: val1, val2) or (val1, val2)
    - Nested objects: { key = value, ... }
    - Comments start with #
    """
    # Remove comments
    content = re.sub(r'#.*', '', content)
    
    # Remove trailing commas before closing braces/brackets
    content = re.sub(r',\s*([}\]])', r'\1', content)
    
    # Convert to JSON-like format
    json_like = content
    
    # Convert (Pair: x, y) to [x, y]
    json_like = re.sub(r'\(Pair:\s*([^,\s]+)\s*,\s*([^,\s\)]+)\s*\)', r'[\1, \2]', json_like)
    
    # Convert (x, y) tuples
    json_like = re.sub(r'\(\s*([0-9\.\-]+)\s*,\s*([0-9\.\-]+)\s*\)', r'[\1, \2]', json_like)
    
    # Convert key = value to "key": value
    json_like = re.sub(r'(\w+)\s*=', r'"\1":', json_like)
    
    # Handle unquoted strings
    def quote_unquoted_strings(match):
        key = match.group(1)
        value = match.group(2).strip()
        if (value.lower() in ('true', 'false', 'null') or 
            value.startswith('[') or value.startswith('{') or
            value.startswith('"') or value.startswith("'") or
            re.match(r'^[\d\.\-]+$', value) or
            value.startswith('null') or value.startswith('true') or value.startswith('false')):
            return f'{key}: {value}'
        return f'{key}: "{value}"'
    
    # Handle top-level key-value pairs
    json_like = re.sub(r'"(\w+)"\s*:\s*([^,\{\[\}]+)(?=,|\s*[}\]])', quote_unquoted_strings, json_like)
    
    try:
        return json.loads(json_like)
    except json.JSONDecodeError as e:
        return {"_parse_error": str(e), "_raw_content": content[:500]}