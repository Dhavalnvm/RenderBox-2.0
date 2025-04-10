# RenderBox-2.0
# Blender-Based Synthetic Dataset Generator for Object Detection (YOLO Format)

This module of **RenderBox** generates a **synthetic underwater dataset** using Blender and `.blend` files containing 3D models (typically imported from STL or other formats). It simulates **underwater environments**, applies **randomized lighting and camera positions**, and exports **YOLO-style annotations** with bounding boxes.

## ✅ Features

- Uses native Blender Python API (`bpy`) for rendering
- Randomized camera orbits around the object
- Dynamic underwater lighting setup:
  - Overhead spotlights
  - Bluish point-fill lights
- Procedural underwater environment:
  - Dark bluish background
  - Volumetric scattering
- Normalizes object scale across files
- Auto-labels objects using 2D bounding box projection
- Exports images + YOLO labels
- Supports train/val split

## 📁 Directory Structure

<pre> output/ 
  └── data2/
    ├── images/
    │   ├── train/                 # Training images
    │   └── val/                   # Validation images
    ├── labels/
    │   ├── train/                 # Training labels
    │   └── val/                   # Validation labels </pre>

> All images and labels are exported in YOLO format with `.txt` annotations.

## 🔧 Configuration

Edit the configuration section in the script:

<pre>BLEND_DIR = "path/to/blend/files"        # Input Blender files
OUTPUT_DIR = "path/to/output/dir"        # Base output folder
CLASS_NAME = 'propeller'                 # Class label name
IMG_SIZE = 512                           # Output resolution (square)
NUM_IMAGES_PER_FILE = 40                 # Rendered views per model
TRAIN_RATIO = 0.8                        # Train/val split ratio</pre>

## ⚙️ Requirements

You'll need Blender 3.x installed. Run the script *inside* Blender’s scripting panel or from the CLI:

```bash
blender --background --python Blender.py
pip install bpy uuid opencv-python
