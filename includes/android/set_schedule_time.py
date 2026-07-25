# File : includes/android/set_schedule_time.py

from includes.android import command
from includes.android.websocket import (
    send_command,
    wait_response
)


def set_schedule_time(
    ws,
    command_id,
    day,
    hour,
    minute,
    delay=500
):

    cmd = command.set_schedule_time(

        command_id=command_id,

        day=day,

        hour=hour,

        minute=minute,

        delay=delay

    )

    send_command(ws, cmd)

    return wait_response(ws)