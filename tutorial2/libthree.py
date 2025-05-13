try:
    from dataclasses import dataclass, field
except ImportError:
    from udataclasses import dataclass, field

from pyscript import document, window, config

# JS: import * as THREE from 'three';
from pyscript.js_modules import three as THREE

# JS: import { OrbitControls } from 'oc';
from pyscript.js_modules.oc import OrbitControls

# JS: import Stats from 'stats';
from pyscript.js_modules.stats_gl import default as StatsGL
from pyscript.js_modules import uniforms

from pyscript.ffi import to_js, create_proxy

MICROPYTHON = config["type"] == "mpy"

if MICROPYTHON:
    def new(obj, *args, **kwargs):
        return obj.new(*args, kwargs) if kwargs else obj.new(*args)
    def call(obj, *args, **kwargs):
        return obj(*args, kwargs) if kwargs else obj(*args)
else:
    def new(obj, *args, **kwargs):
        return obj.new(*args, **kwargs)
    def call(obj, *args, **kwargs):
        return obj(*args, **kwargs)

def get_renderer():
    renderer = new(THREE.WebGLRenderer, antialias=True)
    renderer.setSize(window.innerWidth, window.innerHeight)
    renderer.setPixelRatio(window.devicePixelRatio)
    # renderer.setClearColor(0xC39AE5)
    
    pyterms = list(document.getElementsByTagName("py-terminal"))
    if pyterms:
        pyterm = pyterms[0]
        pyterm.parentNode.removeChild(pyterm)
        document.getElementById("pyterm").appendChild(pyterm)

    document.getElementById("threejs").appendChild(renderer.domElement)
    initial = {0: "115px", 1: "calc(100vh - 120px)"}

    @create_proxy
    def split_element_style(dimension, size, gutter_size, index):
        if index in initial:
            result = {dimension: initial.pop(index)}
        else:
            result = {dimension: f"calc({int(size)}vh - {gutter_size}px)"}
        return to_js(result)

    call(
        window.Split,
        ["#pyterm", "#threejs"],
        direction="vertical",
        elementStyle=split_element_style,
        minSize=0,
        maxSize=to_js([120, 10000]),
    )       
    return renderer

def get_ortho_camera(view_size):
    aspect_ratio = window.innerWidth / window.innerHeight
    camera = new(
        THREE.OrthographicCamera,
        -view_size * aspect_ratio,  # Left
        view_size * aspect_ratio,   # Right
        view_size,                  # Top
        -view_size,                 # Bottom
        -100,                       # Near plane
        1000,                       # Far plane
    )
    camera.position.set(0, 0, 10)
    return camera

def get_perspective_camera():
    aspect_ratio = window.innerWidth / window.innerHeight
    camera = new(
        THREE.PerspectiveCamera,
        45,             # fov
        aspect_ratio,
        0.25,           # near plane
        300,            # far plane
    )
    camera.position.set(0, 0, 30)
    return camera

def get_controls(camera, renderer):
    controls = new(OrbitControls, camera, renderer.domElement)
    controls.minDistance = 1
    controls.maxDistance = 100
    controls.target.set(0, 0, 0)
    controls.saveState()
    return controls

def get_stats_gl(renderer):
    stats = new(StatsGL, trackGPU=True, horizontal=False)
    stats.init(renderer)
    stats.dom.style.removeProperty("left")
    stats.dom.style.right = "90px"
    document.getElementById("stats").appendChild(stats.dom)
    return stats

def clear():
    # toggle stats and terminal?
    stats_style = document.getElementById("stats").style
    if stats_style.display == "none":
        # turn stuff back on
        stats_style.removeProperty("display")
        document.getElementById("pyterm").style.height = "115px"
        document.getElementById("threejs").style.height = "calc(100vh - 120px)"
        for e in document.getElementsByClassName("gutter"):
            e.style.removeProperty("display")    
        for e in document.getElementsByClassName("xterm-helper-textarea"):
            e.focus()
            break
        return

    # no longer focus on xterm
    document.activeElement.blur()
    # hide stats
    document.getElementById("stats").style.display = "none"
    # hide pyterm and split gutter
    document.getElementById("pyterm").style.height = "0vh"
    document.getElementById("threejs").style.height = "100vh"
    for e in document.getElementsByClassName("gutter"):
        e.style.display = "none"
    # hide ltk ad
    for e in document.getElementsByClassName("ltk-built-with"):
        e.style.display = "none"
    # hide pyscript ad
    for e in document.getElementsByTagName("div"):
        style = e.getAttribute("style")
        if style and style.startswith("z-index:999"):
            e.style.display = "none"
    for e in document.getElementsByTagName("svg"):
        style = e.getAttribute("style")
        if style and style.startswith("z-index:999"):
            e.style.display = "none"