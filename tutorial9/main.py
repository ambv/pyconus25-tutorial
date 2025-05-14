from __future__ import annotations
print("Starting up...")

import asyncio
import functools
import math
import random

from pyscript import document
from pyscript import config
from pyscript.ffi import create_proxy

from libthree import THREE, new, clear, dataclass, field
from libthree import SceneBase, GLTFLoader, get_loading_manager

MICROPYTHON = config["type"] == "mpy"

if not MICROPYTHON:
    import pyodide_js

    pyodide_js.setDebug(True)
    print = functools.partial(print, flush=True)


@dataclass
class GLTFModels(SceneBase):
    point_light: THREE.PointLight = field(init=False)
    spot_light: THREE.SpotLight = field(init=False)
    python_logo: THREE.Mesh | None = field(default=None)
    flamingo: THREE.Mesh | None = field(default=None)
    flamingo_clips: list[THREE.AnimationClip] | None = field(default=None)
    flamingo_animation: THREE.AnimationMixer | None = field(default=None)
    loading_manager: THREE.LoadingManager = field(init=False)
    loaded_event: asyncio.Event = field(init=False)
    texture_loader: THREE.TextureLoader = field(init=False)
    gltf_loader: GLTFLoader = field(init=False)

    def __post_init__(self):
        super().__post_init__()

        self.loading_manager, self.loaded_event = get_loading_manager()
        self.texture_loader = new(THREE.TextureLoader, self.loading_manager)
        self.gltf_loader = new(GLTFLoader, self.loading_manager)

        self.point_light = new(THREE.PointLight, 0xFFFFFF, 10, 100, 0.1)
        self.point_light.name = "PointLight"
        self.point_light.position.set(10, 10, 2)
        self.scene.add(self.point_light)

        self.spot_light = new(THREE.SpotLight, 0xFFFFFF, 100, 40, math.pi / 4)
        self.spot_light.name = "SpotLight"
        self.spot_light.penumbra = 1
        self.spot_light.castShadow = True
        self.spot_light.map = self.texture_loader.load("assets/water.jpg")

        self.spot_light.position.set(0, 12, -30)
        self.spot_light.target.position.set(0, 0, -30)
        self.camera.add(self.spot_light)
        self.camera.add(self.spot_light.target)

        self.gltf_loader.load(
            'assets/python/scene.gltf',
            create_proxy(self.python_logo_callback),
        )

        self.gltf_loader.load(
            'assets/flamingo.glb',
            create_proxy(self.flamingo_callback),
        )

        self.controls._dollyIn(2)

    async def python_logo_callback(self, gltf, arg=None):
        self.python_logo = gltf.scene
        self.python_logo.scale.set(0.2, 0.2, 0.2)
        self.python_logo.name = "Python logo"
        await self.renderer.compileAsync(self.python_logo, self.camera, self.scene)
        self.scene.add(self.python_logo)

    async def flamingo_callback(self, gltf, arg=None):
        self.flamingo = gltf.scene
        self.flamingo.scale.set(0.1, 0.1, 0.1)
        self.flamingo.position.set(20, 0, 0)
        self.flamingo.name = "Flamingo"
        await self.renderer.compileAsync(self.flamingo, self.camera, self.scene)
        self.flamingo_clips = gltf.animations
        self.flamingo_animation = new(THREE.AnimationMixer, self.flamingo)
        action = self.flamingo_animation.clipAction(self.flamingo_clips[0])
        action.play()
        self.scene.add(self.flamingo)
    
    def animate(self, now, delta):
        if self.python_logo:
            self.python_logo.rotation.x = now / 1000
            self.python_logo.rotation.y = now / 2000
        if self.flamingo_animation:
            self.flamingo_animation.update(delta)                


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
            app.python_logo.visible = not app.python_logo.visible
            app.black_logo.visible = not app.black_logo.visible


document.addEventListener("keydown", on_key_down)

app = GLTFModels()

await app.loaded_event.wait()

app.start()
