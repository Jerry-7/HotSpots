import json
import pathlib
from typing import Any, List

from mcp.server.fastmcp import FastMCP
import os


# Create an MCP server
mcp = FastMCP("Demo")

# Add an addition tool
@mcp.tool()
def sum(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b

# Add a dynamic greeting resource
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    return f"Hello, {name}!"

@mcp.tool()
def read_file(path: str) -> list[Any] | str:
    """
    读取指定目录下的所有文件名（不包括子目录中的文件）

    参数:
        directory_path (str): 目录路径

    返回:
        List[str]: 文件名列表
    """
    try:
        file_list = []
        for root, dirs, files in os.walk(path):
            for file in files:
                full_path = os.path.join(root, file)
                file_list.append({
                    "path": full_path,
                    "name": file
                })
        return json.dumps(file_list, ensure_ascii=False, indent=2)
    except FileNotFoundError:
        print(f"目录不存在: {path}")
        return []
    except PermissionError:
        print(f"没有权限访问目录: {path}")
        return []

if __name__ == "__main__":
    mcp.run(transport="stdio")
