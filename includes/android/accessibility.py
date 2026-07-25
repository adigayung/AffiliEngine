# File : includes\android\accessibility.py

from includes.android import command
from includes.android.websocket import (
    send_command,
    wait_response
)

from includes.android.command import (
    read_text as read_text_command
)


def click(
    ws,
    command_id,
    target,
    delay=500
):

    cmd = command.click(

        command_id=command_id,

        target=target,

        delay=delay

    )

    send_command(ws, cmd)

    response = wait_response(ws)

    if response is None:
        return False

    if isinstance(response, bytes):
        return False

    return response.get("success", False)


def input_text(
    ws,
    command_id,
    target,
    text,
    delay=500
):

    cmd = command.input_text(

        command_id=command_id,

        target=target,

        text=text,

        delay=delay

    )

    send_command(ws, cmd)

    response = wait_response(ws)

    if response is None:
        return False

    if isinstance(response, bytes):
        return False

    return response.get("success", False)


def clear_text(
    ws,
    command_id,
    target,
    delay=500
):

    cmd = command.clear_text(

        command_id=command_id,

        target=target,

        delay=delay

    )

    send_command(ws, cmd)

    response = wait_response(ws)

    if response is None:
        return False

    if isinstance(response, bytes):
        return False

    return response.get("success", False)


def read_text(
    ws,
    command_id,
    target,
    delay=0
):

    cmd = command.read_text(

        command_id=command_id,

        target=target,

        delay=delay

    )

    send_command(ws, cmd)

    response = wait_response(ws)

    if response is None:
        return None

    if isinstance(response, bytes):
        return None

    if not response.get("success", False):
        return None

    return response.get("data", {}).get("text", "")