print("Starting up...")

import functools
import math
import random

from pyscript import document
from pyscript import config
from pyscript.ffi import create_proxy

from libthree import THREE, new, call, uniforms, clear, dataclass, field
from libthree import SceneBase, get_ortho_camera

from perlin import perlin3

MICROPYTHON = config["type"] == "mpy"

if not MICROPYTHON:
    import pyodide_js

    pyodide_js.setDebug(True)
    print = functools.partial(print, flush=True)


@dataclass
class Voxels(SceneBase):
    point_light: THREE.PointLight = field(init=False)
    spot_light: THREE.SpotLight = field(init=False)
    texture_loader: THREE.TextureLoader = field(default=new(THREE.TextureLoader))
    grid_h: int = field(default=100)
    grid_w: int = field(default=100)
    grid_scale: int = field(default=10)
    grid: list[THREE.Mesh | None] = field(init=False)
    height_map: list[float] = field(init=False)

    def __post_init__(self):
        super().__post_init__()

        grid_center_x = self.grid_w / 2
        grid_center_y = self.grid_h / 2

        self.scene.fog = new(THREE.Fog, 0x000000, 10, 100)

        self.point_light = new(THREE.PointLight, 0xFFFFFF, 10, 100, 0.1)
        self.point_light.name = "PointLight"
        self.point_light.position.set(0, 10, 0)
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

        self.grid = [None] * (self.grid_w * self.grid_h)
        self.height_map = [0.0] * (self.grid_w * self.grid_h)
        self.update_height_map(self.grid_scale * random.random())

        box_geo = new(THREE.BoxGeometry, 1, 1, 1)
        box_mat_snow = new(
            THREE.MeshStandardMaterial,
            color=0xffffff,
            roughness=0,
            metalness=0.5,
        )
        box_mat_hill = new(
            THREE.MeshStandardMaterial,
            color=0x8B4513,
            roughness=1,
            metalness=0,
        )
        box_mat_land = new(
            THREE.MeshStandardMaterial,
            color=0x008000,
            roughness=1,
            metalness=0,
        )
        box_mat_beach = new(
            THREE.MeshStandardMaterial,
            color=0xffff00,
            roughness=1,
            metalness=0,
        )
        box_mat_water = new(
            THREE.MeshStandardMaterial,
            color=0x0000FF,
            roughness=0,
            metalness=0,
            wireframe=False,
            transparent=True,
            alphaMap=self.texture_loader.load('assets/water.jpg'),
        )
        for y in range(0, self.grid_h):
            for x in range(0, self.grid_w):
                i = y * self.grid_w + x
                z = self.grid_scale * self.height_map[i]
                if z > 3.5:
                    mat = box_mat_snow
                elif z > 2.5:
                    mat = box_mat_hill
                elif z > 0:
                    mat = box_mat_land
                elif z > -0.5:
                    mat = box_mat_beach
                else:
                    mat = box_mat_water
                box = new(THREE.Mesh, box_geo, mat)
                box.position.set(x - grid_center_x, z, y - grid_center_y)
                self.grid[i] = box
                self.scene.add(box)
        
        self.controls._rotateLeft(math.pi / 4)
        self.controls._rotateUp(math.pi / 4)

    def update_height_map(self, z):
        i = 0
        noise_factor = 500
        for y in range(0, self.grid_h * self.grid_scale, self.grid_scale):
            for x in range(0, self.grid_w * self.grid_scale, self.grid_scale):
                # 3 octaves of noise
                n = perlin3(x/noise_factor, y/noise_factor, z)
                n += 0.50 * perlin3(2*x/noise_factor, 2*y/noise_factor, z)
                n += 0.25 * perlin3(4*x/noise_factor, 4*y/noise_factor, z)
                self.height_map[i] = n
                i += 1


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

view_size = 50
app = Voxels(camera=get_ortho_camera(view_size), view_size=view_size)
app.start()

import code

code.interact()
