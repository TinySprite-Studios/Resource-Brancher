# Windows builds and releases

Run `powershell -ExecutionPolicy Bypass -File scripts/build.ps1` with Python 3.11 installed.
The branded executable is in `dist/Resource Brancher/Resource Brancher.exe`.
Distribute the complete `Resource-Brancher-1.0.0-Windows.zip`; extract before launching.
Microsoft Edge WebView2 Runtime is required.
Packaged settings are stored in `%LOCALAPPDATA%/Resource Brancher`, surviving upgrades.
Source launches and packaged launches use the same personal settings folder. Settings are never bundled.

Commit and push your changes to the existing GitHub repository, then create and
push a tag such as `v1.0.1`. The tag supplies the release version automatically.
GitHub Actions runs tests, builds that tagged commit, and publishes a release titled
`v1.0.1` with the Windows ZIP attached and generated release notes.
For example: `git tag v1.0.1` then `git push origin v1.0.1`.
The workflow must be committed before tagging. Creating a tag only on your computer
does not trigger GitHub. Manual workflow runs produce a downloadable build artifact.
Local builds use VERSION; update it when you want the local ZIP version to change.

Executables are unsigned; Windows may display a reputation prompt.

## In-app updates
Built apps check the latest public GitHub release on launch. Users can also check
manually, download, then choose Restart with update. Downloads require GitHub's
SHA-256 asset digest. Drafts, prereleases and older versions are ignored.
Updates run from a versioned folder under Local AppData/Resource Brancher.
The original portable EXE stays at its previous version; launching it again requires
checking for updates again. Source copies use Git and cannot install updates.
Personal settings are shared across versions and never sent to GitHub.
The first release containing the updater must be downloaded manually.
