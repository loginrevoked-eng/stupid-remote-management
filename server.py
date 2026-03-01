from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from enum import Enum
import os
import json
import base64
import subprocess
from typing import Optional, Dict, Any
from dyn_config import SERVER_MAGIC_TOKEN



app = FastAPI()





def authenticate(req: Request) -> None:
    magic_token = req.headers.get("x-magic-token")
    if magic_token != SERVER_MAGIC_TOKEN:
        raise HTTPException(status_code=401, detail="Unauthorized")

class RPCCommand(Enum):
    READ = "read"
    WRITE = "write"
    DELETE = "delete"
    LIST = "list"
    MKDIR = "mkdir"
    RMDIR = "rmdir"
    RUNRAWCOMMANDSINSHELL = "RAW"


class FileService:
    @staticmethod
    def get_file_modified_time(path: str) -> str:
        return str(os.path.getmtime(path))

    @staticmethod
    def read_file(path: str, mode: str = "rb") -> str:
        try:
            with open(path, mode) as f:
                content = f.read()
                if mode == "rb":
                    return base64.b64encode(content).decode('utf-8')
                return content
        except Exception as e:
            raise Exception(f"Failed to read file: {str(e)}")

    @staticmethod
    def write_file(path: str, data: str, mode: str = "wb") -> bool:
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, mode) as f:
                if isinstance(data, str) and mode == "wb":
                    f.write(base64.b64decode(data))
                else:
                    f.write(data)
            return True
        except Exception as e:
            raise Exception(f"Failed to write file: {str(e)}")

    @staticmethod
    def delete_file(path: str) -> bool:
        if os.path.isfile(path):
            os.remove(path)
            return True
        return False

    @staticmethod
    def list_directory(path: str) -> list:
        if not os.path.isdir(path):
            raise Exception("Path is not a directory")
        
        items = []
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            item_info = {
                "name": item,
                "type": "directory" if os.path.isdir(item_path) else "file",
                "size": os.path.getsize(item_path) if os.path.isfile(item_path) else 0,
                "modified": str(os.path.getmtime(item_path))
            }
            items.append(item_info)
        return items

    @staticmethod
    def create_directory(path: str) -> bool:
        os.makedirs(path, exist_ok=True)
        return True

    @staticmethod
    def remove_directory(path: str) -> bool:
        if os.path.isdir(path):
            os.rmdir(path)
            return True
        return False


class CommandService:
    @staticmethod
    def execute_command(command: str, background: bool = False) -> Dict[str, Any]:
        if background:
            subprocess.Popen(command, shell=True)
            return {
                "status": "success",
                "command": command,
                "message": "Command executed in background"
            }
        
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=30
            )
            return {
                "status": "success",
                "command": command,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        except subprocess.TimeoutExpired:
            return {
                "status": "error",
                "message": "Command timed out after 30 seconds"
            }


class ResponseHelper:
    @staticmethod
    def success(message: str, data: Optional[Dict] = None) -> JSONResponse:
        response = {"status": "success", "message": message}
        if data:
            response.update(data)
        return JSONResponse(content=response)

    @staticmethod
    def error(message: str, status_code: int = 500) -> JSONResponse:
        return JSONResponse(
            content={"status": "error", "message": message},
            status_code=status_code
        )


class RPCHandler:
    def __init__(self):
        self.file_service = FileService()
        self.command_service = CommandService()
        self.response_helper = ResponseHelper()

    def _handle_read(self, path: str) -> JSONResponse:
        try:
            content = self.file_service.read_file(path)
            return JSONResponse(content={
                "filename": os.path.basename(path),
                "content": {
                    "type": "octet-stream",
                    "last-modified": self.file_service.get_file_modified_time(path),
                    "value": content
                }
            })
        except Exception as e:
            return self.response_helper.error(str(e))

    def _handle_write(self, path: str, data: str) -> JSONResponse:
        try:
            self.file_service.write_file(path, data)
            return self.response_helper.success(f"File written to {path}")
        except Exception as e:
            return self.response_helper.error(str(e))

    def _handle_delete(self, path: str) -> JSONResponse:
        try:
            if self.file_service.delete_file(path):
                return self.response_helper.success(f"File {path} deleted")
            return self.response_helper.error("File not found", 404)
        except Exception as e:
            return self.response_helper.error(str(e))

    def _handle_list(self, path: str) -> JSONResponse:
        try:
            items = self.file_service.list_directory(path)
            return JSONResponse(content={
                "status": "success",
                "items": items
            })
        except Exception as e:
            return self.response_helper.error(str(e), 400)

    def _handle_mkdir(self, path: str) -> JSONResponse:
        try:
            self.file_service.create_directory(path)
            return self.response_helper.success(f"Directory {path} created")
        except Exception as e:
            return self.response_helper.error(str(e))

    def _handle_rmdir(self, path: str) -> JSONResponse:
        try:
            if self.file_service.remove_directory(path):
                return self.response_helper.success(f"Directory {path} removed")
            return self.response_helper.error("Directory not found", 404)
        except Exception as e:
            return self.response_helper.error(str(e))

    def _handle_raw(self, data: str, optional: bool) -> JSONResponse:
        if not data:
            return self.response_helper.error("No command provided", 400)
        
        result = self.command_service.execute_command(data, optional)
        if result["status"] == "error":
            return self.response_helper.error(result["message"], 408)
        
        return JSONResponse(content=result)

    def handle_request(self, rpc_body: Dict[str, Any]) -> JSONResponse:
        command = rpc_body.get("command")
        path = rpc_body.get("path")
        data = rpc_body.get("data")
        optional = rpc_body.get("optional", False)

        handlers = {
            "read": lambda: self._handle_read(path) if path else self.response_helper.error("Path required", 400),
            "write": lambda: self._handle_write(path, data) if path and data else self.response_helper.error("Path and data required", 400),
            "delete": lambda: self._handle_delete(path) if path else self.response_helper.error("Path required", 400),
            "list": lambda: self._handle_list(path) if path else self.response_helper.error("Path required", 400),
            "mkdir": lambda: self._handle_mkdir(path) if path else self.response_helper.error("Path required", 400),
            "rmdir": lambda: self._handle_rmdir(path) if path else self.response_helper.error("Path required", 400),
            "RAW": lambda: self._handle_raw(data, optional),
        }

        handler = handlers.get(command)
        if handler:
            return handler()
        
        return self.response_helper.error("Invalid command", 400)


def rpc_ctoenum(command: str) -> RPCCommand:
    mapping = {
        "read": RPCCommand.READ,
        "write": RPCCommand.WRITE,
        "delete": RPCCommand.DELETE,
        "list": RPCCommand.LIST,
        "mkdir": RPCCommand.MKDIR,
        "rmdir": RPCCommand.RMDIR,
        "RAW": RPCCommand.RUNRAWCOMMANDSINSHELL
    }
    return mapping.get(command, RPCCommand.READ)


rpc_handler = RPCHandler()

RPC_SUPPORTED_COMMANDS = ["read", "write", "delete", "list", "mkdir", "rmdir", "RAW"]
RPC_EXPECTED_STRUCTURE = {
    "command": "REQUIRED:read|write|delete|list|mkdir|rmdir|RAW",
    "path": "REQUIRED:/path/to/file (except for RAW)",
    "data": "OPTIONAL:file content or shell command",
    "optional": "OPTIONAL:for RAW command, runs in background if true"
}


@app.get("/")
def read_root() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/rpc")
async def rpc_request(req: Request) -> JSONResponse:
    authenticate(req)
    try:
        rpc_body = await req.json()
        return rpc_handler.handle_request(rpc_body)
    except Exception as e:
        return ResponseHelper.error(f"Invalid request: {str(e)}", 400)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
