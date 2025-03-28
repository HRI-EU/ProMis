from pathlib import Path

from flask import Flask

app = Flask(__name__)


@app.route("/")
def index():
    with (Path("examples") / "debug_keplergl.html").open() as f:
        return f.read()


if __name__ == "__main__":
    app.run(debug=True)
