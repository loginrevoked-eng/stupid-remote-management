#!/usr/bin/env python3
import requests
import json
import base64
import sys
import os
from typing import Optional, Dict, Any
import cmd
import argparse


class RPCClient:
    def __init__(self, host: str, port: int, magic_token: str):
        self.base_url = f"http://{host}:{port}"
        self.magic_token = magic_token
        self.session = requests.Session()
        self.session.headers.update({
            "x-magic-token": magic_token,
            "Content-Type": "application/json"
        })

    def send_request(self, command: str, path: str = None, data: str = None, optional: bool = False) -> Dict[str, Any]:
        payload = {"command": command}
        if path is not None:
            payload["path"] = path
        if data is not None:
            payload["data"] = data
        if optional:
            payload["optional"] = True

        try:
            response = self.session.post(f"{self.base_url}/rpc", json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"status": "error", "message": f"Connection error: {str(e)}"}
        except json.JSONDecodeError:
            return {"status": "error", "message": "Invalid JSON response from server"}

    def test_connection(self) -> bool:
        try:
            response = requests.get(f"{self.base_url}/")
            return response.status_code == 200
        except:
            return False


class RPCClientREPL(cmd.Cmd):
    intro = """
RPC File System Client - Simple Version

Commands:
  test                    - Test connection
  ls <path>              - List directory
  exec <command>          - Execute command
  exit                    - Exit
"""
    prompt = "rpc> "

    def __init__(self, client: RPCClient):
        super().__init__()
        self.client = client

    def do_test(self, arg):
        """Test server connection"""
        print("Testing connection...")
        if self.client.test_connection():
            print("SUCCESS: Connected to server")
        else:
            print("ERROR: Failed to connect")

    def do_ls(self, arg):
        """List directory: ls <path>"""
        if not arg:
            print("ERROR: Path required")
            return
        
        print(f"Listing directory: {arg}")
        result = self.client.send_request("list", path=arg)
        
        if result.get("status") == "success" and "items" in result:
            items = result["items"]
            if not items:
                print("(empty directory)")
            else:
                for item in items:
                    item_type = "[DIR]" if item["type"] == "directory" else "[FILE]"
                    size = f"{item['size']} bytes" if item["type"] == "file" else "<DIR>"
                    print(f"{item_type} {item['name']:<30} {size:>15}")
        else:
            print(f"ERROR: {result.get('message', 'Unknown error')}")

    def do_exec(self, arg):
        """Execute shell command: exec <command>"""
        if not arg:
            print("ERROR: Command required")
            return
        
        print(f"Executing: {arg}")
        result = self.client.send_request("RAW", data=arg)
        
        if result.get("status") == "success":
            print("SUCCESS")
            if "stdout" in result and result["stdout"].strip():
                print("STDOUT:")
                print(result["stdout"])
            if "stderr" in result and result["stderr"].strip():
                print("STDERR:")
                print(result["stderr"])
            if "returncode" in result:
                print(f"Return code: {result['returncode']}")
        else:
            print(f"ERROR: {result.get('message', 'Unknown error')}")

    def do_exit(self, arg):
        """Exit client"""
        print("Goodbye!")
        return True


def main():
    parser = argparse.ArgumentParser(description="RPC File System Client")
    parser.add_argument("--host", default="localhost", help="Server host")
    parser.add_argument("--port", type=int, default=8000, help="Server port")
    parser.add_argument("--token", default="68098fd3-771f-4fd3-a460-0b6bbc180205", help="Magic token")
    
    args = parser.parse_args()
    
    client = RPCClient(args.host, args.port, args.token)
    
    print(f"Connecting to {args.host}:{args.port}...")
    if not client.test_connection():
        print(f"ERROR: Failed to connect to server")
        sys.exit(1)
    
    print("SUCCESS: Connected!")
    
    try:
        RPCClientREPL(client).cmdloop()
    except KeyboardInterrupt:
        print("\nGoodbye!")


if __name__ == "__main__":
    main()
