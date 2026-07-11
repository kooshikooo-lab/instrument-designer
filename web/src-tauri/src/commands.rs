use serde::{Deserialize, Serialize};
use std::process::Command;

#[derive(Debug, Serialize, Deserialize)]
pub struct InstrumentInfo {
    pub name: String,
    pub family: String,
    pub demakein_preset: Option<String>,
    pub range: String,
    pub key: String,
}

// ── Demakein Integration ────────────────────────────────────────────────

#[tauri::command]
pub async fn demakein_design(
    preset: String,
    transpose: i32,
    output_dir: String,
) -> Result<String, String> {
    let output = Command::new("python3")
        .args([
            "-m", "demakein",
            "design-folk-flute:",
            &format!("{}_{}", preset, chrono_offset()),
            "--transpose",
            &transpose.to_string(),
            "--output",
            &output_dir,
        ])
        .output()
        .map_err(|e| format!("Failed to start demakein: {}", e))?;

    if output.status.success() {
        Ok(String::from_utf8_lossy(&output.stdout).to_string())
    } else {
        Err(String::from_utf8_lossy(&output.stderr).to_string())
    }
}

#[tauri::command]
pub async fn demakein_make(
    design_path: String,
    output_dir: String,
) -> Result<String, String> {
    let output = Command::new("python3")
        .args([
            "-m", "demakein",
            "make-flute:",
            &design_path,
            "--output",
            &output_dir,
        ])
        .output()
        .map_err(|e| format!("Failed to start demakein make: {}", e))?;

    if output.status.success() {
        Ok(String::from_utf8_lossy(&output.stdout).to_string())
    } else {
        Err(String::from_utf8_lossy(&output.stderr).to_string())
    }
}

// ── OpenWInD Integration ────────────────────────────────────────────────

#[tauri::command]
pub async fn openwind_simulate(
    bore_file: String,
    frequency_range: String,
) -> Result<String, String> {
    let script = format!(
        r#"
import sys
from openwind import imp_edo
import json

bore = imp_edo.load_bore_from_file('{}')
freq_range = {}
result = bore.compute_impedance(freq_range)
print(json.dumps({{
    "frequencies": result.frequencies.tolist(),
    "impedance": result.impedance.tolist()
}}))
"#,
        bore_file, frequency_range
    );

    let output = Command::new("python3")
        .args(["-c", &script])
        .output()
        .map_err(|e| format!("Failed to start openwind: {}", e))?;

    if output.status.success() {
        Ok(String::from_utf8_lossy(&output.stdout).to_string())
    } else {
        Err(String::from_utf8_lossy(&output.stderr).to_string())
    }
}

// ── FreeCAD Integration ─────────────────────────────────────────────────

#[tauri::command]
pub async fn freecad_bore_to_step(
    bore_profile: Vec<f64>,
    hole_positions: Vec<(f64, f64)>,
    output_path: String,
) -> Result<String, String> {
    let script = format!(
        r#"
import sys
import FreeCAD
import Part

bore_profile = {:?};
hole_positions = {:?};

bore = Part.makeCylinder(bore_profile[0] / 2, bore_profile[1])

for (x, y) in hole_positions:
    hole = Part.makeCylinder(y / 2, bore_profile[1], FreeCAD.Vector(x, 0, 0))
    bore = bore.cut(hole)

bore.exportStep('{}')
print('STEP exported to {}')
"#,
        bore_profile, hole_positions, output_path, output_path
    );

    let output = Command::new("freecadcmd")
        .args(["-c", &script])
        .output()
        .map_err(|e| format!("Failed to start freecad: {}", e))?;

    if output.status.success() {
        Ok(String::from_utf8_lossy(&output.stdout).to_string())
    } else {
        Err(String::from_utf8_lossy(&output.stderr).to_string())
    }
}

#[tauri::command]
pub async fn freecad_step_to_stl(
    step_path: String,
    stl_path: String,
) -> Result<String, String> {
    let script = format!(
        r#"
import sys
import FreeCAD
import Part
import Mesh

doc = FreeCAD.openDocument('{}')
shapes = [obj.Shape for obj in doc.Objects if hasattr(obj, 'Shape')]
compound = Part.makeCompound(shapes)
Mesh.export([compound], '{}')
print('STL exported to {}')
"#,
        step_path, stl_path, stl_path
    );

    let output = Command::new("freecadcmd")
        .args(["-c", &script])
        .output()
        .map_err(|e| format!("Failed to start freecad: {}", e))?;

    if output.status.success() {
        Ok(String::from_utf8_lossy(&output.stdout).to_string())
    } else {
        Err(String::from_utf8_lossy(&output.stderr).to_string())
    }
}

// ── OpenSCAD Integration ────────────────────────────────────────────────

#[tauri::command]
pub async fn openscad_generate(
    params: serde_json::Value,
    output_stl: String,
) -> Result<String, String> {
    let bore_length = params["length"].as_f64().unwrap_or(200.0);
    let bore_radius = params["boreDiameter"].as_f64().unwrap_or(20.0) / 2.0;
    let wall_thickness = params["wallThickness"].as_f64().unwrap_or(3.0);

    let scad_content = format!(
        r#"
$fn = 64;
difference() {{
    cylinder(h = {}, r = {} + {});
    cylinder(h = {} + 1, r = {});
}}
"#,
        bore_length, bore_radius, wall_thickness, bore_length, bore_radius
    );

    let scad_path = format!("{}.scad", output_stl.trim_end_matches(".stl"));
    std::fs::write(&scad_path, &scad_content)
        .map_err(|e| format!("Failed to write SCAD file: {}", e))?;

    let output = Command::new("openscad")
        .args(["-o", &output_stl, &scad_path])
        .output()
        .map_err(|e| format!("Failed to start openscad: {}", e))?;

    if output.status.success() {
        let _ = std::fs::remove_file(&scad_path);
        Ok(output_stl)
    } else {
        Err(String::from_utf8_lossy(&output.stderr).to_string())
    }
}

// ── Slicer Integration ──────────────────────────────────────────────────

#[tauri::command]
pub async fn slice_stl(
    stl_path: String,
    profile_path: Option<String>,
    output_gcode: String,
) -> Result<String, String> {
    let mut args = vec![
        "--export-gcode".to_string(),
        "-o".to_string(),
        output_gcode,
        stl_path,
    ];

    if let Some(profile) = profile_path {
        args.insert(0, "--load-settings".to_string());
        args.insert(1, profile);
    }

    let output = Command::new("prusa-slicer-console")
        .args(&args)
        .output()
        .map_err(|e| format!("Failed to start slicer: {}", e))?;

    if output.status.success() {
        Ok(String::from_utf8_lossy(&output.stdout).to_string())
    } else {
        Err(String::from_utf8_lossy(&output.stderr).to_string())
    }
}

// ── File System Utilities ───────────────────────────────────────────────

#[tauri::command]
pub async fn read_stl_file(path: String) -> Result<Vec<u8>, String> {
    std::fs::read(&path).map_err(|e| format!("Failed to read STL: {}", e))
}

#[tauri::command]
pub async fn save_stl_file(path: String, data: Vec<u8>) -> Result<(), String> {
    std::fs::write(&path, &data).map_err(|e| format!("Failed to save STL: {}", e))
}

#[tauri::command]
pub async fn list_instruments() -> Result<Vec<InstrumentInfo>, String> {
    let instruments = vec![
        InstrumentInfo {
            name: "Penny Whistle".into(),
            family: "Flutes".into(),
            demakein_preset: Some("penny_whistle".into()),
            range: "D5-D7".into(),
            key: "D".into(),
        },
        InstrumentInfo {
            name: "Recorder".into(),
            family: "Flutes".into(),
            demakein_preset: Some("recorder".into()),
            range: "C4-D6".into(),
            key: "C".into(),
        },
        InstrumentInfo {
            name: "Ocarina".into(),
            family: "Vessel Flutes".into(),
            demakein_preset: Some("ocarina".into()),
            range: "C4-C6".into(),
            key: "C".into(),
        },
    ];
    Ok(instruments)
}

#[tauri::command]
pub async fn check_server_health(url: String) -> Result<serde_json::Value, String> {
    let output = Command::new("curl")
        .args(["-s", &format!("{}/health", url)])
        .output()
        .map_err(|e| format!("Failed to check server: {}", e))?;

    if output.status.success() {
        let json_str = String::from_utf8_lossy(&output.stdout);
        serde_json::from_str(&json_str).map_err(|e| format!("Invalid JSON: {}", e))
    } else {
        Err(String::from_utf8_lossy(&output.stderr).to_string())
    }
}

// ── Helpers ─────────────────────────────────────────────────────────────

fn chrono_offset() -> u64 {
    use std::time::{SystemTime, UNIX_EPOCH};
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_secs()
}
