
# File : includes\creator.py
from flask import session
from includes.mysql import add_creator, get_creator, get_creator_list

def get_active_creator():

    print("SESSION =", dict(session))

    creator_id = session.get("creator_id")

    print("creator_id =", creator_id)

    if creator_id:

        current_creator = get_creator(creator_id)

    else :
        return None

    return current_creator

def menambahkan_creator(data):

    hasil = add_creator(data)

    return hasil

def load_creator():

    hasil = get_creator_list()

    return hasil