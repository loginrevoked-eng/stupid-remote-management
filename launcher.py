import socket
import os
import shutil
import subprocess
import time
import urllib.request
import json
from main_utils import parse_args, rerun_as, _exit
from dyn_config import(
    SERVER_SHARED_LOGS,
    MAIN_SERVER_EXECUTABLE_DEST,
    NGROK_DESTINATION_PATH,
    PORT_NGROK_EXPOSE
)

class server_shared_logger:
    def __init__(self, file_path):
        self.file_path = file_path
    
    def format_logs(self, message):
        return f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}\n"
    
    def log(self, message):
        if os.environ.get("HORNY_BASTARD"):
            print(message)
        with open(self.file_path, "a") as f:
            f.write(self.format_logs(message))

server_logger = server_shared_logger(SERVER_SHARED_LOGS)

def copy_ngrok(destination_path):
    if os.path.exists(destination_path):
        return
    try:
        if os.path.exists(".\\ngrok.exe"):
            shutil.copy2(".\\ngrok.exe", destination_path)
            server_logger.log("INFO: ngrok.exe copied successfully")
        else:
            server_logger.log("ERROR: ngrok.exe not found in current directory")
    except Exception as e:
        server_logger.log(f"ERROR: Failed to copy ngrok.exe: {str(e)}")

def run_ngrok(port):
    try:
        cmd = [NGROK_DESTINATION_PATH, "tcp", str(port), "--log=stdout"]
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        time.sleep(3)
        
        try:
            response = urllib.request.urlopen("http://127.0.0.1:4040/api/tunnels")
            tunnels = json.loads(response.read().decode())
            if tunnels['tunnels']:
                url = tunnels['tunnels'][0]['public_url']
                server_logger.log(f"INFO: Ngrok tunnel established at {url}")
                return url
        except Exception as api_error:
            server_logger.log(f"WARNING: Could not get URL from API: {str(api_error)}")
            
        stdout, stderr = process.communicate(timeout=10)
        if "tunnel established" in stdout.lower():
            for line in stdout.split('\n'):
                if 'tcp://' in line:
                    url = line.strip()
                    server_logger.log(f"INFO: Ngrok tunnel established at {url}")
                    return url
        
        server_logger.log("ERROR: Could not establish ngrok tunnel")
        return None
        
    except Exception as e:
        server_logger.log(f"ERROR: Failed to run ngrok: {str(e)}")
        return None

def is_connected():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(2)
    try:
        sock.sendto(b'', ("8.8.8.8", 53))
        server_logger.log("INFO: machine is connected to the internet")
        return True
    except Exception:
        server_logger.log("ERROR: machine isnt connected to the internet")
        return False
    finally:
        sock.close()

def start_server(server_path):
    try:
        subprocess.run([server_path])
        server_logger.log("INFO: Server started successfully")
    except Exception as e:
        server_logger.log(f"ERROR: Failed to start server: {str(e)}")


def main():
    args = parse_args()
    if(getattr(args, "--run-as-admin", False)):
        already_admin = rerun_as(args=getattr(args, "delegate_launch"))
        if not already_admin:
            _exit("Rerunning as admin...")
        subprocess.Popen(getattr(args, "delegate_launch"))
    if is_connected():
        copy_ngrok(NGROK_DESTINATION_PATH)
        exposed_url = run_ngrok(PORT_NGROK_EXPOSE)
        if not exposed_url:
            server_logger.log("ERROR: Ngrok failed to return exposed url")
        else:
            server_logger.log(f"INFO: Ngrok successfully started and EXPOSED_URL is {exposed_url}")
        start_server(MAIN_SERVER_EXECUTABLE_DEST)
