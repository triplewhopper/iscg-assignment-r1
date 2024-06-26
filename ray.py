import taichi as ti
import taichi.math as tm
from typing import overload, Literal

MAX_RAYMARCH = 256
TMIN = 1e-3
TMAX = 2e3
PRECISION = 1e-4
@ti.dataclass
class Ray:
    ro: tm.vec3
    rd: tm.vec3

    @ti.func
    def at(self, t: ti.f32) -> tm.vec3:
        return self.ro + t * self.rd

@ti.dataclass
class Hit:
    dis: ti.f32
    normal: tm.vec3

@ti.func
def intersect(obj, ray):
    t = TMIN
    sdf_n = tm.vec3(0.0)
    i = 0
    while i < MAX_RAYMARCH:
        p = ray.ro + ray.rd * t
        d = obj.sdf(p)
        dis = ti.abs(d)
        if dis < 1e-4:
            sdf_n = sdf_normal(obj, p)
            break
        t += dis
        if t > TMAX:
            t = tm.inf
            break
        i += 1
    if i == MAX_RAYMARCH:
        t = tm.inf
        sdf_n.fill(0.0)
    return Hit(t, sdf_n)

@ti.dataclass
class Camera:
    pos: tm.vec3
    look_at: tm.vec3
    up: tm.vec3
    film: tm.vec2
    resolution: tm.vec2
    focal_length: ti.f32
    
    # @ti.func
    # def translate(self, delta: tm.vec3):
    #     self.pos += delta
    #     self.look_at += delta

    # @ti.func
    # def rotate(self, rot: tm.mat3):
    #     # self.up = rot @ self.up
    #     self.look_at = rot @ (self.look_at - self.pos) + self.pos

    @ti.func
    def get_ortho_basis(self):
        w = tm.normalize(self.pos - self.look_at)
        u = tm.normalize(self.up.cross(w))
        v = tm.normalize(w.cross(u))
        return u, v, w, self.pos
    
    @ti.func
    def _shoot_ray(self, pixel: tm.vec3) -> 'Ray':
        u, v, w, o = self.get_ortho_basis()
        d = pixel.x * u + pixel.y * v + pixel.z * w
        return Ray(o, -tm.normalize(d))
    
    @ti.func
    def shoot_ray_from_screen(self, pixelXY: tm.vec2):
        x = self.film.x * (1.0 - 2.0 * (pixelXY.x + 0.5) / self.resolution.x)
        y = self.film.y * (1.0 - 2.0 * (pixelXY.y + 0.5) / self.resolution.y)
        pixel = tm.vec3(x, y, self.focal_length)
        return self._shoot_ray(pixel)


@ti.dataclass
class Sphere:
    center: tm.vec3
    radius: ti.f32
    material: ti.i32
    # def __init__(self, center: tm.vec3, radius: ti.f32) -> None:
    #     assert radius > 0.0
    #     self.center = center
    #     self.radius = radius

    @ti.func
    def sdf(self, pos):
        return tm.length(pos - self.center) - self.radius
    
    intersect = intersect
    

@ti.dataclass
class Plane:
    normal: tm.vec3
    offset: ti.f32
    material: ti.i32

    @ti.func
    def sdf(self, pos: tm.vec3) -> ti.f32:
        return pos.dot(self.normal) - self.offset
    
    intersect = intersect
    
@ti.dataclass
class Box:
    center: tm.vec3
    size: tm.vec3
    material: ti.i32

    @ti.func
    def sdf(self, pos: tm.vec3) -> ti.f32:
        q = ti.abs(pos - self.center) - self.size
        return tm.length(tm.max(q, 0.0)) + tm.min(tm.max(q.x, tm.max(q.y, q.z)), 0.0)
    
    intersect = intersect
    
@ti.dataclass
class Torus:
    center: tm.vec3
    normal: tm.vec3
    major_radius: ti.f32
    minor_radius: ti.f32
    material: ti.i32

    @ti.func
    def sdf(self, pos: tm.vec3) -> ti.f32:
        pos = pos - self.center
        v = tm.vec3(0, 1, 0).cross(self.normal)
        c = pos.dot(self.normal)
        v_plus = ti.Matrix([
            [0, -v.z, v.y],
            [v.z, 0, -v.x],
            [-v.y, v.x, 0]
        ], dt=ti.f32)
        pos = pos + v_plus @ pos + v_plus @ v_plus / (1.0 + c) @ pos
        q = tm.vec2(tm.length(pos.xz) - self.major_radius, pos.y)
        return tm.length(q) - self.minor_radius
    
    intersect = intersect

@ti.data_oriented
class Intersection:
    def __init__(self, *objs, material: ti.i32=0) -> None:
        assert len(objs) > 0
        assert material or len(set(o.material for o in objs)) == 1
        self.objs = list(objs)
        if material == 0:
            material = objs[0].material

    @ti.func
    def sdf(self, pos: tm.vec3) -> ti.f32:
        d = tm.inf
        for i in ti.static(range(len(self.objs))):
            d = tm.min(d, self.objs[i].sdf(pos))
        return d

@ti.func
def sdf_normal(obj, p) -> tm.vec3:
    k = tm.vec2(1.0, -1.0) / tm.sqrt(3.0)
    return tm.normalize(
        k.xyy * obj.sdf(p + k.xyy * 1e-4) +
        k.yyx * obj.sdf(p + k.yyx * 1e-4) + 
        k.yxy * obj.sdf(p + k.yxy * 1e-4) +
        k.xxx * obj.sdf(p + k.xxx * 1e-4)
    )

@ti.data_oriented
class Scene:
    def __init__(self):
        self.spheres = Sphere.field(shape=100)
        self.planes = Plane.field(shape=100)
        self.boxes = Box.field(shape=100)
        self.toruses = Torus.field(shape=100)
        self.num_sphere = ti.field(ti.i32, shape=())
        self.num_plane = ti.field(ti.i32, shape=())
        self.num_box = ti.field(ti.i32, shape=())
        self.num_torus = ti.field(ti.i32, shape=())
        self.clear()

    @ti.kernel
    def add_sphere(self, center: tm.vec3, radius: ti.f32, material: ti.i32):
        assert radius > 0.0
        self.spheres[self.num_sphere[None]].center = center
        self.spheres[self.num_sphere[None]].radius = radius
        self.spheres[self.num_sphere[None]].material = material
        self.num_sphere[None] += 1

    @ti.kernel
    def add_plane(self, normal: tm.vec3, offset: ti.f32, material: ti.i32):
        assert normal.norm_sqr() == 1.0
        self.planes[self.num_plane[None]].normal = normal
        self.planes[self.num_plane[None]].offset = offset
        self.planes[self.num_plane[None]].material = material
        self.num_plane[None] += 1

    @ti.kernel
    def add_box(self, center: tm.vec3, size: tm.vec3, material: ti.i32):
        self.boxes[self.num_box[None]].center = center
        self.boxes[self.num_box[None]].size = size
        self.boxes[self.num_box[None]].material = material
        self.num_box[None] += 1
    @ti.kernel
    def add_torus(self, center: tm.vec3, normal: tm.vec3, major_radius: ti.f32, minor_radius: ti.f32, material: ti.i32):
        assert normal.norm_sqr() == 1.0
        assert major_radius > minor_radius
        self.toruses[self.num_torus[None]].center = center
        self.toruses[self.num_torus[None]].normal = normal
        self.toruses[self.num_torus[None]].major_radius = major_radius
        self.toruses[self.num_torus[None]].minor_radius = minor_radius
        self.toruses[self.num_torus[None]].material = material
        self.num_torus[None] += 1
    
    def clear(self):
        self.num_sphere[None] = 0
        self.num_plane[None] = 0
        self.num_box[None] = 0
        self.num_torus[None] = 0
        

    @ti.func
    def intersect(self, ray):
        hit = Hit(tm.inf, tm.vec3(0.0))
        material = 0
        for upper_bound, primitives in ti.static(zip(
            [self.num_sphere[None], self.num_plane[None], self.num_box[None], self.num_torus[None]], 
            [self.spheres, self.planes, self.boxes, self.toruses])):
            for i in range(upper_bound):
                obj_ = primitives[i]
                hit_ = obj_.intersect(ray)
                if hit_.dis < hit.dis:
                    hit = hit_
                    material = obj_.material

        return hit, material
  
@ti.func
def normal_shade(ray: Ray, hit: Hit):
    return ti.abs(hit.normal)  

@ti.func
def checkerboard_shade(ray: Ray, hit: Hit):
    pos = ray.ro + ray.rd * hit.dis
    checkboad = (tm.mod(pos.x, 1.0) > 0.5) ^ (tm.mod(pos.z, 1.0) > 0.5)
    return tm.vec3(0.0) if checkboad else tm.vec3(1.0)

@ti.func
def shade(ray, hit, material: ti.i32):
    s = tm.vec3(0.0)
    if material == 1:
        s = normal_shade(ray, hit)
    elif material == 2:
        s = checkerboard_shade(ray, hit)
    return s

@ti.data_oriented
class Renderer:
    def __init__(self, scene: Scene, camera: Camera, width: ti.i32, height: ti.i32, fov: ti.f32, output_field):
        self.scene = scene
        self.camera = camera
        self.width = width
        self.height = height
        self.output_field = output_field
        self.aspect_ratio = width / height
        self.fov = fov
        assert self.aspect_ratio > 0.0

    @ti.kernel
    def render(self, camera_position: tm.vec3, camera_lookat: tm.vec3, camera_up: tm.vec3):
            # fov: ti.f32, width: ti.f32, height: ti.f32, 
            # scene: ti.template(), output_field: ti.template()):
        aspect_ratio = self.aspect_ratio
        assert aspect_ratio > 0.0 
        fov_radian = tm.radians(self.fov)
        film_diagonal = 2.0 * ti.tan(fov_radian / 2.0)
        film_height = film_diagonal / ti.sqrt(1.0 + aspect_ratio**2)
        film_width = film_height * aspect_ratio
        camera = Camera(
            pos=camera_position, 
            look_at=camera_lookat, 
            up=camera_up, 
            film=tm.vec2(film_width, film_height), 
            resolution=tm.vec2(self.width, self.height), 
            focal_length=1.0)
        
        for I in ti.grouped(self.output_field):
            ray = camera.shoot_ray_from_screen(I)
            # print(f'{I=}, {ray.ro=}, {ray.rd=}')
            hit, material = self.scene.intersect(ray)
            if not tm.isinf(hit.dis):
                self.output_field[I] = shade(ray, hit, material)
            else:
                self.output_field[I] = tm.vec3(0.0)