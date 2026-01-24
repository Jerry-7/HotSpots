#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
main.py  –  WebSocket → SSH 透明转发（修复版 - 鲁棒的异常处理）
运行：./main.py
注意：此版本增加了对 'closed' 属性访问的异常处理。
"""
import asyncio
import json
import logging
import sys
import subprocess
from pathlib import Path


# ---------------- 自动装依赖 ----------------
def ensure_deps():
    try:
        import websockets, asyncssh
    except ImportError:
        print("📦 缺少依赖，正在自动安装 …")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "websockets>=12", "asyncssh>=2.14"])
        print("✅ 依赖安装完成\n")


ensure_deps()

# ---------------- 导入已确保存在的包 ----------------
import websockets
import asyncssh

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s", datefmt="%H:%M:%S")

# SESSIONS now stores (ssh_connection, channel) tuples
SESSIONS = {}  # {websocket: (ssh_connection, channel)}


class SSHShellSession(asyncssh.SSHClientSession):
    def __init__(self, ws):
        self._ws = ws  # Store the WebSocket connection object in a private variable
        self._chan = None

    def connection_made(self, chan):
        self._chan = chan
        try:
            logging.info("SSH channel established for ws %s", self._ws.remote_address)
        except AttributeError:
            logging.warning("WebSocket object lost in session during connection_made")

    def data_received(self, data, datatype):
        # Send data received from SSH to the WebSocket client
        try:
            if not self._ws.closed:  # Check WebSocket's closed state using private variable
                # Send the actual SSH output data
                asyncio.create_task(self._ws.send(data))
        except AttributeError:
            # The _ws object might have been replaced by asyncssh internals
            logging.warning("WebSocket object lost in session during data_received, cannot send data")

    def connection_lost(self, exc):
        msg = f"\r\n🔌 SSH 连接丢失: {exc}\r\n" if exc else "\r\n🔌 SSH 连接关闭\r\n"
        try:
            if not self._ws.closed:  # Check WebSocket's closed state using private variable
                asyncio.create_task(self._ws.send(msg))
        except AttributeError:
            # The _ws object might have been replaced by asyncssh internals
            logging.warning("WebSocket object lost in session during connection_lost, cannot send message")

        # Even if _ws is corrupted, try to clean up the session entry
        # We need to find the websocket key associated with this session object
        # This is tricky, so we'll try to get it from the _ws object if it's still valid
        try:
            asyncio.create_task(cleanup(self._ws))
        except AttributeError:
            logging.warning(
                "WebSocket object lost in session during connection_lost, cannot cleanup session entry directly")
            # As a fallback, iterate through SESSIONS to find the entry for this session object
            # Note: This is less efficient but more robust
            websocket_to_remove = None
            for ws_key, (ssh_conn, chan) in SESSIONS.items():
                if chan and chan._session is self:
                    websocket_to_remove = ws_key
                    break
            if websocket_to_remove:
                asyncio.create_task(cleanup(websocket_to_remove))

        try:
            logging.info("SSH connection lost for ws %s", self._ws.remote_address)
        except AttributeError:
            logging.warning("WebSocket object lost in session during connection_lost logging")


async def cleanup(ws):
    """Clean up the SSH session associated with a WebSocket."""
    if ws in SESSIONS:
        ssh_conn, chan = SESSIONS.pop(ws)
        logging.info("Cleaning up SSH session for ws %s", ws.remote_address)
        if chan:
            chan.close()
        if ssh_conn:
            ssh_conn.close()
            await ssh_conn.wait_closed()
        logging.info("SSH session cleaned up for ws %s", ws.remote_address)


async def send_ready_after_delay(websocket, delay=0.5):
    """Coroutine to send 'ready' message after a delay."""
    await asyncio.sleep(delay)
    try:
        if not websocket.closed:  # Check WebSocket's closed state
            await websocket.send(json.dumps({"type": "ready"}))
            logging.info("Sent 'ready' signal to frontend for ws %s after delay", websocket.remote_address)
    except (websockets.exceptions.ConnectionClosed, AttributeError) as e:
        logging.info("WebSocket closed or invalid object while trying to send 'ready' signal to ws %s: %s",
                     websocket.remote_address, e)


async def handler(websocket: websockets.WebSocketServerProtocol):  # Use deprecated but available type
    """
    WebSocket message handler.
    Expects JSON messages of type: connect, input, resize, disconnect.
    """
    logging.info("New WebSocket connection from %s", websocket.remote_address)
    ssh_conn = None
    chan = None

    try:
        async for msg in websocket:
            try:
                data = json.loads(msg)
            except json.JSONDecodeError:
                if not websocket.closed:
                    await websocket.send(json.dumps({"type": "error", "message": "❌ 非 JSON 消息"}))
                continue

            msg_type = data.get("type")

            if msg_type == "connect":
                if websocket in SESSIONS:
                    if not websocket.closed:
                        await websocket.send(json.dumps({"type": "error", "message": "⚠️  已连接，请先断开"}))
                    continue

                host = data.get("host")
                user = data.get("username")
                pwd = data.get("password")
                port = int(data.get("port", 22))

                try:
                    logging.info("Attempting to connect to %s@%s:%d", user, host, port)
                    ssh_conn = await asyncssh.connect(
                        host, port=port, username=user, password=pwd,
                        known_hosts=None, connect_timeout=10  # Increased timeout
                    )
                    # Create an interactive shell session
                    chan, sess = await ssh_conn.create_session(
                        lambda: SSHShellSession(websocket),  # Pass WebSocket object to session
                        term_type="xterm-color", term_size=(80, 24)  # Initial size, will be resized
                    )
                    SESSIONS[websocket] = (ssh_conn, chan)
                    # Send initial status message to client
                    await websocket.send(json.dumps({"type": "status", "message": f"✅ 已连接 {host}:{port}"}))
                    logging.info("SSH session established for ws %s to %s:%d", websocket.remote_address, host, port)

                    # CRITICAL: Start a task to send 'ready' message after a short delay
                    # This ensures the SSH session is likely ready to receive input
                    asyncio.create_task(send_ready_after_delay(websocket, delay=0.5))

                except Exception as e:
                    error_msg = f"❌ SSH 连接失败: {e}"
                    if not websocket.closed:
                        await websocket.send(json.dumps({"type": "error", "message": error_msg}))
                    logging.error("SSH connection failed for ws %s: %s", websocket.remote_address, e)

            elif msg_type == "input":
                if websocket not in SESSIONS or SESSIONS[websocket][1] is None:
                    if not websocket.closed:
                        await websocket.send(json.dumps({"type": "error", "message": "❌ 未连接或通道未就绪"}))
                    continue
                input_data = data.get("data", "")
                _, chan = SESSIONS[websocket]
                if chan:
                    # Write the raw input data to the SSH channel's stdin
                    chan.write(input_data)
                    logging.debug("Forwarded input to SSH channel for ws %s", websocket.remote_address)

            elif msg_type == "resize":
                if websocket not in SESSIONS or SESSIONS[websocket][1] is None:
                    continue  # Silently ignore if not connected, resize is non-critical
                cols = data.get("cols", 80)
                rows = data.get("rows", 24)
                _, chan = SESSIONS[websocket]
                if chan:
                    try:
                        chan.set_terminal_size(cols, rows)
                        logging.info("Resized terminal for ws %s to %dx%d", websocket.remote_address, cols, rows)
                    except Exception as e:
                        logging.warning("Failed to resize terminal for ws %s: %s", websocket.remote_address, e)

            elif msg_type == "disconnect":
                logging.info("Disconnect request received from ws %s", websocket.remote_address)
                await cleanup(websocket)
                if not websocket.closed:
                    await websocket.send(json.dumps({"type": "status", "message": "🔌 已断开"}))
                break  # Exit the message loop to close the connection

    except websockets.ConnectionClosed:
        logging.info("WebSocket connection closed by client %s", websocket.remote_address)
    except Exception as e:
        logging.error("Unexpected error in handler for ws %s: %s", websocket.remote_address, e)
    finally:
        # Ensure cleanup happens even if an exception occurs
        await cleanup(websocket)
        logging.info("Handler finished for ws %s", websocket.remote_address)


async def main():
    # Listen on all interfaces, port 8765
    server = await websockets.serve(handler, "0.0.0.0", 8765)
    logging.info("🚀 WebSocket SSH 网关已启动  ws://0.0.0.0:8765")
    await server.wait_closed()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("服务器已关闭 (KeyboardInterrupt). 再见~")



