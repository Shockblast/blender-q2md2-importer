import bpy
import bmesh
from .md2_parser import MD2File, MD2Vertex
from typing import List

def _anim_name_from_frame(name):
    while name and (name[-1] in '0123456789' or name[-1] == '_'):
        name = name.rstrip('0123456789')
        name = name.rstrip('_')
    return name if name else "Anim"

def create_material(md2: MD2File, context) -> bpy.types.Material:
    mat_name = "Material"
    if md2.skins:
        import os
        mat_name = os.path.basename(md2.skins[0]).replace('\x00', '')
    
    mat = bpy.data.materials.new(name=mat_name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    
    if md2.skins or md2.filepath:
        import os
        base_dir = os.path.dirname(md2.filepath)
        
        candidates = []
        base_name = os.path.basename(md2.filepath)
        name_no_ext = os.path.splitext(base_name)[0]
        extensions = [".png", ".jpg", ".jpeg", ".tga"]
        
        for ext in extensions:
            candidates.append(name_no_ext + ext)
        
        if md2.skins:
            skin_path = md2.skins[0]
            candidates.append(os.path.basename(skin_path))
            skin_base = os.path.splitext(os.path.basename(skin_path))[0]
            for ext in extensions:
                candidates.append(skin_base + ext)
            
        for ext in extensions:
            candidates.append("skin" + ext)

        image = None
        
        try:
            files_in_dir = os.listdir(base_dir)
            files_map = {f.lower(): f for f in files_in_dir}
            
            for c in candidates:
                if c.lower().endswith('.pcx'):
                    continue
                    
                c_lower = c.lower()
                if c_lower in files_map:
                    image_path = os.path.join(base_dir, files_map[c_lower])
                    try:
                        image = bpy.data.images.load(image_path)
                        print(f"Loaded texture: {image_path}")
                        break
                    except:
                        continue
        except:
            pass
            
        if image:
            tex_node = mat.node_tree.nodes.new('ShaderNodeTexImage')
            tex_node.image = image
            tex_node.interpolation = 'Closest'
            mat.node_tree.links.new(tex_node.outputs['Color'], bsdf.inputs['Base Color'])

    return mat

def load_md2(filepath, context, one_object_per_frame=False, fps=10, scale=1.0):
    try:
        md2 = MD2File(filepath)
        md2.read()
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {'CANCELLED'}

    import os
    base_name = os.path.splitext(os.path.basename(filepath))[0]
    
    mat = create_material(md2, context)
    
    def build_mesh_for_frame(frame_data, mesh_name):
        new_mesh = bpy.data.meshes.new(mesh_name)
        
        verts = []
        sx, sy, sz = frame_data.scale
        tx, ty, tz = frame_data.translate
        
        for v in frame_data.verts:
            x = (v.v[0] * sx) + tx
            y = (v.v[1] * sy) + ty
            z = (v.v[2] * sz) + tz
            verts.append((x * scale, y * scale, z * scale))
            
        new_mesh.from_pydata(verts, [], [t.vertex_indices for t in md2.triangles])
        
        uv_layer = new_mesh.uv_layers.new(name="MD2_UV")
        bm = bmesh.new()
        bm.from_mesh(new_mesh)
        bm.faces.ensure_lookup_table()
        uv_layer = bm.loops.layers.uv.verify()
        
        skin_w = float(md2.header.skinwidth)
        skin_h = float(md2.header.skinheight)
        
        for i, tri in enumerate(md2.triangles):
            face = bm.faces[i]
            for j, loop in enumerate(face.loops):
                st_idx = tri.st_indices[j]
                st = md2.tex_coords[st_idx]
                u = st.s / skin_w
                v = 1.0 - (st.t / skin_h)
                loop[uv_layer].uv = (u, v)
        
        bm.to_mesh(new_mesh)
        bm.free()
        
        if mat:
            new_mesh.materials.append(mat)
            
        return new_mesh

    if one_object_per_frame:
        col = bpy.data.collections.new(base_name + "_Frames")
        context.collection.children.link(col)
        
        for i, frame in enumerate(md2.frames):
            obj_name = f"{base_name}_{i+1:03d}_{frame.name}"
            mesh = build_mesh_for_frame(frame, obj_name)
            obj = bpy.data.objects.new(obj_name, mesh)
            col.objects.link(obj)
            
    else:
        sk_names = [f.name for f in md2.frames]
        anims = {}
        for i, name in enumerate(sk_names):
            anim = _anim_name_from_frame(name)
            anims.setdefault(anim, []).append((i, name))

        col = bpy.data.collections.new(base_name)
        context.collection.children.link(col)
        first_obj = None

        for anim_name, frames in anims.items():
            first_idx = frames[0][0]
            basis_frame = md2.frames[first_idx]
            obj_name = f"{base_name}_{anim_name}"
            mesh = build_mesh_for_frame(basis_frame, obj_name)
            obj = bpy.data.objects.new(obj_name, mesh)

            col.objects.link(obj)
            if first_obj is None:
                first_obj = obj

            obj.shape_key_add(name="Basis")
            obj.data.shape_keys.use_relative = False

            for local_idx, (global_idx, _) in enumerate(frames):
                if local_idx == 0:
                    continue
                frame = md2.frames[global_idx]
                sk = obj.shape_key_add(name=frame.name)

                sx, sy, sz = frame.scale
                tx, ty, tz = frame.translate

                flat_coords = [0.0] * (len(frame.verts) * 3)
                for v_idx, mv in enumerate(frame.verts):
                    x = (mv.v[0] * sx) + tx
                    y = (mv.v[1] * sy) + ty
                    z = (mv.v[2] * sz) + tz
                    base_idx = v_idx * 3
                    flat_coords[base_idx] = x * scale
                    flat_coords[base_idx + 1] = y * scale
                    flat_coords[base_idx + 2] = z * scale
                sk.data.foreach_set("co", flat_coords)

            sk_block = obj.data.shape_keys
            sk_block.animation_data_create()

            for local_idx in range(len(frames)):
                sk_block.eval_time = (local_idx + 1) * 10
                sk_block.keyframe_insert(data_path="eval_time", frame=local_idx + 1)

        if first_obj:
            context.view_layer.objects.active = first_obj
            first_obj.select_set(True)
            context.scene.frame_start = 1
            context.scene.frame_end = max(len(f) for f in anims.values())
            context.scene.frame_current = 1
    
    return {'FINISHED'}
