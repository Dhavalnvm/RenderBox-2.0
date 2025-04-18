import bpy
import os
import math
import random
import uuid
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Euler, Vector

# ---------- CONFIG ----------
BLEND_DIR = r"C:/Users/Admin/Machine Learning/Propeller/blender"
OUTPUT_DIR = r"C:/Users/Admin/Machine Learning/Propeller/Output"
CLASS_NAME = 'propeller'
IMG_SIZE = 512
BUBBLE_COUNT = 80  # Reduced bubble count to make the object clearer

# Video settings - explicitly defined
FPS = 30
VIDEO_DURATION_SECONDS = 10
TOTAL_FRAMES = FPS * VIDEO_DURATION_SECONDS  # 300 frames for 10 seconds at 30fps
RPM = 1000  # 1000 RPM as requested
CAMERA_ANGLE_OFFSET = 0  # Removed angle offset to get a clean side view

# ---------- UTILS ----------
def clear_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

# ---------- SCENE SETUP ----------
def setup_camera():
    cam_data = bpy.data.cameras.new("Camera")
    cam = bpy.data.objects.new("Camera", cam_data)
    bpy.context.collection.objects.link(cam)
    bpy.context.scene.camera = cam
    return cam

def setup_lighting():
    # Key light
    key_light_data = bpy.data.lights.new(name="Key", type='SUN')
    key_light = bpy.data.objects.new(name="Key", object_data=key_light_data)
    bpy.context.collection.objects.link(key_light)
    key_light.location = (2, -2, 4)
    key_light.data.energy = random.uniform(5, 10)
    key_light.data.color = (1.0, 0.95, 0.9)  # Warm key light
    
    # Fill light
    fill_light_data = bpy.data.lights.new(name="Fill", type='SUN')
    fill_light = bpy.data.objects.new(name="Fill", object_data=fill_light_data)
    bpy.context.collection.objects.link(fill_light)
    fill_light.location = (-3, 0, 2)
    fill_light.data.energy = random.uniform(2, 4) 
    fill_light.data.color = (0.9, 0.95, 1.0)  # Cool fill light
    
    # Backlight for rim highlight
    back_light_data = bpy.data.lights.new(name="Back", type='SUN')
    back_light = bpy.data.objects.new(name="Back", object_data=back_light_data)
    bpy.context.collection.objects.link(back_light)
    back_light.location = (0, 5, 1)
    back_light.data.energy = random.uniform(3, 6)
    back_light.data.color = (1.0, 1.0, 1.0)

def setup_clear_underwater_world():
    world = bpy.context.scene.world
    world.use_nodes = True
    nodes = world.node_tree.nodes
    links = world.node_tree.links
    for node in nodes:
        nodes.remove(node)

    # Create a clear blue background without volume scattering
    bg = nodes.new(type='ShaderNodeBackground')
    bg.inputs[0].default_value = (
        random.uniform(0.1, 0.2),
        random.uniform(0.2, 0.4),
        random.uniform(0.4, 0.6),
        1.0)  # Lighter blue for better visibility
    
    out = nodes.new(type='ShaderNodeOutputWorld')
    links.new(bg.outputs['Background'], out.inputs['Surface'])
    
    # No volume scatter node to keep the scene clear

# ---------- BUBBLES ----------
def add_bubbles(count=80):
    # Create a new collection for bubbles if it doesn't exist
    if "Bubbles" not in bpy.data.collections:
        bubbles_collection = bpy.data.collections.new("Bubbles")
        bpy.context.scene.collection.children.link(bubbles_collection)
    else:
        bubbles_collection = bpy.data.collections["Bubbles"]
    
    for _ in range(count):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=random.uniform(0.003, 0.01))
        b = bpy.context.object
        
        # Move bubble to bubbles collection
        for coll in b.users_collection:
            coll.objects.unlink(b)
        bubbles_collection.objects.link(b)
        
        # Set location - keeping bubbles more to the side/background
        b.location = (
            random.uniform(-1, 1),
            random.uniform(0.5, 2),  # Position bubbles more behind the object
            random.uniform(0, 2),
        )
        
        # Create material for bubble
        mat = bpy.data.materials.new(name=f"BubbleMat_{uuid.uuid4().hex[:4]}")
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        
        # Get the principled BSDF node
        principled = nodes.get("Principled BSDF")
        if principled:
            # Make bubble transparent - safely set properties
            principled.inputs["Base Color"].default_value = (0.8, 0.9, 1.0, 1.0)
            
            # Safely set properties (handle different Blender versions)
            try:
                principled.inputs["Metallic"].default_value = 0.0
                principled.inputs["Roughness"].default_value = 0.1
                principled.inputs["Transmission"].default_value = 0.95
                principled.inputs["IOR"].default_value = 1.33
            except: 
                pass
        
        b.data.materials.append(mat)
        
        # Animate bubbles rising
        b.keyframe_insert(data_path="location", frame=1)
        
        # Bubbles rise at different speeds
        rise_speed = random.uniform(0.5, 2.0)
        b.location.z += rise_speed * VIDEO_DURATION_SECONDS
        
        # Add some horizontal drift
        b.location.x += random.uniform(-0.3, 0.3)
        b.location.y += random.uniform(-0.3, 0.3)
        
        b.keyframe_insert(data_path="location", frame=TOTAL_FRAMES)

# ---------- TEXTURE VARIATION ----------
def assign_enhanced_material(obj):
    mat = bpy.data.materials.new(name=f"Mat_{uuid.uuid4().hex[:4]}")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    
    # Choose from a palette of colors that will stand out against blue background
    color_palettes = [
        (0.8, 0.2, 0.2, 1.0),  # Red
        (0.8, 0.6, 0.2, 1.0),  # Orange/Gold
        (0.2, 0.7, 0.3, 1.0),  # Green
        (0.7, 0.7, 0.7, 1.0),  # Silver/Gray
        (0.8, 0.8, 0.3, 1.0),  # Yellow
    ]
    
    selected_color = random.choice(color_palettes)
    
    if bsdf:
        try:
            bsdf.inputs['Base Color'].default_value = selected_color
            bsdf.inputs['Roughness'].default_value = random.uniform(0.1, 0.5)  # More glossy finish
            bsdf.inputs['Metallic'].default_value = random.uniform(0.6, 1.0)  # More metallic look
            bsdf.inputs['Specular'].default_value = 0.8  # Enhance highlights
        except:
            pass
    
    obj.data.materials.clear()
    obj.data.materials.append(mat)

# ---------- MAIN ----------
def configure_video_settings():
    """Set up the render settings specifically for video output"""
    # Basic render settings
    bpy.context.scene.render.resolution_x = IMG_SIZE
    bpy.context.scene.render.resolution_y = IMG_SIZE
    bpy.context.scene.render.fps = FPS
    
    # Set up for VIDEO output
    bpy.context.scene.render.image_settings.file_format = 'FFMPEG'
    
    # FFMPEG settings
    ffmpeg = bpy.context.scene.render.ffmpeg
    ffmpeg.format = 'MPEG4'
    ffmpeg.codec = 'H264'
    ffmpeg.constant_rate_factor = 'MEDIUM'
    ffmpeg.gopsize = 18
    ffmpeg.video_bitrate = 8000
    
    # Frame range settings
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = TOTAL_FRAMES
    
    # Higher quality render settings if using EEVEE
    if bpy.context.scene.render.engine == 'BLENDER_EEVEE':
        bpy.context.scene.eevee.taa_render_samples = 64  # More samples for clearer image
        bpy.context.scene.eevee.use_gtao = True  # Ambient occlusion for better depth
        bpy.context.scene.eevee.use_bloom = True  # Slight bloom for highlights
        bpy.context.scene.eevee.bloom_intensity = 0.05
    
    # Higher quality render settings if using Cycles
    elif bpy.context.scene.render.engine == 'CYCLES':
        bpy.context.scene.cycles.samples = 128
        bpy.context.scene.cycles.use_denoising = True

def main():
    # Ensure compatible render engine
    try:
        if bpy.context.scene.render.engine not in {'BLENDER_EEVEE', 'CYCLES'}:
            bpy.context.scene.render.engine = 'BLENDER_EEVEE'
    except:
        try:
            bpy.context.scene.render.engine = 'CYCLES'
        except:
            print("Warning: Could not set a compatible render engine")
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    blend_files = [f for f in os.listdir(BLEND_DIR) if f.endswith('.blend')]
    
    for blend_file in blend_files:
        try:
            # Try to open the file
            bpy.ops.wm.open_mainfile(filepath=os.path.join(BLEND_DIR, blend_file))
            
            # Set up render settings - MUST be done after loading each file
            configure_video_settings()
            
            setup_lighting()
            cam = setup_camera()
            setup_clear_underwater_world()
            add_bubbles(BUBBLE_COUNT)

            propeller_found = False
            for obj in bpy.context.scene.objects:
                if obj.type == 'MESH' and "Bubbles" not in obj.name:
                    # Skip collection objects by checking name
                    assign_enhanced_material(obj)

                    # Center object, normalize size
                    bpy.ops.object.select_all(action='DESELECT')
                    obj.select_set(True)
                    bpy.context.view_layer.objects.active = obj
                    
                    try:
                        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
                        
                        # Avoid division by zero
                        max_dim = max(obj.dimensions) if max(obj.dimensions) > 0 else 1.0
                        scale = 1.0 / max_dim
                        obj.scale = (scale, scale, scale)
                        bpy.ops.object.transform_apply(scale=True)
                    except Exception as e:
                        print(f"Warning: Could not transform object: {str(e)}")

                    # Calculate rotation for 1000 RPM over 10 seconds
                    total_rotation = (RPM / 60) * VIDEO_DURATION_SECONDS * 360  # in degrees
                    
                    # Animate propeller
                    obj.animation_data_clear()
                    try: 
                        obj.driver_remove("rotation_euler", 0)
                    except: 
                        pass
                    
                    obj.rotation_euler = (0.0, 0.0, 0.0)
                    obj.keyframe_insert(data_path="rotation_euler", frame=1)
                    
                    obj.rotation_euler = (math.radians(total_rotation), 0.0, 0.0)
                    obj.keyframe_insert(data_path="rotation_euler", frame=TOTAL_FRAMES)
                    
                    # Set linear interpolation for smooth rotation
                    if obj.animation_data and obj.animation_data.action:
                        for fc in obj.animation_data.action.fcurves:
                            for kp in fc.keyframe_points:
                                kp.interpolation = 'LINEAR'

                    # Position camera for perfect side view
                    cam.location = (0, 2.5, 0)  # Direct side view position
                    cam.data.lens = random.uniform(24, 35)  # Slightly narrower angle lens
                    
                    # Calculate rotation to look at object from the side
                    target_position = Vector((0, 0, 0))  # Object should be at origin
                    direction = target_position - cam.location
                    
                    # Create a rotation that points the camera's -Y axis toward the target
                    # and keeps the Z axis pointing upward
                    cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
                    
                    # Set DOF settings for better depth and focus on object
                    try:
                        cam.data.dof.use_dof = True
                        cam.data.dof.focus_distance = 2.5  # Match camera distance
                        cam.data.dof.aperture_fstop = random.uniform(4.0, 8.0)  # Higher f-stop for better clarity
                    except:
                        print("Warning: Could not set DOF settings")

                    # Set video output path - use blend file name as part of the output
                    blend_name = os.path.splitext(blend_file)[0]
                    video_path = os.path.join(OUTPUT_DIR, f"{blend_name}_1000rpm_side_view_{CLASS_NAME}_{uuid.uuid4().hex[:4]}.mp4")
                    
                    # CRITICAL: Make sure the output path explicitly includes the file extension
                    bpy.context.scene.render.filepath = video_path
                    
                    print(f"Rendering video: {video_path}")
                    print(f"Propeller RPM: {RPM}")
                    print(f"Camera: Side view")
                    print(f"Frame range: {bpy.context.scene.frame_start} to {bpy.context.scene.frame_end}")
                    print(f"File format: {bpy.context.scene.render.image_settings.file_format}")
                    
                    # Render animation as video
                    bpy.ops.render.render(animation=True)
                    propeller_found = True
                    break  # Process only the first suitable mesh object
            
            if not propeller_found:
                print(f"Warning: No suitable mesh object found in {blend_file}")
                
        except Exception as e:
            print(f"Error processing {blend_file}: {str(e)}")
            continue

main()
