RESOURCE BRANCHER

Double-click "Launch Resource Brancher.bat" to open the app.
Requires Windows, Python 3.10 or newer on PATH, and Microsoft Edge WebView2 Runtime.
The launcher sets up pywebview on first use if needed. Administrator launch is normally not needed.

1. Click Add source folder or Choose folder and select the real folder, such as:
   C:\Resources\my-resource
2. Click Add destination and choose a parent folder.
3. Choose the server's resources location. The source folder name is added automatically.
   Edit the full path if you want a different folder name or location.
4. Add more destinations for your other servers.
5. Click Create branches.

The app remembers destinations separately for each source folder. Use the Sources sidebar
to return to a saved setup. The refresh button checks link status again.

BRANCHING HISTORY

Open the History tab to see earlier branches across all your source folders.
Search by folder name or full path. Each row shows its recorded date and current link status.
Choose Load setup on a history entry to return to its destinations.
Loading a setup does not create or replace any links; use Create branches when ready.

Created means the app created the link on that date. Found means an existing link was
recognised in a saved setup; its original creation date is unknown.
Removing a destination from a setup does not remove its history.
The app remembers its own setups; it does not scan your drives for unrelated junctions.

HOW IT WORKS

These "branches" are Windows directory junctions, not copies or Git branches.
All destinations refer to the same real source files. GitHub Desktop should track the source folder.
Edits, additions and deletions made through ANY branch affect the same source files.
Configuration files are shared too. Rebuild the UI and restart resources as usual after changes.

EXISTING FOLDERS

An existing real folder or a link pointing elsewhere is blocked. Nothing is overwritten or moved.
Compare any existing server copy with your source, and stop the affected server before replacing it.
Move or rename the old copy yourself, then refresh the list and create the branch.
An existing junction to the selected source is recognised and left alone.

"Remove from setup" only forgets a destination. It does not delete its junction or files.
Editing a saved destination path likewise does not remove a previously created junction.
For removing a junction itself, Windows Command Prompt's rmdir "FULL BRANCH PATH" removes
the junction only. Do not add /s, and do not delete the files inside the branch.

Use local drives with junction support. Network shares are not supported.
Keep the real source folder in place: moving it will break junctions pointing to its old location.

FILES

resource_brancher.py   Desktop window and folder pickers.
branch_store.py        Saved setups and history.
ui/                    Interface files.
junctions.py           Junction creation and path checks.
settings.json         Saved in %LOCALAPPDATA%\Resource Brancher, outside the app folder.
brancher-error.log    Startup errors, if any.
