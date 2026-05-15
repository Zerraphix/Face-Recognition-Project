from pathlib import Path
from werkzeug.utils import secure_filename


ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg"}


def allowed_file(filename, allowed_extensions):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in allowed_extensions
    )


def save_uploaded_file(file, upload_folder, allowed_extensions=None, preferred_name=None):
    if allowed_extensions is None:
        allowed_extensions = ALLOWED_IMAGE_EXTENSIONS

    if file is None:
        raise ValueError("Missing file")

    if file.filename == "":
        raise ValueError("No file selected")

    if not allowed_file(file.filename, allowed_extensions):
        raise ValueError("File type not allowed")

    if preferred_name:
        filename = secure_filename(preferred_name)
    else:
        filename = secure_filename(file.filename)

    upload_path = Path(upload_folder)
    upload_path.mkdir(parents=True, exist_ok=True)

    save_path = upload_path / filename

    file.save(save_path)

    return save_path.as_posix()