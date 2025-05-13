print("Starting up...")

import functools
import random

from pyscript import document, window
from pyscript import config
from pyscript.ffi import create_proxy

from libthree import THREE, new, call
from libthree import get_renderer, get_perspective_camera, get_controls
from libthree import get_stats_gl

MICROPYTHON = config["type"] == "mpy"

if not MICROPYTHON:
    import pyodide_js
    pyodide_js.setDebug(True)
    print = functools.partial(print, flush=True)

scene = new(THREE.Scene)

view_size = 50
renderer = get_renderer()
camera = get_perspective_camera()
controls = get_controls(camera, renderer)

light = new(THREE.AmbientLight, 0xffffff, 2.0)
scene.add(light)

grid_size_x = 10
grid_size_y = 10
spacing = 1.5
spheres = []
grid_center_x = grid_size_x * spacing / 2
grid_center_y = grid_size_y * spacing / 2

print("Computing shapes", end="...")
for x in range(grid_size_x):
    print(end=".")
    for y in range(grid_size_y):
        geometry = new(THREE.SphereGeometry, 0.3, 16, 16)
        material = new(THREE.MeshStandardMaterial, color=0x800080)
        sphere = new(THREE.Mesh, geometry, material)
        sphere.position.set(
            x * spacing - grid_center_x,
            y * spacing - grid_center_y,
            0
        )
        scene.add(sphere)
        spheres.append(sphere)
print("done!")

@create_proxy
def on_window_resize(event):
    aspect_ratio = window.innerWidth / window.innerHeight
    if camera.type == "OrthographicCamera":
        camera.left = -view_size * aspect_ratio
        camera.right = view_size * aspect_ratio
        camera.top = view_size
        camera.bottom = -view_size
        camera.updateProjectionMatrix()
    elif camera.type == "PerspectiveCamera":
        camera.aspect = window.innerWidth / window.innerHeight
        camera.updateProjectionMatrix()
    else:
        raise ValueError("Unknown camera type")
    renderer.setSize(window.innerWidth, window.innerHeight)

window.addEventListener("resize", on_window_resize)

@create_proxy
def animate(now=0.0):
    random.choice(spheres).material.color.setRGB(
        random.random(),
        random.random(),
        random.random(),
    )
    controls.update()
    renderer.render(scene, camera)
    stats_gl.update()

stats_gl = get_stats_gl(renderer)
renderer.setAnimationLoop(animate)

import code; code.interact()
