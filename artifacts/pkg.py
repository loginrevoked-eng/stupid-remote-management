#package-app.py






import subprocess
import shutil
import os
import argparse

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("FILE_NAME", help="The file to package", default="main.py")
    parser.add_argument("OUT_FILE", help="The output file name", default="main.exe")
    parser.add_argument("ICON_PATH", help="The path to the icon", default="icon.ico")
    return parser.parse_args()

def package_app(flags):
    print("starting pyinstaller with flags:", flags)
    subprocess.run(["pyinstaller", *flags])


def clean_build(out_file):
    print("cleaning build...")
    shutil.rmtree("build")
    print("copying", out_file, "to root...")
    shutil.copy2(".\\dist\\" + out_file, ".\\" + out_file)
    print("removing dist folder...")
    shutil.rmtree("dist")
    print("removing spec file...")
    os.remove(out_file + ".spec")
    print("done!")



if __name__ == "__main__":
    args = parse_args()
    FILE_NAME = args.FILE_NAME
    OUT_FILE = args.OUT_FILE
    ICON_PATH = args.ICON_PATH
    
    package_app([
        FILE_NAME, 
        "--onefile", 
        "--noconsole", 
        f"--icon={ICON_PATH}", 
        f"--name {OUT_FILE}"
    ])

    clean_build(OUT_FILE)
    print("DONE! Packaging complete!")

