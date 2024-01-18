from PIL import Image
from pathlib import Path

print(dir(Image))

size = 33, 21
#size = 64, 41
size_intermediate = 128, 82

for infile in Path('./').glob("*.png"):
    if "icon" not in str(infile) and "sprite" not in str(infile):
        try:
            outfile = infile.with_name(infile.name.replace(".png", "_sprite.png"))
            im = Image.open(infile)
            im.thumbnail(size_intermediate, Image.ANTIALIAS)
            im.thumbnail(size, Image.NEAREST)
            im.save(outfile, "PNG")
        except IOError:
            print(f"cannot create thumbnail for {infile}")
