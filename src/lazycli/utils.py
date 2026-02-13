import re
import os
from pathlib import Path

def validate_title(title):
    """
    Checks if title is valid and safe/ No empty title/ only alphanumeric chars spaces and '_'
    :param title: str: user given title
    :return: True if title is valid else false
    """
    if not title or not title.strip():
        return False

    if re.search(r'[^\w\s\-]', title):
        return False

    return True


def validate_tags(tags):
    """
    Checks if tags are safe and valid/No empty tags/ Only alphanumeric chars spaces and ','
    :param tags: str user given tags
    :return: True if tags are valid else false
    """
    if not isinstance(tags, str):
        return False

    tags = tags.strip()

    if not tags:
        return False

    taglist = tags.split(',')

    if len(taglist) > 2:
        return False

    if re.search(r'[^\w\s\,]', tags):
        return False

    return True


def slugify(title):
    """
    Turns the title into a slug (File system friendly)
    Example: "My First Note" -> "my-first-note"
    :param title: str: user given title
    :return: slug: str final slug
    """
    slug = re.sub(r'\s', '-', title)
    slug = re.sub(r'-+', '-', slug)
    return slug.lower().strip('-')


def get_db_path(app_name="LazyNotes"):
    """
    Defines the perm storage location based on OS
    :param app_name: str : name of application for storage folder
    :return: path:Path (path object) final path
    """
    app_data = os.getenv("APPDATA")

    if app_data:
        base_dir = Path(app_data) / app_name
    else:
        base_dir = Path.home() / f"{app_name.lower()}"

    base_dir.mkdir(parents=True, exist_ok=True)
    return base_dir / "notes.db"