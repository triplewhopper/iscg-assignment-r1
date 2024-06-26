# iscg2024-assignment-r1
This is the repository for the rendering part 1 assignment for the lecture Computer Graphics at the University of Tokyo, 2024 Spring Semester.
## Features
- [x] Sphere Tracing (Ray Marching)
    - [x] Sphere
    - [x] Plane
    - [x] Box
    - [x] Torus

- [x] Interactive Camera
    `W`: Move forward
    `S`: Move backward
    `A`: Move left
    `D`: Move right
    `Q`: Move up
    `E`: Move down
    Press and hold `Right Mouse Button` to rotate the camera

- [x] Panel for changing size of the shapes
- [x] Shading
    - [x] Normal Shading
    - [x] Checkerboard Shading

## How to run
Python 3.10 is favored for this project. To run the project, follow the steps below:
1. `git clone`
2. `cd iscg2024-assignment-r1`
3. `pip install -r requirements.txt`
4. `python main.py`

If the FPS is low, try changing line 9 in `main.py`:
from 
```python
    ti.init(arch=ti.cpu)
```
to
```python
    ti.init(arch=ti.gpu)
```
## Demo
<video id="video" controls="" preload="none" poster="封面">
      <source id="mp4" src="./demo.mp4" type="video/mp4">
</video>