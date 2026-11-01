# Windows builds and releases

Install Python 3.11 and Inno Setup 6. Run `powershell -ExecutionPolicy Bypass -File scripts/build.ps1`.
The build produces a branded `dist/Resource-Brancher-Setup-VERSION.exe` and a portable ZIP.
Setup installs per user, creates a Start menu shortcut, offers a desktop shortcut,
and registers an uninstaller in Windows Settings. Microsoft Edge WebView2 Runtime is required.

## Release
Commit and push changes, then push a new stable tag such as v1.0.3.
The tag supplies the version automatically. GitHub Actions tests and builds that commit,
then publishes the installer and portable ZIP together with generated release notes.
Local builds use VERSION. Never reuse an existing published tag.

## Updates and personal data
The app checks the latest public GitHub release at launch and on request.
Download retrieves the setup EXE and verifies GitHub's SHA-256 digest.
Install and restart closes the app, waits for it to exit, runs Setup, and reopens
its installed executable. Installed copies upgrade in their existing folder.
Portable copies migrate to the normal per-user installation when using this updater.
Older ZIP-only updater builds need this installer downloaded manually once.
If installation fails, the helper displays an error and retains the installer and log
under Local AppData/Resource Brancher/update-* for retry.

Source launches and installed launches share `%LOCALAPPDATA%/Resource Brancher/settings.json`.
Settings, source/destination paths, history and backups are never copied into the build.
Setup and the uninstaller leave this settings folder intact. Source copies are updated through Git.
Executables are unsigned; Windows may show a reputation prompt.
