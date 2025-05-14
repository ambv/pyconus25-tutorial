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
    python_logo: THREE.Mesh = field(init=False)
    black_logo: THREE.Mesh = field(init=False)
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
        self.point_light.position.set(10, 10, 0)
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
            'assets/black.glb',
            create_proxy(self.black_logo_callback),
        )

    async def python_logo_callback(self, gltf, arg=None):
        self.python_logo = gltf.scene
        self.python_logo.scale.set(0.2, 0.2, 0.2)
        self.python_logo.name = "Python logo"
        await self.renderer.compileAsync(self.python_logo, self.camera, self.scene)
        self.scene.add(self.python_logo)

    async def black_logo_callback(self, gltf, arg=None):
        self.black_logo = gltf.scene
        self.black_logo.scale.set(20, 20, 20)
        self.black_logo.name = "Black logo"
        await self.renderer.compileAsync(self.black_logo, self.camera, self.scene)
        material = THREE.MeshStandardMaterial.new( 
            color=0xffffff,
            metalness=0.8,
            roughness=0,
        ) 

        def set_material(o):
            if hasattr(o, "material"):
                o.material = material
                o.receiveShadow = True
                o.castShadow = True
        
        self.black_logo.traverse(set_material)
        self.black_logo.visible = False
        self.scene.add(self.black_logo)


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
