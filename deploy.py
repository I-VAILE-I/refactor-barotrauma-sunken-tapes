import jinja2 as j2
import yaml
import subprocess
import shutil
import requests
import os
import os.path
import sys
import time
import logging
import certifi
import math
from PIL import Image
from mutagen.oggvorbis import OggVorbis
from distutils.dir_util import copy_tree
from pathlib import Path


def download_via_requests(url_source, file_name):

    response = requests.get(url_source, stream=True, verify=certifi.where())

    with open(file_name, 'wb') as out_file:
        shutil.copyfileobj(response.raw, out_file)
    del response


def rmfulldir(dirpath):
    try:
        shutil.rmtree(dirpath)
    except FileNotFoundError:
        pass


def update():
    logging.info(f"checking for updates via git pull.")
    pull = ["utils/git/bin/git.exe", "pull"]
    subprocess.call(pull)


def download_and_extract(url_source, out_archive):
    logging.info(f"Downloading {url_source}, this may take a while.")

    download_via_requests(url_source, out_archive)
    time.sleep(0.7)
    logging.info("Download complete.")

    logging.info(f"Extracting {out_archive}")
    extract = ["utils/7z/7za.exe", "x", out_archive, "-o" "./utils/"]
    subprocess.call(extract)

    time.sleep(0.7)
    logging.info("Removing " + out_archive)
    os.remove(out_archive)


def download_ffmpeg(clean=False):
    if clean:
        rmfulldir("./ffmpeg-6.0-full_build/bin/ffmpeg.exe")

    url_ffmpeg_source = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-full.7z"
    out_ffmpeg_archive = "./utils/ffmpeg-release-full.7z.exe"

    download_and_extract(url_ffmpeg_source, out_ffmpeg_archive)


def download_git(clean=False):
    if clean:
        rmfulldir("./utils/PortableGit-2.33.0.2-64-bit")

    url_git_source = "https://github.com/git-for-windows/git/releases/download/" + \
                     "v2.33.0.windows.2/PortableGit-2.33.0.2-64-bit.7z.exe"
    out_git_archive = "./utils/PortableGit-2.33.0.2-64-bit.7z"

    download_via_requests(url_git_source, out_git_archive)
    time.sleep(0.7)
    logging.info("Download complete.")

    logging.info(f"Extracting {out_git_archive}")
    extract = [out_git_archive, "-o" "./utils/git", "-y"]
    subprocess.call(extract)

    time.sleep(0.7)
    logging.info("Removing " + out_git_archive)
    os.remove(out_git_archive)


def get_ffmpeg_version():
    url_ffmpeg_version = "https://www.gyan.dev/ffmpeg/builds/release-version"

    fp = requests.get(url_ffmpeg_version, verify=certifi.where())
    ffmpeg_version = fp.text
    del fp

    return ffmpeg_version


def fetch_and_cut_song(tape):
    python_executable = "./venv/Scripts/python.exe"
    script = "./fetch_song.py"

    if type(tape["source"]) == str:
        shutil.copy(tape["source"], f"./build/music/{tape['identifier']}.ogg")
    else:
        fetch = [python_executable, script, tape["source"]["url"], "-x", "--audio-format", "vorbis",
                 "--audio-quality", "0", "-o", f"./build/tmp_music/{tape['identifier']}.ogg"]

        # this is done in a separate python script because subprocess.call makes sure that the
        # download process is finished before trying to cut the song

        subprocess.call(fetch)

        time.sleep(0.1)

        cut = ["./ffmpeg-6.0-full_build/bin/ffmpeg.exe",
               "-y", "-ss", f"{tape['source']['start']}",
               "-i", f"./build/tmp_music/{tape['identifier']}.ogg", "-acodec", "libvorbis",
               "-ac", "1", "-af", f"volume={tape['source']['volume']}dB",
               f"./build/music/{tape['identifier']}.ogg"]

        if tape["source"]["end"] != -1:
            cut = cut[:-7] + ["-to", f"{tape['source']['end']}"] + cut[-7:]

        try:
            subprocess.call(cut)
        except FileNotFoundError:
            print("ffmpeg not in utils directory. Run python install_dependencies.py "
                  "or download the latest release version manually.")
            sys.exit()

    walkman = ["./ffmpeg-6.0-full_build/bin/ffmpeg.exe",
               "-i", f"./build/music/{tape['identifier']}.ogg",
               "-af", f"highpass=f=300,lowpass=f=12000",
               f"./build/music/{tape['identifier']}-walkman.ogg"]

    try:
        subprocess.call(walkman)
    except FileNotFoundError:
        print("ffmpeg not in utils directory. Run python install_dependencies.py "
              "or download the latest release version manually.")
        sys.exit()


def assemble_png_images(tapes, outfile: str, resize=None):

    img_names = [f"./source/images/{tape['identifier']}.png" for tape in tapes]

    images = [Image.open(x) for x in img_names]

    if resize is not None:
        for i, (im, tape) in enumerate(zip(images, tapes)):
            im.thumbnail((128, 82), Image.ANTIALIAS)
            if resize == (64, 41) and tape["icon_resize"] == "blur":
                im.thumbnail(resize, Image.ANTIALIAS)
            else:
                im.thumbnail(resize, Image.NEAREST)
            images[i] = im

    widths, heights = zip(*(i.size for i in images))

    columns = int((len(images))**0.5)
    rows = int(math.ceil(len(images) / columns))

    total_width = max(widths) * columns
    max_height = max(heights) * rows

    new_im = Image.new('RGBA', (total_width, max_height))

    for i, im in enumerate(images):
        x_offset = max(widths) * (i % columns)
        y_offset = max(heights) * math.floor(i / columns)
        new_im.paste(im, (x_offset, y_offset))

    new_im.save(f"./build/{outfile}.png")


def prepare_music(data):
    try:
        os.mkdir('./build/music/')
    except FileExistsError:
        pass

    logging.info("reading ffmpeg version")
    ffmpeg_version = get_ffmpeg_version()
    logging.info(f"ffmpeg version is {ffmpeg_version}")

    logging.info("downloading and cutting the songs")
    for i, tape in enumerate(data):
        if not (os.path.exists(f"./build/music/{tape['identifier']}.ogg") or os.path.exists(f"./build/music/{tape['identifier']}-walkman.ogg")):
            logging.info(f"{i + 1}/{len(data)} Downloading: {tape['name']}")
            fetch_and_cut_song(tape)
        else:
            logging.info(f"{i + 1}/{len(data)} Already exists: {tape['name']}")

    logging.info(f"removing temporary music folder")
    rmfulldir('./build/tmp_music/')

    logging.info(f"copying the sound effects to build")
    copy_tree("./source/sound_effects", "./build/sound_effects")


def prepare_images(data, config):
    logging.info(f"assembling covers and icons into png files")
    assemble_png_images(data, "covers")
    assemble_png_images(data, "icons", resize=(64, 41))
    assemble_png_images(data, "sprites", resize=(33, 21))

    logging.info(f"copying other images")
    shutil.copy("./source/images/players_icons.png", "./build/players_icons.png")
    shutil.copy("./source/images/players_sprites.png", "./build/players_sprites.png")
    shutil.copy("./source/images/PreviewImage.png", "./build/PreviewImage.png")


def build_xml_code(data, config):
    logging.info(f"calculate the value that lets you use the songs n-times")
    song_lengths = [OggVorbis(f"./build/music/{tape['identifier']}.ogg").info.length
                    for tape in data]

    use_lengths = [song_length * n for song_length, n in
                   zip(song_lengths, [tape["no_of_uses"] for tape in data])]

    condition_delta = [f"{1 / use_length:0.5f}" for use_length in use_lengths]
    affliction_delta = [100 / song_length for song_length in song_lengths]

    columns = int((len(data))**0.5)
    positions = [{"column": i % columns, "row": math.floor(i / columns)} for i in range(len(data))]

    logging.info(f"creating jinja environment")
    # create jinja2 environment
    j2env = j2.Environment(loader=j2.FileSystemLoader(Path(".")))
    j2env.globals.update(zip=zip)

    # load the template file
    template0 = j2env.get_template("./source/filelist_template.xml")
    template1 = j2env.get_template("./source/sunken_tapes_template.xml")

    template2 = j2env.get_template("./source/sunken_tapes_style_template.xml")

    logging.info(f"rendering the xml files")
    with open("./build/filelist.xml", "w+", encoding="utf8") as output_file:
        # render the template
        output_file.write(template0.render(config=config, tapes=data))

    with open(f"./build/{config['slug']}.xml", "w+", encoding="utf8") as output_file:
        # render the template
        output_file.write(template1.render(tapes=data, config=config,
                                           condition_delta=condition_delta,
                                           affliction_delta=affliction_delta,
                                           song_lengths=song_lengths,
                                           positions=positions))

    with open(f"./build/{config['slug']}_style.xml", "w+", encoding="utf8") as output_file:
        # render the template
        output_file.write(template2.render(tapes=data, config=config, positions=positions))


def deploy(config):
    try:
        os.mkdir('./build')
    except FileExistsError:
        logging.info(f"removing old XML files in ./build/:")
        for f in Path('./build/').glob("*.xml"):
            logging.info(f"  {f}")
            os.remove(f)
        pass

    logging.info("Reading tapes.yaml")
    data_file = Path("./source/tapes.yaml")

    # load yaml file
    with data_file.open(encoding='utf-8') as fr:
        data = yaml.load(fr, Loader=yaml.SafeLoader)

    prepare_music(data)
    prepare_images(data, config)
    build_xml_code(data, config)

    mod_directory = f"/LocalMods/{config['name']}/"

    logging.info(f"removing the old installed mod directory {config['installdir'] + mod_directory}")
    rmfulldir(config["installdir"] + mod_directory)

    logging.info(f"copying the new build")
    if Path(config["installdir"]).is_dir():
        copy_tree("./build/", config["installdir"] + mod_directory)
    else:
        raise FileNotFoundError(
            f"{config['installdir']} does not exist. Set up the correct Barotrauma installation directory")

    logging.info(f"Done!")
