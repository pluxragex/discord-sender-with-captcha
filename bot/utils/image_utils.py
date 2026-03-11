from typing import Iterable


IMAGE_EXTENSIONS: tuple[str, ...] = (".png", ".jpg", ".jpeg", ".webp")


def is_supported_image_filename(filename: str) -> bool:
    lower = filename.lower()
    return any(lower.endswith(ext) for ext in IMAGE_EXTENSIONS)


def any_supported_attachment(
    filenames: Iterable[str],
) -> bool:
    return any(is_supported_image_filename(name) for name in filenames)

