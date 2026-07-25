# File : includes\android\device.py
from includes.android.accessibility import (
    click,
    input_text,
    clear_text,
    read_text
)

from includes.android.screenshot import screenshot
from includes.android.set_schedule_time import set_schedule_time
from includes.android.file import (
    push_file,
    pull_file,
    delete_file
)

class AndroidDevice:

    def __init__(self, ws):

        self.ws = ws
        self.command_id = 1

    def next_id(self):

        command_id = self.command_id
        self.command_id += 1

        return command_id

    # ==========================================================
    # Screenshot
    # ==========================================================

    def screenshot(
        self,
        local_path="screenshot.png",
        delay=1000
    ):

        return screenshot(

            self.ws,

            self.next_id(),

            local_path,

            delay

        )

    # ==========================================================
    # Accessibility
    # ==========================================================

    def click(
        self,
        target,
        delay=500
    ):

        return click(

            self.ws,

            self.next_id(),

            target,

            delay

        )

    def input_text(
        self,
        target,
        text,
        delay=500
    ):

        return input_text(

            self.ws,

            self.next_id(),

            target,

            text,

            delay

        )

    def clear_text(
        self,
        target,
        delay=500
    ):

        return clear_text(

            self.ws,

            self.next_id(),

            target,

            delay

        )

    # ==========================================================
    # File
    # ==========================================================

    def push_file(
        self,
        local_path,
        remote_path,
        mime="application/octet-stream"
    ):

        return push_file(

            self.ws,

            self.next_id(),

            local_path,

            remote_path,

            mime

        )

    def pull_file(
        self,
        remote_path,
        local_path
    ):

        return pull_file(

            self.ws,

            remote_path,

            local_path

        )

    def delete_file(
        self,
        remote_path
    ):

        return delete_file(

            self.ws,

            self.next_id(),

            remote_path

        )
    
    def set_schedule_time(
        self,
        day,
        hour,
        minute,
        delay=500
    ):

        return set_schedule_time(

            self.ws,

            self.next_id(),

            day,

            hour,

            minute,

            delay

        )
    def read_text(
        self,
        target,
        delay=0
    ):

        return read_text(

            self.ws,

            self.next_id(),

            target,

            delay

        )