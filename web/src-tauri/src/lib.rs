mod commands;

use commands::*;

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_log::Builder::default().build())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_process::init())
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_http::init())
        .invoke_handler(tauri::generate_handler![
            demakein_design,
            demakein_make,
            openwind_simulate,
            freecad_bore_to_step,
            freecad_step_to_stl,
            openscad_generate,
            slice_stl,
            read_stl_file,
            save_stl_file,
            list_instruments,
            check_server_health,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
