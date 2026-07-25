from flask import Blueprint, render_template, request, session
from includes.creator import load_creator, menambahkan_creator

creator_bp = Blueprint(
    "creator",
    __name__,
    url_prefix="/creator"
)


@creator_bp.route("/")
def creator_list():

    creators = load_creator()

    return render_template(
        "creator/index.html",
        creators=creators
    )

@creator_bp.route("/add", methods=["POST"])
def creator_add_route():

    data = request.get_json()
    result_creator_add = menambahkan_creator(data)
    print(data)

    return {
        "success": True,
        "data": result_creator_add
    }

@creator_bp.route("/select", methods=["POST"])
def creator_select():

    data = request.get_json()

    session["creator_id"] = data["creator_id"]

    return {
        "success": True
    }

@creator_bp.route("/edit/<int:creator_id>")
def creator_edit(creator_id):
    pass


@creator_bp.route("/delete/<int:creator_id>")
def creator_delete(creator_id):
    pass