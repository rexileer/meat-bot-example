import logging

from data.config import env

logging.basicConfig(
    format="[%(asctime)s] [%(filename)s - LINE:%(lineno)d] %(message)s",
    level=logging.DEBUG,
    handlers=(
        [
            logging.StreamHandler(),
            logging.FileHandler(f"{env.APP_DIR}/debug.log", encoding="utf-8"),
        ]
    ),
)
