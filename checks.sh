set -e
set -u
set -o pipefail

black promis
ruff check promis --fix
