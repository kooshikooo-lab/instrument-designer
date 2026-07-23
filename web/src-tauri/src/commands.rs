use serde::{Deserialize, Serialize};
use std::process::{Child, Command, Stdio};
use std::sync::Mutex;
use tokio::sync::oneshot;

static SERVER_CHILD: Mutex<Option<Child>> = Mutex::new(None);

#[derive(Debug, Serialize, Deserialize)]
pub struct InstrumentInfo {
    pub name: String,
    pub family: String,
    pub preset: String,
    pub range: String,
    pub key: String,
    pub description: String,
}

// ── Python Server Management ──────────────────────────────────────────

#[tauri::command]
pub async fn server_start(port: u16) -> Result<String, String> {
    let mut child = SERVER_CHILD.lock().map_err(|e| e.to_string())?;

    if child.is_some() {
        return Ok("Server already running".into());
    }

    let script = format!(
        r#"import sys; sys.path.insert(0, '.'); from woodwind_designer.engine.design_server import app; import uvicorn; uvicorn.run(app, host='127.0.0.1', port={})"#,
        port
    );

    let c = Command::new("python")
        .args(["-c", &script])
        .current_dir(std::env::current_dir().map_err(|e| e.to_string())?)
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .map_err(|e| format!("Failed to start Python server: {}", e))?;

    *child = Some(c);
    Ok(format!("Server starting on port {}", port))
}

#[tauri::command]
pub async fn server_stop() -> Result<String, String> {
    let mut child = SERVER_CHILD.lock().map_err(|e| e.to_string())?;

    if let Some(mut c) = child.take() {
        drop(c.kill().map_err(|e| format!("Failed to stop server: {}", e)));
        Ok("Server stopped".into())
    } else {
        Ok("No server running".into())
    }
}

#[tauri::command]
pub async fn server_status() -> Result<bool, String> {
    let child = SERVER_CHILD.lock().map_err(|e| e.to_string())?;
    Ok(child.is_some())
}

// ── HTTP Bridge ───────────────────────────────────────────────────────

#[tauri::command]
pub async fn http_get(url: String) -> Result<String, String> {
    let resp = reqwest::get(&url)
        .await
        .map_err(|e| format!("HTTP GET failed: {}", e))?;
    resp.text()
        .await
        .map_err(|e| format!("Failed to read response: {}", e))
}

#[tauri::command]
pub async fn http_post(url: String, body: serde_json::Value) -> Result<String, String> {
    let client = reqwest::Client::new();
    let resp = client
        .post(&url)
        .json(&body)
        .send()
        .await
        .map_err(|e| format!("HTTP POST failed: {}", e))?;
    resp.text()
        .await
        .map_err(|e| format!("Failed to read response: {}", e))
}

// ── File Dialogs ──────────────────────────────────────────────────────

#[tauri::command]
pub async fn save_file_dialog(
    app: tauri::AppHandle,
    default_name: String,
    filter_name: String,
    filter_ext: String,
) -> Result<Option<String>, String> {
    use tauri_plugin_dialog::{DialogExt, FilePath};

    let (tx, rx) = oneshot::channel::<Option<FilePath>>();

    app.dialog()
        .file()
        .add_filter(&filter_name, &[&filter_ext])
        .set_file_name(&default_name)
        .save_file(move |path| {
            let _ = tx.send(path);
        });

    let path = rx.await.map_err(|_| "Dialog cancelled".to_string())?;
    Ok(path.map(|p| p.to_string()))
}

#[tauri::command]
pub async fn open_file_dialog(
    app: tauri::AppHandle,
    filter_name: String,
    filter_ext: String,
) -> Result<Option<String>, String> {
    use tauri_plugin_dialog::{DialogExt, FilePath};

    let (tx, rx) = oneshot::channel::<Option<FilePath>>();

    app.dialog()
        .file()
        .add_filter(&filter_name, &[&filter_ext])
        .pick_file(move |path| {
            let _ = tx.send(path);
        });

    let path = rx.await.map_err(|_| "Dialog cancelled".to_string())?;
    Ok(path.map(|p| p.to_string()))
}

#[tauri::command]
pub async fn save_stl_to_disk(path: String, data: Vec<u8>) -> Result<(), String> {
    std::fs::write(&path, &data).map_err(|e| format!("Failed to save file: {}", e))
}

#[tauri::command]
pub async fn read_stl_from_disk(path: String) -> Result<Vec<u8>, String> {
    std::fs::read(&path).map_err(|e| format!("Failed to read file: {}", e))
}

// ── Instrument Metadata ───────────────────────────────────────────────

#[tauri::command]
pub async fn list_instruments() -> Result<Vec<InstrumentInfo>, String> {
    Ok(vec![
        InstrumentInfo {
            name: "Folk Flute".into(),
            family: "Flute".into(),
            preset: "folk_flute".into(),
            range: "C5-C7".into(),
            key: "C".into(),
            description: "Pennywhistle-style folk flute, 6 holes".into(),
        },
        InstrumentInfo {
            name: "Penny Whistle".into(),
            family: "Flute".into(),
            preset: "folk_whistle".into(),
            range: "D5-D7".into(),
            key: "D".into(),
            description: "Tin whistle with pennywhistle fingering".into(),
        },
        InstrumentInfo {
            name: "Soprano Recorder".into(),
            family: "Flute".into(),
            preset: "recorder".into(),
            range: "C5-C7".into(),
            key: "C".into(),
            description: "Recorder with full fingering system".into(),
        },
        InstrumentInfo {
            name: "Dorian Whistle".into(),
            family: "Flute".into(),
            preset: "dorian_whistle".into(),
            range: "D5-D7".into(),
            key: "D".into(),
            description: "Whistle tuned to the Dorian mode".into(),
        },
        InstrumentInfo {
            name: "Three-Hole Whistle".into(),
            family: "Flute".into(),
            preset: "three_hole_whistle".into(),
            range: "C5-C7".into(),
            key: "C".into(),
            description: "Medieval three-hole tabor pipe".into(),
        },
        InstrumentInfo {
            name: "Reedpipe".into(),
            family: "Woodwind".into(),
            preset: "reedpipe".into(),
            range: "C4-C6".into(),
            key: "C".into(),
            description: "Simple single-reed pipe".into(),
        },
        InstrumentInfo {
            name: "Folk Shawm".into(),
            family: "Woodwind".into(),
            preset: "folk_shawm".into(),
            range: "C4-C6".into(),
            key: "C".into(),
            description: "Compact double-reed folk shawm".into(),
        },
        InstrumentInfo {
            name: "Shawm".into(),
            family: "Woodwind".into(),
            preset: "shawm".into(),
            range: "C4-C6".into(),
            key: "C".into(),
            description: "Full double-reed shawm".into(),
        },
        InstrumentInfo {
            name: "Reed Drone".into(),
            family: "Woodwind".into(),
            preset: "reed_drone".into(),
            range: "C3-C5".into(),
            key: "C".into(),
            description: "Continuous-sounding reed drone pipe".into(),
        },
    ])
}

// ── Preset Helpers ────────────────────────────────────────────────────

#[derive(Debug, Serialize, Deserialize)]
pub struct PresetGroup {
    pub label: String,
    pub presets: Vec<PresetEntry>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct PresetEntry {
    pub key: String,
    pub name: String,
    pub description: String,
}

#[tauri::command]
pub async fn list_preset_groups() -> Result<Vec<PresetGroup>, String> {
    Ok(vec![
        PresetGroup {
            label: "Flute".into(),
            presets: vec![
                PresetEntry { key: "folk_flute".into(), name: "Folk Flute".into(), description: "Pennywhistle-style folk flute, 6 holes".into() },
                PresetEntry { key: "folk_whistle".into(), name: "Penny Whistle".into(), description: "Tin whistle with pennywhistle fingering".into() },
                PresetEntry { key: "recorder".into(), name: "Soprano Recorder".into(), description: "Recorder with full fingering system".into() },
                PresetEntry { key: "dorian_whistle".into(), name: "Dorian Whistle".into(), description: "Whistle tuned to the Dorian mode".into() },
                PresetEntry { key: "pflute".into(), name: "Pan Flute".into(), description: "Pan flute with multiple pipes".into() },
                PresetEntry { key: "three_hole_whistle".into(), name: "Three-Hole Whistle".into(), description: "Medieval three-hole tabor pipe".into() },
            ],
        },
        PresetGroup {
            label: "Woodwind (Reed)".into(),
            presets: vec![
                PresetEntry { key: "reedpipe".into(), name: "Reedpipe".into(), description: "Simple single-reed pipe".into() },
                PresetEntry { key: "folk_shawm".into(), name: "Folk Shawm".into(), description: "Compact double-reed folk shawm".into() },
                PresetEntry { key: "shawm".into(), name: "Shawm".into(), description: "Full double-reed shawm".into() },
                PresetEntry { key: "reed_drone".into(), name: "Reed Drone".into(), description: "Continuous-sounding reed drone pipe".into() },
            ],
        },
    ])
}
