# File : includes/schedule/folder.py

import json
import shutil

from pathlib import Path


def create_directory(path):

    path = Path(path)

    path.mkdir(
        parents=True,
        exist_ok=True
    )

    return path


def create_batch_folder(
    upload_directory,
    start_datetime
):

    batch_folder = Path(upload_directory) / start_datetime.strftime(
        "%Y_%m_%d_%H_%M"
    )

    batch_folder.mkdir(
        parents=True,
        exist_ok=True
    )

    return batch_folder


def create_job_folder(
    batch_folder,
    schedule_datetime
):

    folder = Path(batch_folder) / schedule_datetime.strftime(
        "%Y_%m_%d_%H_%M"
    )

    folder.mkdir(
        exist_ok=True
    )

    return folder


def create_empty_video(
    folder_path,
    filename
):

    video_file = Path(folder_path) / filename

    with open(
        video_file,
        "w",
        encoding="utf-8"
    ) as f:

        f.write("")

    return video_file


def write_json(
    filename,
    data
):

    filename = Path(filename)

    with open(
        filename,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            data,
            f,
            indent=4,
            ensure_ascii=False
        )


def write_text(
    filename,
    text
):

    filename = Path(filename)

    with open(
        filename,
        "w",
        encoding="utf-8"
    ) as f:

        f.write(text)


def copy_directory(
    source,
    destination,
    overwrite=True
):

    source = Path(source)

    destination = Path(destination)

    if not source.exists():

        return False

    if destination.exists():

        if overwrite:

            shutil.rmtree(destination)

        else:

            return False

    shutil.copytree(
        source,
        destination
    )

    return True


def copy_product_images(
    product_id,
    destination_folder
):

    source = Path(
        f"static/products/{product_id}/product"
    )

    destination = Path(destination_folder) / "product"

    return copy_directory(
        source,
        destination
    )


def copy_creator_assets(
    username,
    destination_folder
):

    source = Path(
        "data"
    ) / username

    destination = Path(destination_folder) / "aseets"

    return copy_directory(
        source,
        destination
    )


def write_product_description(
    folder_path,
    description
):

    filename = (
        Path(folder_path)
        / "product"
        / "tiktok_description.txt"
    )

    write_text(
        filename,
        description
    )

    return filename


def write_product_info(
    folder_path,
    creator_username,
    product
):

    filename = (
        Path(folder_path)
        / "product"
        / "product.txt"
    )

    content = f"""Creator : {creator_username}
Product ID : {product["id"]}
Title : {product["title"]}
Url : {product["product_link"]}
"""

    write_text(
        filename,
        content
    )

    return filename