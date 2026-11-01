# Windows builds and releases

Run `powershell -ExecutionPolicy Bypass -File scripts/build.ps1` with Python 3.11 installed.
The branded executable is in `dist/Resource Brancher/Resource Brancher.exe`.
Distribute the complete `Resource-Brancher-1.0.0-Windows.zip`; extract before launching.
Microsoft Edge WebView2 Runtime is required.
Packaged settings are stored in `%LOCALAPPDATA%/Resource Brancher`, surviving upgrades.
Source launches and packaged launches use the same personal settings folder. Settings are never bundled.

Create a GitHub repository and push this project. Change VERSION for each release,
commit, then push a matching tag such as v1.0.0. GitHub Actions tests, builds and
publishes the ZIP. Manual workflow runs produce a downloadable build artifact.
Executables are unsigned; Windows may display a reputation prompt.
