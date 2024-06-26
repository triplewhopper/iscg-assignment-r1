import taichi as ti
import taichi.math as tm
import time
from collections.abc import Sequence
from ray import Renderer, Camera, Ray, Hit, Sphere, Plane, Scene, Box, Torus
import taichi as ti
import numpy as np

ti.init(arch=ti.cpu)

width, height = 1280, 720
rgb_image = ti.Vector.field(n=3, dtype=ti.f32, shape=(width, height))
window = ti.ui.Window('iscg2024-assignment-r1', (width, height), vsync=True, fps_limit=60)
canvas = window.get_canvas()
gui = window.get_gui()
camera = ti.ui.Camera()
camera.position(0, 1, 1)
camera.lookat(0, 0, 0)

scene = Scene()
scene.add_sphere(tm.vec3(1.0, 0.0, -1.0), 0.5, 1)
scene.add_plane(tm.vec3(0, 1, 0), 0, 2)
scene.add_box(tm.vec3(0.0, 0.0, -1.0), tm.vec3(0.5, 0.5, 0.5), 1)
scene.add_torus(tm.vec3(-1.0, 0.0, -1.0), tm.vec3(0.0, 1.0, 0.0), 0.3, 0.05, 1)
renderer = Renderer(scene, camera, width, height, 60.0, rgb_image)

while window.running:
    camera.track_user_inputs(window, movement_speed=0.03, yaw_speed=0.5, pitch_speed=0.5, hold_key=ti.ui.RMB)
    # render(camera.curr_position, camera.curr_lookat, camera.curr_up, 60.0, width, height, scene, rgb_image)
    renderer.render(camera.curr_position, camera.curr_lookat, camera.curr_up)
    canvas.set_image(rgb_image)
    with gui.sub_window("Sub Window", x=0., y=0., width=0.3, height=0.5) as sub_gui:
        sub_gui.text(f'camera position: ({camera.curr_position.x:.2f}, {camera.curr_position.y:.2f}, {camera.curr_position.z:.2f})')
        sub_gui.text(f'camera lookat: ({camera.curr_lookat.x:.2f}, {camera.curr_lookat.y:.2f}, {camera.curr_lookat.z:.2f})')
        if sub_gui.button('save screenshot'):
            ti.tools.imwrite(rgb_image, 'screenshot.png')
            print('screenshot saved')
        for i in range(scene.num_sphere[None]):
            sphere = scene.spheres[i]
            sphere.center.x = sub_gui.slider_float(f"Sphere {i} center x", sphere.center.x, -1.0, 1.0)
            sphere.center.y = sub_gui.slider_float(f"Sphere {i} center y", sphere.center.y, -1.0, 1.0)
            sphere.center.z = sub_gui.slider_float(f"Sphere {i} center z", sphere.center.z, -1.0, 1.0)
            sphere.radius = sub_gui.slider_float(f"Sphere {i} radius", sphere.radius, 0.0, 1.0)
        for i in range(scene.num_box[None]):
            box = scene.boxes[i]
            box.center.x = sub_gui.slider_float(f"Box {i} center x", box.center.x, -1.0, 1.0)
            box.center.y = sub_gui.slider_float(f"Box {i} center y", box.center.y, -1.0, 1.0)
            box.center.z = sub_gui.slider_float(f"Box {i} center z", box.center.z, -1.0, 1.0)
            box.size.x = sub_gui.slider_float(f"Box {i} size x", box.size.x, 0.0, 1.0)
            box.size.y = sub_gui.slider_float(f"Box {i} size y", box.size.y, 0.0, 1.0)
            box.size.z = sub_gui.slider_float(f"Box {i} size z", box.size.z, 0.0, 1.0)
        for i in range(scene.num_torus[None]):
            torus = scene.toruses[i]
            torus.center.x = sub_gui.slider_float(f"Torus {i} center x", torus.center.x, -1.0, 1.0)
            torus.center.y = sub_gui.slider_float(f"Torus {i} center y", torus.center.y, -1.0, 1.0)
            torus.center.z = sub_gui.slider_float(f"Torus {i} center z", torus.center.z, -1.0, 1.0)
            torus.major_radius = sub_gui.slider_float(f"Torus {i} major radius", torus.major_radius, 0.0, 1.0)
            torus.minor_radius = sub_gui.slider_float(f"Torus {i} minor radius", torus.minor_radius, 0.0, torus.major_radius)
    window.show()

