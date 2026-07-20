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
            server_start,
            server_stop,
            server_status,
            http_get,
            http_post,
            save_file_dialog,
            open_file_dialog,
            save_stl_to_disk,
            read_stl_from_disk,
            list_instruments,
            list_preset_groups,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
