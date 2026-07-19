import struct
from dataclasses import dataclass
from typing import List, Tuple

MD2_IDENT = 844121161
MD2_VERSION = 8

@dataclass
class MD2Header:
    ident: int
    version: int
    skinwidth: int
    skinheight: int
    framesize: int
    num_skins: int
    num_xyz: int
    num_st: int
    num_tris: int
    num_glcmds: int
    num_frames: int
    ofs_skins: int
    ofs_st: int
    ofs_tris: int
    ofs_frames: int
    ofs_glcmds: int
    ofs_end: int

@dataclass
class MD2Vertex:
    v: Tuple[int, int, int]
    lightnormalindex: int

@dataclass
class MD2Frame:
    scale: Tuple[float, float, float]
    translate: Tuple[float, float, float]
    name: str
    verts: List[MD2Vertex]

@dataclass
class MD2Triangle:
    vertex_indices: Tuple[int, int, int]
    st_indices: Tuple[int, int, int]

@dataclass
class MD2TexCoord:
    s: int
    t: int

class MD2File:
    def __init__(self, filepath):
        self.filepath = filepath
        self.header = None
        self.skins = []
        self.tex_coords = []
        self.triangles = []
        self.frames = []
        self.glcmds = []

    def read(self):
        with open(self.filepath, 'rb') as f:
            buffer = f.read(68)
            data = struct.unpack('<17i', buffer)
            self.header = MD2Header(*data)

            if self.header.ident != MD2_IDENT:
                raise ValueError(f"Invalid MD2 ident: {self.header.ident}")
            if self.header.version != MD2_VERSION:
                raise ValueError(f"Invalid MD2 version: {self.header.version}")

            f.seek(self.header.ofs_skins)
            for _ in range(self.header.num_skins):
                raw_name = f.read(64)
                skin_name = raw_name.split(b'\x00', 1)[0].decode('utf-8', errors='ignore')
                self.skins.append(skin_name)

            f.seek(self.header.ofs_st)
            for _ in range(self.header.num_st):
                s, t = struct.unpack('<hh', f.read(4))
                self.tex_coords.append(MD2TexCoord(s, t))

            f.seek(self.header.ofs_tris)
            for _ in range(self.header.num_tris):
                tris_data = struct.unpack('<3H3H', f.read(12))
                self.triangles.append(MD2Triangle(tris_data[:3], tris_data[3:]))

            f.seek(self.header.ofs_frames)
            for _ in range(self.header.num_frames):
                self.frames.append(self._read_frame(f))

            if self.header.num_glcmds > 0 and self.header.ofs_glcmds < self.header.ofs_end:
                f.seek(self.header.ofs_glcmds)
                raw = f.read(self.header.num_glcmds * 4)
                self.glcmds = list(struct.unpack(f'<{self.header.num_glcmds}i', raw))

    def _read_frame(self, f) -> MD2Frame:
        scale = struct.unpack('<3f', f.read(12))
        translate = struct.unpack('<3f', f.read(12))
        name = f.read(16).split(b'\x00')[0].decode('utf-8', errors='ignore').strip()

        verts = []
        for _ in range(self.header.num_xyz):
            v_data = struct.unpack('<3B B', f.read(4))
            verts.append(MD2Vertex(v_data[:3], v_data[3]))

        return MD2Frame(scale, translate, name, verts)
