import bpy
import bmesh


def _get_evaluated_mesh(obj, context):
    depsgraph = context.evaluated_depsgraph_get()
    eval_obj = obj.evaluated_get(depsgraph)
    mesh = eval_obj.to_mesh()
    return mesh


def _triangulate_mesh(mesh):
    bm = bmesh.new()
    bm.from_mesh(mesh)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    return mesh


def _extract_mesh_data(obj, context, convert_coords, scale):
    mesh = _get_evaluated_mesh(obj, context)
    _triangulate_mesh(mesh)

    if hasattr(mesh, 'loop_triangles') and mesh.loop_triangles:
        mesh.calc_loop_triangles()
    elif hasattr(mesh, 'corner_triangles'):
        mesh.calc_corner_triangles()

    verts = []
    for v in mesh.vertices:
        x, y, z = v.co
        x *= scale
        y *= scale
        z *= scale
        if convert_coords:
            x, y, z = y, -x, z
        verts.append((x, y, z))

    tris = []
    uv_coords = []
    uv_layer = mesh.uv_layers.active

    tris_iter = getattr(mesh, 'loop_triangles', None) or getattr(mesh, 'corner_triangles', [])

    for tri in tris_iter:
        v0, v1, v2 = tri.vertices
        tris.append((v0, v1, v2, len(uv_coords), len(uv_coords) + 1, len(uv_coords) + 2))

        for loop_idx in tri.loops:
            if uv_layer:
                uv = uv_layer.data[loop_idx].uv
                uv_coords.append((uv.x, uv.y))
            else:
                uv_coords.append((0.0, 0.0))

    normals = []
    for v in mesh.vertices:
        nx, ny, nz = v.normal
        if convert_coords:
            normals.append((ny, -nx, nz))
        else:
            normals.append((nx, ny, nz))

    return verts, tris, uv_coords, normals, mesh


def _get_animations(obj):
    anims = []

    if obj.data.shape_keys and obj.data.shape_keys.animation_data:
        for track in obj.data.shape_keys.animation_data.nla_tracks:
            for strip in track.strips:
                if strip.action:
                    anim_name = track.name
                    anims.append((anim_name, strip.action, 10))

    if not anims:
        sk_block = obj.data.shape_keys
        if sk_block and sk_block.animation_data and sk_block.animation_data.action:
            action = sk_block.animation_data.action
            anims.append((action.name, action, 10))

    return anims


def _sample_frames(obj, context, anim_name, action, fps, frame_sampling, convert_coords, scale):
    frames = []
    if not action:
        return frames

    scene = context.scene
    orig_frame = scene.frame_current
    frame_range = action.frame_range
    sk_block = obj.data.shape_keys

    prev_eval = None
    frame_idx = 0

    for frame_num in range(int(frame_range[0]), int(frame_range[1]) + 1):
        scene.frame_set(frame_num)

        if sk_block:
            current_eval = sk_block.eval_time
            if not frame_sampling and current_eval == prev_eval:
                continue
            prev_eval = current_eval

        mesh = _get_evaluated_mesh(obj, context)
        _triangulate_mesh(mesh)

        if hasattr(mesh, 'loop_triangles') and mesh.loop_triangles:
            mesh.calc_loop_triangles()
        elif hasattr(mesh, 'corner_triangles'):
            mesh.calc_corner_triangles()

        frame_verts = []
        for v in mesh.vertices:
            x, y, z = v.co
            x *= scale
            y *= scale
            z *= scale
            if convert_coords:
                x, y, z = y, -x, z
            frame_verts.append((x, y, z))

        frame_normals = []
        for v in mesh.vertices:
            nx, ny, nz = v.normal
            if convert_coords:
                frame_normals.append((ny, -nx, nz))
            else:
                frame_normals.append((nx, ny, nz))

        frame_name = f"{anim_name}{frame_idx:03d}"

        frames.append({
            "name": frame_name,
            "verts": frame_verts,
            "normals": frame_normals,
        })
        frame_idx += 1

    scene.frame_set(orig_frame)
    return frames


def _get_material_info(obj):
    if not obj.data.materials:
        return None, "skin"

    mat = obj.data.materials[0]
    if mat is None:
        return None, "skin"
    if not mat.use_nodes:
        return mat.name, "skin"

    for node in mat.node_tree.nodes:
        if node.type == 'TEX_IMAGE' and node.image:
            return mat.name, node.image.name

    return mat.name, "skin"


def _find_sibling_anim_objs(obj):
    siblings = []
    prefix = ""
    if '_' in obj.name:
        prefix = obj.name.rsplit('_', 1)[0] + '_'

    for col in obj.users_collection:
        for other in col.objects:
            if other.type != 'MESH':
                continue
            if other == obj:
                continue
            if not other.data.shape_keys:
                continue
            if prefix and other.name.startswith(prefix):
                siblings.append(other)
            elif not prefix:
                siblings.append(other)
        if siblings:
            break
    return siblings


def _validate_topology(objs):
    ref = objs[0].data
    ref_verts = len(ref.vertices)
    for o in objs[1:]:
        if len(o.data.vertices) != ref_verts:
            return False
    return True


def extract(obj, context, options):
    convert_coords = options.get("convert_coords", False)
    export_animation = options.get("export_animation", True)
    frame_sampling = options.get("frame_sampling", False)
    scale = options.get("scale", 1.0)

    anim_objs = [obj]
    if export_animation:
        siblings = _find_sibling_anim_objs(obj)
        if siblings:
            all_objs = [obj] + siblings
            if _validate_topology(all_objs):
                anim_objs = all_objs

    verts, tris, uvs, normals, _ = _extract_mesh_data(anim_objs[0], context, convert_coords, scale)

    mat_name, skin_base = _get_material_info(obj)
    tex_name = options.get("texture_name", "") or obj.name
    tex_name = tex_name.rsplit('_', 1)[0] if '_' in tex_name else tex_name
    skin_name = tex_name + ".png"

    data = {
        "verts": verts,
        "tris": tris,
        "uvs": uvs,
        "normals": normals,
        "skin_name": skin_name,
        "skinwidth": options.get("skinwidth", 256),
        "skinheight": options.get("skinheight", 256),
        "material_name": mat_name,
        "frames": [],
    }

    if export_animation:
        for anim_obj in anim_objs:
            anim_name = anim_obj.name.rsplit('_', 1)[-1] if '_' in anim_obj.name else anim_obj.name
            anims = _get_animations(anim_obj)
            if anims:
                for _, action, fps in anims:
                    f = _sample_frames(anim_obj, context, anim_name, action, fps, frame_sampling, convert_coords, scale)
                    data["frames"].extend(f)
            else:
                data["frames"].append({
                    "name": anim_name + "000",
                    "verts": verts,
                    "normals": normals,
                })
    else:
        data["frames"].append({
            "name": obj.name[:13] + "000",
            "verts": verts,
            "normals": normals,
        })

    return data
