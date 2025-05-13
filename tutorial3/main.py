print("Starting up...")

import functools
import math
import random

from pyscript import document, window
from pyscript import config
from pyscript.ffi import create_proxy

from libthree import THREE, new, call, uniforms, clear
from libthree import get_renderer, get_perspective_camera, get_controls
from libthree import get_stats_gl

MICROPYTHON = config["type"] == "mpy"

if not MICROPYTHON:
    import pyodide_js
    pyodide_js.setDebug(True)
    print = functools.partial(print, flush=True)


view_size = 50
renderer = get_renderer()
camera = get_perspective_camera()
controls = get_controls(camera, renderer)

def make_scene_grid():
    scene = new(THREE.Scene)
    light = new(THREE.DirectionalLight, 0xffffff, 2.0)
    light.name = "DirLight"
    light.position.set(0, 10, 0)
    light.target.position.set(-5, 0, 0)
    dlh = new(THREE.DirectionalLightHelper, light)
    scene.add(light)
    scene.add(dlh)
    
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
            geometry = new(THREE.SphereGeometry, x/grid_size_x * 0.5, 16, 16)
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
    return scene, spheres, dlh

def make_scene_knot():
    scene = new(THREE.Scene)
    point = new(THREE.PointLight, 0xffffff, 1, 0, 0.1)
    point.name = "PointLight"
    scene.add(point)

    spot = new(THREE.SpotLight, 0xff0000, 100, 20, math.pi/8)
    spot.name = "SpotLight"
    spot.position.y = 12
    spot.target.position.set(0, 0, 0)

    scene.add(spot)
    scene.add(spot.target)
    slh = new(THREE.SpotLightHelper, spot)
    scene.add(slh)
    
    knot_geo = new(THREE.TorusKnotGeometry, 5, 0.5, 200, 20, 2, 3)
    knot_mat = new(THREE.MeshStandardMaterial, color=0xffffff, roughness=0, metalness=0)
    knot = new(THREE.Mesh, knot_geo, knot_mat)
    knot.position.set(0, 1, 2)
    scene.add(knot)
    return scene, knot, spot, slh


scene_grid, spheres, dlh = make_scene_grid()
scene_knot, knot, spot, slh = make_scene_knot()
active_scene = scene_grid


@create_proxy
def on_key_down(event):
    element = document.activeElement
    _class = element.getAttribute("class")
    in_xterm = element.tagName != "BODY" and _class and "xterm" in _class
    
    if event.code == "Backquote":
        # Screenshot mode.
        clear()
    elif not in_xterm:
        # Don't react to those bindings when typing code.
        if event.code == "Space":
            global active_scene
            if active_scene == scene_grid:
                active_scene = scene_knot
            else:
                active_scene = scene_grid
document.addEventListener("keydown", on_key_down)


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
    dlh.update()
    slh.update()
    renderer.render(active_scene, camera)
    stats_gl.update()

stats_gl = get_stats_gl(renderer)
renderer.setAnimationLoop(animate)

animate()
import code; code.interact()
