import os
import shutil
from distutils.dir_util import copy_tree
import subprocess
import stat


def rmfulldir(top):
    for root, dirs, files in os.walk(top, topdown=False):
        for name in files:
            filename = os.path.join(root, name)
            os.chmod(filename, stat.S_IWUSR)
            os.remove(filename)
        for name in dirs:
            os.rmdir(os.path.join(root, name))
    os.rmdir(top)


def main():
    try:
        os.mkdir('./barotrauma-sunken-tapes')
    except FileExistsError:
        pass

    copy_tree("./source/", "./barotrauma-sunken-tapes/source")
    copy_tree("./utils/7z", "./barotrauma-sunken-tapes/utils/7z")
    copy_tree("./utils/python-3.9.7-embed-amd64", "./barotrauma-sunken-tapes/utils/python-3.9.7-embed-amd64")
    copy_tree("./.git", "./barotrauma-sunken-tapes/.git")
    copy_tree("./docs", "./barotrauma-sunken-tapes/docs")
    shutil.copy("./deploy.py", "./barotrauma-sunken-tapes/deploy.py")
    shutil.copy("./main.py", "./barotrauma-sunken-tapes/main.py")
    shutil.copy("./publish.py", "./barotrauma-sunken-tapes/publish.py")
    shutil.copy("./tooltip.py", "./barotrauma-sunken-tapes/tooltip.py")
    shutil.copy("./fetch_song.py", "./barotrauma-sunken-tapes/fetch_song.py")
    shutil.copy("./install.bat", "./barotrauma-sunken-tapes/install.bat")
    shutil.copy("./README.md", "./barotrauma-sunken-tapes/README.md")
    shutil.copy("./LICENSE", "./barotrauma-sunken-tapes/LICENSE")
    shutil.copy("./.gitignore", "./barotrauma-sunken-tapes/.gitignore")

    archive = "7z a -tzip barotrauma-sunken-tapes.zip ./barotrauma-sunken-tapes".split(" ")
    subprocess.call(archive)

    shutil.copy("./barotrauma-sunken-tapes.zip",
                "../../obzorje/barotrauma-sunken-tapes/barotrauma-sunken-tapes.zip")

    os.remove("./barotrauma-sunken-tapes.zip")
    rmfulldir("./barotrauma-sunken-tapes")


if __name__ == "__main__":
    main()
