import sublime
import sublime_plugin

import os
import re
from datetime import datetime
from functools import lru_cache
from os.path import expanduser

_, _, PLUGIN_NAME = __name__.rpartition(".")


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

def get_first_line(view):
    for n in range(50):
        text = sanitize(get_line(view, n))
        if text:
            return text[:50]

@lru_cache(128)
def get_extension_from_syntax_file(name):
    import yaml
    syntax_file = sublime.load_resource(name)
    syntax = yaml.load(syntax_file, Loader=yaml.BaseLoader)
    extension = syntax["file_extensions"][0]
    return extension

def get_extension(view):
    syntax_file_name = view.settings().get('syntax')
    if syntax_file_name.startswith('Packages/'):
        try: return get_extension_from_syntax_file(syntax_file_name)
        except: pass

def assign_file_name_to_view(view, folder):
    date = datetime.now().strftime("%Y%m%d")
    name = sanitize(view.name()) or get_first_line(view) or "(empty)"
    extension = get_extension(view) or ""
    if extension and not extension.startswith("."):
        extension = "." + extension
    for suffix in range(100):
        full_name = os.path.join(folder, date + " " + name + ("." + str(suffix) if suffix else "") + extension)
        if not os.path.exists(full_name):
            view.retarget(full_name)
            return
    log("error: couldn't find a suitable file name like", full_name)

def save_view(view, folder):
    had_file_name = bool(view.file_name())
    if not had_file_name:
        assign_file_name_to_view(view, folder)

    log("existing:" if had_file_name else "new:     ", view.file_name())
    view.run_command("save")

def get_folder():
    folder = sublime.load_settings("save_unnamed.sublime-settings").get("folder")
    folder = os.path.join(os.path.expanduser(folder), "")
    return folder if os.path.isdir(folder) else None

class SaveAllFilesIncludingUnnamedCommand(sublime_plugin.ApplicationCommand):
    def run(self):
        log("getting folder...")

        folder = get_folder()
        if not folder:
            log("error: folder", folder, "doesn't exist")
            sublime.error_message("Save Unnamed: target folder \"{}\" doesn't exist".format(folder))
            return

        log("saving all files to {}...".format(folder))
        for window in sublime.windows():
            for view in window.views():
                if view.is_dirty():
                    save_view(view, folder)
        log("done")
