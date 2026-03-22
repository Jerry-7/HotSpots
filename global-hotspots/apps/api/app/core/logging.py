import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_file_logging(log_dir: str, log_file: str, level_name: str = "INFO") -> Path:
    level = getattr(logging, level_name.upper(), logging.INFO)
    target_dir = Path(log_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    target_file = target_dir / log_file

    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s - %(message)s")
    root = logging.getLogger()
    root.setLevel(level)

    exists = any(
        isinstance(h, RotatingFileHandler) and getattr(h, "baseFilename", "") == str(target_file)
        for h in root.handlers
    )
    if not exists:
        handler = RotatingFileHandler(str(target_file), maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8")
        handler.setLevel(level)
        handler.setFormatter(formatter)
        root.addHandler(handler)

    return target_file
