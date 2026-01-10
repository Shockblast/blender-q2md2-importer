import struct
from dataclasses import dataclass
from typing import List, Tuple

# MD2 Constants
MD2_IDENT = 844121161  # "IDP2"
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

    def read(self):
        with open(self.filepath, 'rb') as f:
            # Read Header (68 bytes)
            # 17 integers (4 bytes each)
            buffer = f.read(68)
            data = struct.unpack('<17i', buffer)
            
            self.header = MD2Header(*data)

            if self.header.ident != MD2_IDENT:
                raise ValueError(f"Invalid MD2 ident: {self.header.ident}")
            if self.header.version != MD2_VERSION:
                raise ValueError(f"Invalid MD2 version: {self.header.version}")

            # Read Skins
            f.seek(self.header.ofs_skins)
            for _ in range(self.header.num_skins):
                # Skin names are 64 bytes char array
                raw_name = f.read(64)
                # Split by null byte to get the first string before any garbage/padding
                skin_name = raw_name.split(b'\x00', 1)[0].decode('utf-8', errors='ignore')
                self.skins.append(skin_name)

            # Read Texture Coordinates (st)
            f.seek(self.header.ofs_st)
            for _ in range(self.header.num_st):
                s, t = struct.unpack('<hh', f.read(4))
                self.tex_coords.append(MD2TexCoord(s, t))

            # Read Triangles
            f.seek(self.header.ofs_tris)
            for _ in range(self.header.num_tris):
                # 3 shorts for vertex indices, 3 shorts for st indices
                # Total 12 bytes
                tris_data = struct.unpack('<3H3H', f.read(12))
                self.triangles.append(MD2Triangle(tris_data[:3], tris_data[3:]))

            # Read Frames
            f.seek(self.header.ofs_frames)
            for _ in range(self.header.num_frames):
                self.frames.append(self._read_frame(f))

    def _read_frame(self, f) -> MD2Frame:
        # Frame header: scale(3f), translate(3f), name(16s) -> 12+12+16 = 40 bytes
        scale = struct.unpack('<3f', f.read(12))
        translate = struct.unpack('<3f', f.read(12))
        name = f.read(16).decode('utf-8', errors='ignore').strip('\x00')
        
        # Verts: num_xyz * 4 bytes (v[3] bytes, lightnormalindex byte)
        verts = []
        for _ in range(self.header.num_xyz):
            v_data = struct.unpack('<3B B', f.read(4))
            verts.append(MD2Vertex(v_data[:3], v_data[3]))
            
        return MD2Frame(scale, translate, name, verts)
