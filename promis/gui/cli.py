import uvicorn


def main() -> None:
    uvicorn.run("promis.gui.main:app", port=8000, log_level="info")
