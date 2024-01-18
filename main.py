import os
import tkinter as tk
from tkinter import filedialog as fd
from tkinter.messagebox import showinfo, askyesno, askokcancel
from tkinter import ttk
from tooltip import Hovertip
from pathlib import Path
from deploy import download_ffmpeg, download_git, deploy, get_ffmpeg_version, update
import logging
import sys
import re
import unicodedata


def slugify(value, allow_unicode=False):
    """
    Taken from https://github.com/django/django/blob/master/django/utils/text.py
    Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
    dashes to single dashes. Remove characters that aren't alphanumerics,
    underscores, or hyphens. Convert to lowercase. Also strip leading and
    trailing whitespace, dashes, and underscores.
    """
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize('NFKC', value)
    else:
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value.lower())
    return re.sub(r'[-\s]+', '-', value).strip('-_')


def get_curr_screen_geometry():
    """
    Workaround to get the size of the current screen in a multi-screen setup.

    Returns:
        geometry (str): The standard Tk geometry string.
            [width]x[height]+[left]+[top]
    """
    root = tk.Tk()
    root.update_idletasks()
    root.attributes('-fullscreen', True)
    root.state('iconic')
    geometry = root.winfo_geometry()
    root.destroy()

    return geometry


def create_name_frame(container):
    frame = ttk.LabelFrame(container, text='Mod Name')

    # Override Workshop checkbox
    override_workshop = tk.StringVar()
    override_workshop.set("0")
    override_workshop_check = ttk.Checkbutton(
        frame,
        variable=override_workshop,
        text='Override Workshop',
        command=lambda: override_action())

    override_workshop_check.pack(side="left", padx=3, pady=3)

    name = tk.StringVar()
    name.set("Sunken Tapez")

    name_entry = ttk.Entry(frame, width=30, textvariable=name)
    name_entry.pack(side="left", padx=3, pady=3, expand=True, fill="x")

    slug = tk.StringVar()
    slug.set(slugify("Sunken Tapez"))

    slug_entry = ttk.Entry(frame, width=30, textvariable=slug)
    slug_entry["state"] = "disable"
    slug_entry.pack(side="left", padx=3, pady=3, expand=True, fill="x")

    Hovertip(override_workshop_check,
             'Keep this unchecked to prevent Steam Workshop'
             '\noverriding your custom installation.'
             '\n\nIt exists only for the author\'s convenience.')

    Hovertip(name_entry,
             'Name of the deploy mod. You can customise this'
             '\nif you want to create your own version.')

    Hovertip(slug_entry,
             'Slug of the deployed mod name that is'
             '\nused for file paths and references.')

    def update_slug(*args):
        slug.set(slugify(name.get()))

    name.trace("w", update_slug)

    def override_action():
        if override_workshop.get() == "1":
            name.set("Sunken Tapes")
            name_entry["state"] = "disable"
            slug.set("sunken_tapes")
        elif override_workshop.get() == "0":
            name.set("Sunken Tapez")
            name_entry["state"] = "normal"

    return frame, name, slug


def create_install_frame(container):
    def find_barotrauma_directory():
        first_guess = Path("C:/Program Files (x86)/Steam/steamapps/common/Barotrauma")
        second_guess = Path("D:/Steam/steamapps/common/Barotrauma")
        third_guess = Path("D:/SteamLibrary/steamapps/common/Barotrauma")

        if first_guess.is_dir():
            return first_guess.as_posix()
        elif second_guess.is_dir():
            return second_guess.as_posix()
        elif third_guess.is_dir():
            return third_guess.as_posix()
        else:
            return False

    def select_barotrauma_directory():
        return_dir = fd.askdirectory(initialdir="C:/")
        install_dir.set(return_dir)

    frame = ttk.LabelFrame(container, text='Barotrauma installation directory')

    find_button = ttk.Button(frame, text='Guess',
                             command=lambda: install_dir.set(find_barotrauma_directory()))
    find_button.pack(side="left", padx=3, pady=3)

    install_dir = tk.StringVar()
    install_dir.set(find_barotrauma_directory())

    directory_entry = ttk.Entry(frame, width=60, textvariable=install_dir)
    directory_entry.pack(side="left", padx=3, pady=3, expand=True, fill="x")

    browse_button = ttk.Button(frame, text='Browse', command=select_barotrauma_directory)
    browse_button.pack(side="left", padx=3, pady=3)

    return frame, install_dir


def create_options_frame(container):
    frame = ttk.LabelFrame(container, text='Options')

    # Buffs checkbox
    buffs = tk.StringVar()
    buffs.set("1")
    buffs_check = ttk.Checkbutton(
        frame,
        variable=buffs,
        text='Buffs',
        command=lambda: print(buffs.get()))

    Hovertip(buffs_check,
             'Check this box to enable some songs causing strange effects'
             '\nThis is the intended default behaviour.')

    for widget in frame.winfo_children():
        widget.pack(side="top", padx=3, pady=3, fill="x")

    return frame, buffs


def create_resolution_frame(container):
    frame = ttk.LabelFrame(container, text='Resolution')

    def detect_screen_resolution():
        w, h = get_curr_screen_geometry().split("+")[0].split("x")
        width.set(w)
        height.set(h)

    width = tk.StringVar()
    width.set("1920")
    width_label = ttk.Label(frame, text='Width:')
    width_frame = ttk.Entry(frame, width=12, textvariable=width)

    height = tk.StringVar()
    height.set("1080")
    height_label = ttk.Label(frame, text='Height:')
    height_frame = ttk.Entry(frame, width=12, textvariable=height)

    detect_button = ttk.Button(frame, text='Detect', command=detect_screen_resolution)

    for widget in frame.winfo_children():
        widget.pack(side="left", padx=3, pady=3)

    return frame, width, height


def create_deploy_frame(container, config):
    def deploy_action():
        config_values = {"installdir": config["installdir"].get(),
                         "buffs": config["buffs"].get() == "1",
                         "name": config["name"].get(),
                         "slug": config["slug"].get(),
                         "resolution_x": int(config["resolution_x"].get()),
                         "resolution_y": int(config["resolution_y"].get())}

        logging.info(f"deploying with config: {config_values}")
        deploy(config_values)

        if config_values["name"] != "Sunken Tapes":
            note = f'\n\nThis is a custom version and is named {config_values["name"]} to differentiate it from ' \
                   + 'the Steam Workshop version that would overwrite it otherwise.' \
                   + '\n\nPlease include a link to the original mod if you publish it to Steam Workshop.'
        else:
            note = ""

        showinfo(title='Success!',
                 message=f'{config_values["name"]} was successfully installed to:'
                         f'\n\n{config_values["installdir"]}/Mods/{config_values["slug"]}'
                         f'\n\nThis installer will now close.'
                         f'{note}')

        container.destroy()

    def download_ffmpeg_action():
        def finish():
            does_ffmpeg_exists()
            showinfo(title='Success!',
                     message=f'ffmpeg downloaded. You can now deploy Sunken Tapes:')

        if not Path("./full_build/bin/ffmpeg.exe").exists():
            download_ffmpeg()
            finish()
            return
        else:
            answer = askyesno(title='ffmpeg already downloaded',
                              message='ffmpeg is already in utils directory!'
                                      '\n\nDelete the existing one and download again?')

        if answer:
            download_ffmpeg(clean=True)
            finish()
        else:
            return

    def update_action():
        if not Path("./utils/git").exists():
            answer = askokcancel(
                title='Confirmation',
                message='Portable version of git will be downloaded.'
                        '\nThis is needed to check for updates in the repository')
            if answer:
                download_git()
            else:
                return
        else:
            logging.info(f"git already in utils")

        update()

    def does_ffmpeg_exists():
        if Path("./ffmpeg-6.0-full_build/bin/ffmpeg.exe").exists():
            deploy_button["state"] = "normal"
            download_tools_button["state"] = "disable"
        else:
            deploy_button["state"] = "disable"
            download_tools_button["state"] = "normal"

    frame = ttk.LabelFrame(container, text='Install')

    frame_1 = ttk.Frame(frame)

    download_tools_label = ttk.Label(frame_1, text='Download and unpack ffmpeg:')
    download_tools_label.pack(side="left", padx=3, pady=3)
    download_tools_button = ttk.Button(frame_1, text='Download', command=download_ffmpeg_action)
    download_tools_button.pack(side="right", padx=3, pady=3)

    frame_1.pack(side="top", fill="x")

    frame_2 = ttk.Frame(frame)

    update_label = ttk.Label(frame_2, text='Download update from git.kompot.si/jaka/barotrauma-sunken-tapes:')
    update_label.pack(side="left", padx=3, pady=3)
    update_button = ttk.Button(frame_2, text='Update', command=update_action)
    update_button.pack(side="right", padx=3, pady=3)

    frame_2.pack(side="top", fill="x")

    frame_3 = ttk.Frame(frame)

    deploy_label = ttk.Label(frame_3, text='Download songs and deploy mod to Barotrauma Mods directory:')
    deploy_label.pack(side="left", padx=3, pady=3)
    deploy_button = ttk.Button(frame_3, text='Deploy', command=deploy_action)
    deploy_button.pack(side="right", padx=3, pady=3)

    frame_3.pack(side="top", fill="x")

    does_ffmpeg_exists()

    return frame


def create_main_window():
    # root window
    root = tk.Tk()
    root.title('Sunken Tapes')
    middle_frame = ttk.Frame(root)

    name_frame, name, slug = create_name_frame(root)
    install_frame, install_dir = create_install_frame(root)
    options_frame, buffs = create_options_frame(middle_frame)
    resolution_frame, width, height = create_resolution_frame(middle_frame)

    config = {"installdir": install_dir,
              "buffs": buffs,
              "name": name,
              "slug": slug,
              "resolution_x": width,
              "resolution_y": height}

    deploy_frame = create_deploy_frame(root, config)

    name_frame.pack(side="top", fill="x", pady=3, padx=3)
    install_frame.pack(side="top", fill="x", pady=3, padx=3)
    options_frame.pack(side="left", fill="y", pady=3, padx=3)
    resolution_frame.pack(side="left", fill="both", pady=3, padx=3, expand=True)
    middle_frame.pack(side="top", fill="x")
    deploy_frame.pack(side="top", fill="x", pady=3, padx=3)

    root.mainloop()


if __name__ == "__main__":
    os.chdir(Path(__file__).parents[0])
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    create_main_window()
