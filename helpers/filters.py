from typing import List, Union
from pyrogram import filters
from config import COMMAND_PREFIXES

def command(commands: Union[str, List[str]]):
    return filters.command(commands, COMMAND_PREFIXES)

def is_edited_message():
    def func(_, __, update):
        return update.edited_message is not None
    return filters.create(func)

def is_forwarded():
    def func(_, __, update):
        return update.forward_date is not None
    return filters.create(func)

def is_via_bot():
    def func(_, __, update):
        return update.via_bot is not None
    return filters.create(func)

other_filters = filters.group & ~is_edited_message() & ~is_via_bot() & ~is_forwarded()
other_filters2 = filters.private & ~is_edited_message() & ~is_via_bot() & ~is_forwarded()
