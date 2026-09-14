import logging, sys

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    # Reduce noisy uvicorn access
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

logger = logging.getLogger("smcpe")
