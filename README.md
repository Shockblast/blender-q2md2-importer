# Quake 2 MD2 Import/Export for Blender

Import and export Quake 2 (`.md2`) models with full animation, UV, and texture support.

Compatible with Blender 4.2+ (Extensions system) and Blender 5.0+.

## Features

### Import
- **Geometry**: Vertices and faces with correct winding.
- **UV Mapping**: Preserves original texture coordinates.
- **Animation**: Absolute shape keys organized into NLA tracks per animation (parsed from frame names).
- **One Object Per Frame**: Option to generate a separate object per frame.
- **Texture Search**: Auto-searches `.png`, `.jpg`, `.jpeg`, `.tga` next to the `.md2`. `.pcx` is skipped.

### Export
- **Mesh**: Triangulated, with modifiers applied.
- **UVs**: One texcoord per triangle corner (no sharing), PNG texture exported alongside.
- **Animation**: Reads NLA tracks or active Action, samples keyframes, writes as MD2 frame sequence.
- **Normals**: Computed per-frame, mapped to the 162-entry Quake normal table.
- **Texture Resize**: Optional power-of-2 resize (8x8 to 1024x1024).
- **Coordinate Conversion**: Optional Blender (Y-forward) to Quake (X-forward).
- **Scale**: Adjustable (1.0 = raw, 0.0254 for import from Quake inches to meters, 39.37 for export meters to inches).

## Installation

```bash
# Package the addon
cd <repo-root>
zip -r q2md2.zip q2md2/
```

In Blender: `Edit > Preferences > Add-ons > Install` → select `q2md2.zip`. Search for "Quake 2 MD2" and enable it.

## Usage

### Import
`File > Import > Quake 2 (.md2)`

Options:
- **One Object Per Frame**: Separate object per frame instead of shape key animation.
- **FPS**: Frames per second for NLA track timing (default 10).
- **Scale**: Scale factor (1.0 = raw Quake units, 0.0254 to convert to meters).

### Export
`File > Export > Quake 2 (.md2)`

Options:
- **Export Animation**: Export NLA/Action frames as MD2 animation frames.
- **Frame Sampling**: Export all frames in range, not just keyframes.
- **FPS**: FPS metadata stored in the exported file.
- **Texture**: Format (PNG/None), resize to power of 2, max size, name, pack toggle.
- **Convert Coords**: Convert Y-forward (Blender) to X-forward (Quake).
- **Scale**: Apply scale to exported geometry (39.37 to convert meters to Quake inches).

## Round-trip workflow

1. Import an `.md2` (scale 1.0, coords as-is).
2. Edit the model in Blender (mesh, UVs, shape keys).
3. Export (scale 1.0, convert coords off) → identical format structure.

To work in meters: import at scale 0.0254, edit, export at scale 39.37.

## Notes

- MD2 uses uint16 vertex indices (max 65535 verts) and texcoord indices (max ~21845 tris with per-corner UVs). Warnings are shown at export.
- PCX textures are not supported. Convert to PNG before importing.
- Only the first material with a ShaderNodeTexImage is exported (MD2 supports one skin).
- GL commands are omitted (`num_glcmds = 0`) — compatible with all engines.

## License

GPL-2.0-or-later
