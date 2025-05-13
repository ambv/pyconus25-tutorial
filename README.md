# Source code for the PyScript + WebGL tutorial at PyCon US 2025

![Rotating 3D logo](_index/python-logo-loop.gif)

The `bundle/` directory is a self-contained, well, bundle of all
dependencies you need to run a PyScript application with Three.js
and Stats-gl. This allows the lessons here to run offline by using
the included `server.py` script. Just run it with
[uv](https://docs.astral.sh/uv/):

```
❯ uv run server.py .
Installed 7 packages in 7ms
INFO:     Started server process [67711]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:5005 (Press CTRL+C to quit)
```

If you insist on running your own Python virtual env without `uv`,
see the dependencies you need to install in the comment on top of
`server.py`.

# Copyright
All source code in `tutorial*/` written by Łukasz Langa unless otherwise
noted in the file. All that source is licensed as public domain under
[CC0](https://creativecommons.org/public-domain/cc0/).

Assets either my own or taken directly from Three.js examples, moved
to per-lesson `assets/` purely for convenience.
