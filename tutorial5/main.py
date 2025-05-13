print("Starting up...")

import functools
import math
import random

from pyscript import document, window
from pyscript import config
from pyscript.ffi import create_proxy

from libthree import THREE, new, call, uniforms, clear, dataclass, field
from libthree import SceneBase, TextGeometry, FontLoader

from js import Float32Array

MICROPYTHON = config["type"] == "mpy"

if not MICROPYTHON:
    import pyodide_js

    pyodide_js.setDebug(True)
    print = functools.partial(print, flush=True)


@dataclass
class Comparison(SceneBase):
    point_light: THREE.PointLight = field(init=False)
    spot_light: THREE.SpotLight = field(init=False)
    plane: THREE.Mesh = field(init=False)
    box: THREE.Mesh = field(init=False)
    cone: THREE.Mesh = field(init=False)
    text: THREE.Mesh = field(init=False)

    def __post_init__(self):
        super().__post_init__()
        self.point_light = new(THREE.PointLight, 0xFFFFFF, 1, 0, 0.1)
        self.point_light.name = "PointLight"
        self.camera.add(self.point_light)

        self.spot_light = new(THREE.SpotLight, 0xFFFFFF, 100, 20, math.pi / 4)
        self.spot_light.name = "SpotLight"
        self.spot_light.penumbra = 1
        self.spot_light.castShadow = True
        self.spot_light.position.set(0, 12, -30)
        self.spot_light.target.position.set(0, 0, -30)
        self.camera.add(self.spot_light)
        self.camera.add(self.spot_light.target)

        plane_geo = new(THREE.PlaneGeometry, 5, 5, 1, 1)
        plane_mat = new(
            THREE.MeshStandardMaterial,
            color=0xFFFF00,
            roughness=0,
            metalness=0.3,
            wireframe=False,
        )
        self.plane = new(THREE.Mesh, plane_geo, plane_mat)
        self.plane.receiveShadow = True
        self.plane.castShadow = True
        self.plane.position.set(-10, 0, 0)
        self.plane.rotation.x = -math.pi / 5
        self.scene.add(self.plane)

        box_geo = new(THREE.BoxGeometry, 5, 5, 5, 3, 3, 3)
        box_mat = new(
            THREE.MeshStandardMaterial,
            color=0x00FFFF,
            roughness=0,
            metalness=0.3,
            transparent=True,
            opacity=0.5,
            wireframe=False,
            side=THREE.DoubleSide,
        )
        self.box = new(THREE.Mesh, box_geo, box_mat)
        self.box.receiveShadow = True
        self.box.castShadow = True
        self.box.position.set(0, 0, 0)
        self.box.rotation.x = -math.pi / 4
        self.box.rotation.z = -math.pi / 4
        self.scene.add(self.box)

        cone_geo = new(THREE.ConeGeometry, 2, 10, 4, 1)
        cone_mat = new(
            THREE.MeshStandardMaterial,
            color=0xFF00FF,
            roughness=1,
            metalness=0,
            wireframe=False,
            side=THREE.DoubleSide,
        )
        self.cone = new(THREE.Mesh, cone_geo, cone_mat)
        self.cone.receiveShadow = True
        self.cone.castShadow = True
        self.cone.position.set(10, 0, 0)
        self.cone.rotation.x = -math.pi / 5
        self.scene.add(self.cone)

        fonts = new(FontLoader)
        fonts.load(
            "bundle/three.js/examples/fonts/helvetiker_regular.typeface.json",
            self._on_font_load,
        )

    def _on_font_load(self, font):
        text_geo = new(
            TextGeometry,
            "PyCon US!",
            font=font,
            size=7,
            depth=2,
            curveSegments=12,
            bevelEnabled=True,
            bevelThickness=0.25,
            bevelSize=0.25,
            bevelSegments=5,
        )
        text_mat = new(
            THREE.MeshStandardMaterial,
            color=0x00FF00,
            roughness=0,
            metalness=0.8,
            wireframe=False,
            side=THREE.DoubleSide,
        )
        self.text = new(THREE.Mesh, text_geo, text_mat)
        self.text.receiveShadow = True
        self.text.castShadow = True
        self.text.position.set(-22, 0, -10)
        self.scene.add(self.text)


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
        pass


document.addEventListener("keydown", on_key_down)

app = Comparison()
app.start()

import code

code.interact()
