# File : includes\android\file.py
import os

from includes.android import command
from includes.android.websocket import (
    send_command,
    wait_response,
    receive_file
)


CHUNK_SIZE = 64 * 1024


def push_file(
    ws,
    command_id,
    local_path,
    remote_path,
    mime="application/octet-stream"
):

    if not os.path.exists(local_path):

        raise FileNotFoundError(local_path)

    file_name = os.path.basename(local_path)

    size = os.path.getsize(local_path)

    cmd = command.push_file(

        command_id=command_id,

        remote_path=remote_path,

        file_name=file_name,

        mime=mime,

        size=size

    )

    send_command(ws, cmd)

    response = wait_response(ws)

    if response is None:
        return None

    if not response.get("success", False):
        return response

    if response.get("status") != "ready":
        return response

    print(f"Sending Binary : {file_name}")

    with open(local_path, "rb") as f:

        while True:

            chunk = f.read(CHUNK_SIZE)

            if not chunk:
                break

            ws.send(chunk)

    print("Binary Sent")

    return wait_response(ws)


def pull_file(
    ws,
    remote_path,
    local_path
):

    cmd = command.pull_file(

        remote_path=remote_path

    )

    send_command(ws, cmd)

    return receive_file(
        ws,
        local_path
    )

def delete_file(
    ws,
    command_id,
    remote_path
):

    cmd = command.delete_file(

        command_id=command_id,

        remote_path=remote_path

    )

    send_command(ws, cmd)

    return wait_response(ws)