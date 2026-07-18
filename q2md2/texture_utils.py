import os
import bpy

POW2_SIZES = [8, 16, 32, 64, 128, 256, 512, 1024]

def _nearest_pow2(value, max_size):
    best = 8
    for s in POW2_SIZES:
        if s <= max_size:
            best = s
        if s >= value:
            break
    return best

def export_texture(data, dest_dir, options):
    if not options.get("pack_texture", True):
        return

    tex_format = options.get("texture_format", "PNG")
    if tex_format == "None":
        return

    resize = options.get("resize_pow2", True)
    max_size = options.get("max_texture_size", 256)
    tex_name = options.get("texture_name", "") or data.get("skin_name", "skin")

    img = _find_image(data)
    if img is None:
        img = _create_default_texture(tex_name)

    orig_w, orig_h = img.size

    if resize:
        new_w = _nearest_pow2(orig_w, max_size)
        new_h = _nearest_pow2(orig_h, max_size)
        if (new_w, new_h) != (orig_w, orig_h):
            img.scale(new_w, new_h)
        data["skinwidth"] = new_w
        data["skinheight"] = new_h
    else:
        data["skinwidth"] = orig_w
        data["skinheight"] = orig_h

    img_path = os.path.join(dest_dir, tex_name + ".png")
    img.save_render(img_path)
    data["skin_name"] = tex_name + ".png"

def _find_image(data):
    mat_name = data.get("material_name", "")
    if not mat_name:
        return None
    mat = bpy.data.materials.get(mat_name)
    if not mat or not mat.use_nodes:
        return None
    for node in mat.node_tree.nodes:
        if node.type == 'TEX_IMAGE' and node.image:
            return node.image
    return None

def _create_default_texture(name):
    img = bpy.data.images.new(name=name + "_tex", width=16, height=16)
    pixels = [0.0] * (16 * 16 * 4)
    img.pixels = pixels
    return img
