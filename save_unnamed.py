import sublime
import sublime_plugin

import os
import re
import plistlib
from datetime import datetime
from functools import lru_cache
from os.path import expanduser

PLUGIN_NAME = "Save Unnamed"
SETTINGS_FILE = "save_unnamed.sublime-settings"


def log(*text):
    print(PLUGIN_NAME + ":", *text)


def sanitize(text):
    text = re.sub(r"[^\w\-_\. {}()\[\]$=,]", "_", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def get_line(view, n, max_chars=100):
    line = view.line(view.text_point(n, 0))
    if line.size() > max_chars:
        line = sublime.Region(line.begin(), line.begin() + max_chars)
    return view.substr(line)


def get_first_line_with_text(view):
    for n in range(50):
        text = sanitize(get_line(view, n))
        if text:
            return text[:50]


def get_extension_from_tmlanguage(data):
    data = plistlib.readPlistFromBytes(data.encode("utf-8"))
    return data['fileTypes'][0]


# sublime-syntax is a yaml file;
# avoid parsing the whole file with yaml as it's slow
RE_FIRST_FILE_EXTENSION = re.compile(r"^file_extensions\s*:\s*[\r\n]*\s*-\s+(\w+)", re.M)
def get_extesnion_from_sublime_syntax(data):
    return RE_FIRST_FILE_EXTENSION.search(data).group(1)


@lru_cache(128)
def get_extension_from_syntax_file(name):
    try:
        data = sublime.load_resource(name)
        if name.endswith("tmLanguage"): return get_extension_from_tmlanguage(data)
        else: return get_extesnion_from_sublime_syntax(data)
    except Exception as e:
        log("error: couldn't retreive the extension from", name)
        import traceback; traceback.print_exc()
        return None


def get_extension(view):
    syntax_file_name = view.settings().get('syntax')
    return get_extension_from_syntax_file(syntax_file_name) if syntax_file_name.startswith('Packages/') else None


def assign_file_name_to_view(view, folder):
    date = datetime.now().strftime("%Y%m%d")
    name = sanitize(view.name()) or get_first_line_with_text(view) or "(empty)"
    extension = get_extension(view) or ""
    if extension and not extension.startswith("."):
        extension = "." + extension
    for suffix in range(50):
        full_name = os.path.join(folder, date + " " + name + ("." + str(suffix) if suffix else "") + extension)
        if not os.path.exists(full_name):
            view.retarget(full_name)
            return
    log("error: couldn't find a suitable file name like", full_name)


def save_view(view, folder):
    had_file_name = bool(view.file_name())

    if had_file_name:
        log("saving a view into existing file:", view.file_name())
    else:
        assign_file_name_to_view(view, folder)
        log("saving a view into a new file:", view.file_name())

    view.run_command("save")


# joining the folder with "" puts an appropriate slash on the end of the folder
# this prevents windows from wrongly reporting that a directory "foo " exists
def get_folder():
    folder = sublime.load_settings(SETTINGS_FILE).get("folder")
    folder = os.path.join(os.path.expanduser(folder), "")
    if not os.path.isdir(folder):
        raise IOError("""folder "{}" doesn't exist""".format(folder))
    return folder


class SaveFiles(sublime_plugin.ApplicationCommand):
    def run(self):
        try:
            folder = get_folder()
        except IOError as e:
            sublime.error_message("{}: {}".format(PLUGIN_NAME, e))
            raise

        log(self.saving_message.format(folder))

        for window in sublime.windows():
            for view in window.views():
                if not view.is_dirty():
                    name = view.file_name()
                    log("skipping a clean view:", "(no name)" if name is None else name)
                    continue

                if not self.save_if_has_name and view.file_name():
                    log("skipping a dirty view that has a name:", view.file_name())
                    continue

                save_view(view, folder)

        log("done")


class SaveAllFilesIncludingUnnamedCommand(SaveFiles):
    saving_message = "saving all files, including unnamed, to {}..."
    save_if_has_name = True
       

class SaveAllUnnamedFilesCommand(SaveFiles):
    saving_message = "saving only unnamed files to {}..."
    save_if_has_name = False
