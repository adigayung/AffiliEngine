# File : includes\android\command.py
def screenshot(command_id, local_path="screenshot.png", delay=1000):

    return {

        "id": command_id,

        "cmd": "screenshot",

        "delay": delay,

        "data": {

            "save_as": local_path

        }

    }


def click(command_id, target, delay=500):

    return {

        "id": command_id,

        "cmd": "click",

        "delay": delay,

        "data": {

            "target": target

        }

    }


def input_text(command_id, target, text, delay=500):

    return {

        "id": command_id,

        "cmd": "input_text",

        "delay": delay,

        "data": {

            "target": target,

            "text": text

        }

    }


def clear_text(command_id, target, delay=500):

    return {

        "id": command_id,

        "cmd": "clear_text",

        "delay": delay,

        "data": {

            "target": target

        }

    }


def push_file(command_id, remote_path, file_name, mime, size):

    return {

        "id": command_id,

        "cmd": "push_file",

        "delay": 0,

        "data": {

            "remote": remote_path,

            "file_name": file_name,

            "mime": mime,

            "size": size

        }

    }


def pull_file(remote_path):

    return {

        "cmd": "send_file",

        "delay": 0,

        "data": {

            "path": remote_path

        }

    }


def delete_file(command_id, remote_path):

    return {

        "id": command_id,

        "cmd": "delete_file",

        "delay": 0,

        "data": {

            "path": remote_path

        }

    }

def set_schedule_time(
    command_id,
    day,
    hour,
    minute,
    delay=500
):

    return {

        "id": command_id,

        "cmd": "set_schedule_time",

        "delay": delay,

        "data": {

            "day": day,

            "hour": hour,

            "minute": minute

        }

    }

def read_text(command_id, target, delay=0):

    return {

        "id": command_id,

        "cmd": "read_text",

        "delay": delay,

        "data": {

            "target": target

        }

    }