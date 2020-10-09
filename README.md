# Save Unnamed

Do you create a lot of temporary files inside Sublime Text, and then spend time deciding whether to save them or not? This plugin will assign each unnamed file a unique name and then save them to a folder of your choosing.

### Usage

Press <kbd>Ctrl</kbd>+<kbd>Shift</kbd>+<kbd>P</kbd> and choose either:

  * Save Unnamed: Save all unnamed files
  * Save Unnamed: Save all files, including unnamed files

To see what the plugin did, open console using <kbd>Ctrl</kbd>+<kbd>\`</kbd>.

New files names start with the curent date in `YYYYmmdd` format, followed by the first line of text and, if syntax was set, an appropriate extension.

### Settings

In `Preferences` → `Package Settings` → `Save Unnamed` → `Settings` you can:

* choose the destination folder
* specify whether empty views should be saved