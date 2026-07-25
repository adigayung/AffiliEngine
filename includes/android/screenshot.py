# File : includes\android\screenshot.py
from includes.android import command
from includes.android.websocket import (
    send_command,
    receive_file
)


def screenshot(
    ws,
    command_id,
    local_path="screenshot.png",
    delay=1000
):

    cmd = command.screenshot(

        command_id=command_id,

        local_path=local_path,

        delay=delay

    )

    send_command(ws, cmd)

    return receive_file(ws, local_path)