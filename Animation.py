# --- FINALIZED SCRIPT WITH ANIMATION, LIGHTING & RANDOM SEED ---

import bpy
import os
import math
import random
import uuid
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

# CONFIG
BLEND_DIR = r"C:/Users/ADMIN/PycharmProjects/dataset generator/blender"
OUTPUT_DIR = r"C:/Users/ADMIN/PycharmProjects/dataset generator/output dir/data3"
CLASS_NAME = 'propeller'
CLASS_ID = 0
IMG_SIZE = 512
TRAIN_RATIO = 0.8
FRAMES_PER_MODEL = 40
TOTAL_ROTATION = 360
ROTATION_SPEEDS = [0.5, 1.0, 1.5, 2.0]
ROTATION_AXES = ['X', 'Y', 'Z']
RANDOM_CAMERA_POSITIONS = True
MULTI_ENVIRONMENT = True
USE_BOUNDING_BOX = True
RANDOM_SEED = 42  # <- Consistency for repeatability

random.seed(RANDOM_SEED)

IMG_TRAIN = os.path.join(OUTPUT_DIR, 'images/train')
IMG_VAL = os.path.join(OUTPUT_DIR, 'images/val')
LBL_TRAIN = os.path.join(OUTPUT_DIR, 'labels/train')
LBL_VAL = os.path.join(OUTPUT_DIR, 'labels/val')
for d in [IMG_TRAIN, IMG_VAL, LBL_TRAIN, LBL_VAL]:
    os.makedirs(d, exist_ok=True)


def setup_camera(target=None):
    if 'Camera' in bpy.data.objects:
        cam = bpy.data.objects['Camera']
    else:
        cam_data = bpy.data.cameras.new("Camera")
        cam = bpy.data.objects.new("Camera", cam_data)
        bpy.context.collection.objects.link(cam)

    if RANDOM_CAMERA_POSITIONS:
        radius = random.uniform(3.0, 5.0)
        theta = random.uniform(0, 2 * math.pi)
        phi = random.uniform(math.radians(30), math.radians(150))
        cam.location = (
            radius * math.sin(phi) * math.cos(theta),
            radius * math.sin(phi) * math.sin(theta),
            radius * math.cos(phi)
        )
    else:
        cam.location = (0, -3.5, 1.5)

    look_at = target.location if target else Vector((0, 0, 0))
    cam.rotation_euler = (look_at - cam.location).to_track_quat('-Z', 'Y').to_euler()

    bpy.context.scene.camera = cam
    return cam


def setup_lighting():
    for obj in bpy.data.objects:
        if obj.type == 'LIGHT':
            bpy.data.objects.remove(obj, do_unlink=True)

    light_data = bpy.data.lights.new(name="KeyLight", type='SUN')
    light_data.energy = random.uniform(1.0, 2.0)
    light_obj = bpy.data.objects.new(name="KeyLight", object_data=light_data)
    light_obj.location = (5, -5, 5)
    bpy.context.collection.objects.link(light_obj)

    fill_data = bpy.data.lights.new(name="FillLight", type='POINT')
    fill_data.energy = 20
    fill_obj = bpy.data.objects.new(name="FillLight", object_data=fill_data)
    fill_obj.location = (-4, 2, 1)
    bpy.context.collection.objects.link(fill_obj)


def detect_rotation_axis(obj):
    dims = obj.dimensions
    smallest_idx = dims[:].index(min(dims))
    return ['X', 'Y', 'Z'][smallest_idx]


def setup_animation(obj, frames):
    axis = detect_rotation_axis(obj)
    if random.random() < 0.2:
        axis = random.choice(ROTATION_AXES)
    speed = random.choice(ROTATION_SPEEDS)

    obj.animation_data_clear()
    obj.animation_data_create()
    action = bpy.data.actions.new(name=f"{obj.name}_spin")
    obj.animation_data.action = action
    obj.rotation_mode = 'XYZ'
    axis_idx = {'X': 0, 'Y': 1, 'Z': 2}[axis]

    for frame in range(frames + 1):
        angle = math.radians((frame / frames) * TOTAL_ROTATION * speed)
        rot = [0, 0, 0]
        rot[axis_idx] = angle
        obj.rotation_euler = rot
        bpy.context.scene.frame_set(frame + 1)
        obj.keyframe_insert(data_path="rotation_euler", frame=frame + 1)

    for fcurve in obj.animation_data.action.fcurves:
        for kf in fcurve.keyframe_points:
            kf.interpolation = 'LINEAR'

    bpy.context.scene.frame_set(1)
    return axis, speed


def save_yolo_label(obj, cam, filepath):
    scene = bpy.context.scene
    mat_world = obj.matrix_world
    if USE_BOUNDING_BOX:
        corners = [mat_world @ Vector(corner) for corner in obj.bound_box]
    else:
        corners = [mat_world @ v.co for v in obj.data.vertices]

    coords_2d = [world_to_camera_view(scene, cam, c) for c in corners]
    coords_2d = [(p.x, p.y) for p in coords_2d if 0 <= p.x <= 1 and 0 <= p.y <= 1]
    if not coords_2d:
        return False

    x_vals = [p[0] for p in coords_2d]
    y_vals = [p[1] for p in coords_2d]
    x_min, x_max = min(x_vals), max(x_vals)
    y_min, y_max = min(y_vals), max(y_vals)
    x_center = (x_min + x_max) / 2
    y_center = (y_min + y_max) / 2
    w = x_max - x_min
    h = y_max - y_min
    if w < 0.05 or h < 0.05:
        return False

    with open(filepath, 'w') as f:
        f.write(f"{CLASS_ID} {x_center:.6f} {y_center:.6f} {w:.6f} {h:.6f}\n")
    return True


def main():
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.samples = 64
    blend_files = [f for f in os.listdir(BLEND_DIR) if f.endswith('.blend')]
    random.shuffle(blend_files)
    train_cutoff = int(len(blend_files) * TRAIN_RATIO)

    total_renders = 0
    total_labels = 0

    for i, blend_file in enumerate(blend_files):
        is_train = i < train_cutoff
        path = os.path.join(BLEND_DIR, blend_file)

        try:
            bpy.ops.wm.open_mainfile(filepath=path)
            objs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
            if not objs:
                print(f"⚠️ {blend_file}: No mesh objects.")
                continue

            uid = uuid.uuid4().hex[:8]
            for j, obj in enumerate(objs):
                cam = setup_camera(obj)
                setup_lighting()
                axis, speed = setup_animation(obj, FRAMES_PER_MODEL)

                for frame in range(1, FRAMES_PER_MODEL + 1):
                    bpy.context.scene.frame_set(frame)
                    img_name = f"{uid}_{CLASS_NAME}_{j}_f{frame:03d}_a{axis}_s{speed:.1f}.png"
                    img_path = os.path.join(IMG_TRAIN if is_train else IMG_VAL, img_name)
                    lbl_path = os.path.join(LBL_TRAIN if is_train else LBL_VAL, img_name.replace('.png', '.txt'))
                    bpy.context.scene.render.filepath = img_path
                    bpy.ops.render.render(write_still=True)
                    total_renders += 1
                    if save_yolo_label(obj, cam, lbl_path):
                        total_labels += 1

            print(f"✅ {blend_file} done.")
        except Exception as e:
            print(f"❌ {blend_file}: {e}")

    print(f"🎬 Done. Rendered: {total_renders}, Labeled: {total_labels}")


if __name__ == "__main__":
    main()
