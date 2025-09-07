use anyhow::Result;
use eframe::egui;
use env_logger;
use log;
use piano_code::gui::PianoApp;

struct ErrorApp {
    error: String,
}

impl eframe::App for ErrorApp {
    fn update(&mut self, ctx: &egui::Context, _frame: &mut eframe::Frame) {
        egui::CentralPanel::default().show(ctx, |ui| {
            ui.heading("❌ Piano Code - Error");
            ui.separator();
            ui.label("Failed to initialize Piano Code:");
            ui.label(&self.error);
            ui.separator();
            ui.label("Please check the logs for more details.");
        });
    }
}

fn main() -> Result<()> {
    // Initialize logging
    env_logger::Builder::from_env(env_logger::Env::default().default_filter_or("info"))
        .filter_module("winit", log::LevelFilter::Error) // silence winit warnings
        .init();
    
    log::info!("🎹 Welcome to Piano Code (Rust GUI Mode)!");
    
    let options = eframe::NativeOptions {
        viewport: egui::ViewportBuilder::default()
            .with_inner_size([900.0, 650.0])
            .with_min_inner_size([800.0, 500.0])
            .with_title("🎹 Piano Code - Rust GUI")
            .with_resizable(true),
        ..Default::default()
    };

    eframe::run_native(
        "Piano Code",
        options,
        Box::new(|cc| {
            match PianoApp::new(cc) {
                Ok(app) => {
                    log::info!("✅ Piano GUI initialized successfully");
                    log::info!("🎵 Click keys or use keyboard to play!");
                    Box::new(app)
                }
                Err(e) => {
                    log::error!("❌ Error initializing Piano GUI: {}", e);
                    // Return a minimal error app instead
                    Box::new(ErrorApp { error: e.to_string() })
                }
            }
        }),
    )
    .map_err(|e| anyhow::anyhow!("Failed to run GUI: {}", e))?;

    Ok(())
}