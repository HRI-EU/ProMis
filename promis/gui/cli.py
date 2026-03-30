import argparse
import uvicorn
from promis.gui.main import app


def main() -> None:
    parser = argparse.ArgumentParser(description="ProMis Web GUI")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to (default: 8000)")
    args = parser.parse_args()

    app.state.host = args.host
    app.state.port = args.port

    uvicorn.run(app, host=args.host, port=args.port, log_level="error")
