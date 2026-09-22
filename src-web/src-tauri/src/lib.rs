use std::process::Command;

#[tauri::command]
fn execute_shell(cmd: String) -> Result<String, String> {
    let output = if cfg!(target_os = "windows") {
        Command::new("cmd").args(["/C", &cmd]).output()
    } else {
        Command::new("bash").args(["-c", &cmd]).output()
    };

    match output {
        Ok(out) => {
            let stdout = String::from_utf8_lossy(&out.stdout).to_string();
            let stderr = String::from_utf8_lossy(&out.stderr).to_string();
            if out.status.success() {
                Ok(stdout)
            } else {
                Err(format!("Error (exit code {:?}): {}{}", out.status.code(), stderr, stdout))
            }
        }
        Err(e) => Err(format!("Fallo ejecutando comando: {}", e)),
    }
}

#[tauri::command]
fn run_opencode(prompt: String) -> Result<String, String> {
    let home = std::env::var("HOME").unwrap_or_else(|_| ".".to_string());
    let opencode_path = format!("{}/.opencode/bin/opencode", home);

    let output = Command::new(&opencode_path)
        .args(["run", &prompt])
        .output();

    match output {
        Ok(out) => {
            let stdout = String::from_utf8_lossy(&out.stdout).to_string();
            let stderr = String::from_utf8_lossy(&out.stderr).to_string();
            if out.status.success() {
                Ok(stdout)
            } else {
                Ok(format!("{}\n{}", stdout, stderr))
            }
        }
        Err(e) => Err(format!("Fallo al invocar OpenCode: {}", e)),
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
  tauri::Builder::default()
    .setup(|app| {
      if cfg!(debug_assertions) {
        app.handle().plugin(
          tauri_plugin_log::Builder::default()
            .level(log::LevelFilter::Info)
            .build(),
        )?;
      }
      Ok(())
    })
    .invoke_handler(tauri::generate_handler![execute_shell, run_opencode])
    .run(tauri::generate_context!())
    .expect("error while running tauri application");
}
