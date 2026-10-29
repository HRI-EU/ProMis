# ProMis GUI

This folder holds the frontend of the ProMis GUI, a React app in [frontend](./frontend).
The backend is part of the Python package, in [promis/gui](../promis/gui).
For how to use the GUI, see the [GUI documentation](https://hri-eu.github.io/ProMis/gui.html).

## Development

The backend serves the built frontend, so the GUI is developed by building the frontend and starting the backend:

```bash
# Build the frontend and copy it, together with the default data, into the Python package
bash scripts/build_gui.sh

# Start the backend, then open http://localhost:8000/gui
promis_gui
```

`scripts/build_gui.sh` copies the build into `promis/gui/frontend` and the default data from `resources/data` into `promis/gui/data`.
Both are generated and ignored by git; the release workflow runs the script before building the Python package.
