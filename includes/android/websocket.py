# file : includes\android\websocket.py
import json


def send_command(ws, command):

    print(f"Send : {command['cmd']}")

    ws.send(json.dumps(command))


def wait_response(ws):

    response = ws.receive()

    if response is None:
        return None

    if isinstance(response, bytes):
        return response

    print("Receive :", response)

    return json.loads(response)


def receive_binary(
    ws,
    expected_size
):

    buffer = bytearray()

    while len(buffer) < expected_size:

        chunk = ws.receive()

        if chunk is None:
            return None

        if not isinstance(chunk, bytes):
            continue

        buffer.extend(chunk)

        print(
            f"Receive Binary : {len(buffer)}/{expected_size}"
        )

    return bytes(buffer)

def receive_file(
    ws,
    local_path
):

    response = wait_response(ws)

    if response is None:
        return None

    if response.get("type") != "file":
        return response

    expected_size = response["size"]

    print("Waiting Binary :", response["file_name"])
    print("Expected Size :", expected_size)

    binary = receive_binary(
        ws,
        expected_size
    )

    if binary is None:
        return None

    with open(local_path, "wb") as f:
        f.write(binary)

    print("File Saved :", local_path)

    response["local_path"] = local_path

    return response
