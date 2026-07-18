import struct
from .quake_normals import best_normal

MD2_IDENT = 844121161
MD2_VERSION = 8

def clamp(val, lo, hi):
    return max(lo, min(hi, val))

def _pack_skin(name):
    data = name.encode('utf-8')[:63]
    data += b'\x00'
    return data.ljust(64, b'\x00')

def _pack_frame_name(name):
    data = name.encode('ascii', errors='replace')[:15]
    return data.ljust(16, b'\x00')

def write_md2(filepath, data):
    verts = data["verts"]
    tris = data["tris"]
    uvs = data["uvs"]
    skin_name = data["skin_name"]
    skinwidth = data["skinwidth"]
    skinheight = data["skinheight"]
    frames = data["frames"]

    num_xyz = len(verts)
    num_tris = len(tris)
    num_st = len(uvs)
    num_skins = 1
    num_frames = len(frames)
    num_glcmds = 0
    frame_size = 40 + num_xyz * 4

    ofs_skins = 68
    ofs_st = ofs_skins + num_skins * 64
    ofs_tris = ofs_st + num_st * 4
    ofs_frames = ofs_tris + num_tris * 12
    ofs_glcmds = ofs_frames + num_frames * frame_size
    ofs_end = ofs_glcmds

    with open(filepath, 'wb') as f:
        f.write(struct.pack('<17i',
            MD2_IDENT, MD2_VERSION,
            skinwidth, skinheight, frame_size,
            num_skins, num_xyz, num_st, num_tris, num_glcmds, num_frames,
            ofs_skins, ofs_st, ofs_tris, ofs_frames, ofs_glcmds, ofs_end))

        f.write(_pack_skin(skin_name))

        for u, v in uvs:
            s = int(round(u * skinwidth))
            t = int(round((1.0 - v) * skinheight))
            f.write(struct.pack('<hh', s, t))

        for tri in tris:
            f.write(struct.pack('<3H3H', tri[0], tri[1], tri[2], tri[3], tri[4], tri[5]))

        for frame in frames:
            fname = frame["name"]
            fverts = frame["verts"]
            fnormals = frame.get("normals", None)

            xs = [v[0] for v in fverts]
            ys = [v[1] for v in fverts]
            zs = [v[2] for v in fverts]

            xmin, xmax = min(xs), max(xs)
            ymin, ymax = min(ys), max(ys)
            zmin, zmax = min(zs), max(zs)

            sx = (xmax - xmin) / 255.0 if xmax != xmin else 1.0
            sy = (ymax - ymin) / 255.0 if ymax != ymin else 1.0
            sz = (zmax - zmin) / 255.0 if zmax != zmin else 1.0
            tx = xmin
            ty = ymin
            tz = zmin

            f.write(struct.pack('<3f', sx, sy, sz))
            f.write(struct.pack('<3f', tx, ty, tz))
            f.write(_pack_frame_name(fname))

            for vi, v in enumerate(fverts):
                cx = clamp(int(round((v[0] - tx) / sx)), 0, 255)
                cy = clamp(int(round((v[1] - ty) / sy)), 0, 255)
                cz = clamp(int(round((v[2] - tz) / sz)), 0, 255)
                ni = best_normal(fnormals[vi]) if fnormals else 0
                f.write(struct.pack('BBB', cx, cy, cz))
                f.write(struct.pack('B', ni))
