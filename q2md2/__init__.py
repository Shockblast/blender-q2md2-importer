bl_info = {
    "name": "Quake 2 MD2 Import/Export",
    "author": "Shockblast",
    "version": (2, 0, 0),
    "blender": (2, 80, 0),
    "location": "File > Import > Quake 2 (.md2) / File > Export > Quake 2 (.md2)",
    "description": "Import and export Quake 2 MD2 models with animations",
    "warning": "",
    "doc_url": "https://github.com/Shockblast/blender-q2md2-importer",
    "category": "Import-Export",
}

import bpy
import os
from bpy.props import StringProperty, BoolProperty, EnumProperty, IntProperty, FloatProperty
from bpy.types import Operator
from bpy_extras.io_utils import ImportHelper, ExportHelper


class ImportMD2(Operator, ImportHelper):
    """Import a Quake 2 MD2 file"""
    bl_idname = "import_scene.md2"
    bl_label = "Import MD2"

    filename_ext = ".md2"
    filter_glob: StringProperty(default="*.md2", options={'HIDDEN'}, maxlen=255)

    one_object_per_frame: BoolProperty(
        name="One Object Per Frame",
        default=False,
    )

    fps: IntProperty(
        name="FPS",
        default=10,
        min=1, max=60,
    )

    scale: FloatProperty(
        name="Scale",
        description="Scale factor (1.0 = raw Quake units, 0.0254 = convert to meters)",
        default=1.0,
        min=0.0001, max=1000.0,
    )

    def execute(self, context):
        from . import builder
        return builder.load_md2(self.filepath, context, self.one_object_per_frame, self.fps, self.scale)


class ExportMD2(Operator, ExportHelper):
    """Export to Quake 2 MD2 format"""
    bl_idname = "export_scene.md2"
    bl_label = "Export MD2"

    filename_ext = ".md2"
    filter_glob: StringProperty(default="*.md2", options={'HIDDEN'}, maxlen=255)

    export_animation: BoolProperty(
        name="Export Animation",
        default=True,
    )

    frame_sampling: BoolProperty(
        name="Frame Sampling",
        description="Export all frames in range, not just keyframes",
        default=False,
    )

    fps: IntProperty(
        name="FPS",
        default=10,
        min=1, max=60,
    )

    texture_format: EnumProperty(
        name="Texture Format",
        items=[('PNG', 'PNG', 'Export texture as PNG'), ('None', 'None', "Don't export texture")],
        default='PNG',
    )

    resize_pow2: BoolProperty(
        name="Resize to Power of 2",
        default=True,
    )

    max_texture_size: EnumProperty(
        name="Max Texture Size",
        items=[
            ('8', '8', ''), ('16', '16', ''), ('32', '32', ''), ('64', '64', ''),
            ('128', '128', ''), ('256', '256', ''), ('512', '512', ''), ('1024', '1024', ''),
        ],
        default='256',
    )

    texture_name: StringProperty(
        name="Texture Name",
        default="",
    )

    pack_texture: BoolProperty(
        name="Pack Texture",
        default=True,
    )

    convert_coords: BoolProperty(
        name="Convert Coords",
        default=False,
    )

    scale: FloatProperty(
        name="Scale",
        description="Scale factor (1.0 = raw Blender units, 39.37 = convert to Quake inches)",
        default=1.0,
        min=0.0001, max=1000.0,
    )

    def execute(self, context):
        obj = context.active_object
        if not obj:
            self.report({'ERROR'}, "No active object selected")
            return {'CANCELLED'}
        if obj.type != 'MESH':
            self.report({'ERROR'}, "Active object is not a mesh")
            return {'CANCELLED'}

        num_verts = len(obj.data.vertices)
        num_tris = sum(len(p.vertices) - 2 for p in obj.data.polygons)

        if num_verts > 65535:
            self.report({'WARNING'}, f"Model has {num_verts} vertices (>65535 may fail in some engines)")

        if num_tris > 21845:
            self.report({'WARNING'}, f"Model has {num_tris} triangles (>21845 may exceed texcoord index limit)")

        if not obj.data.uv_layers.active:
            self.report({'WARNING'}, "Mesh has no UV layers, exporting with zero UVs")

        options = {
            "export_animation": self.export_animation,
            "frame_sampling": self.frame_sampling,
            "fps": self.fps,
            "texture_format": self.texture_format,
            "resize_pow2": self.resize_pow2,
            "max_texture_size": int(self.max_texture_size),
            "texture_name": self.texture_name,
            "pack_texture": self.pack_texture,
            "convert_coords": self.convert_coords,
            "scale": self.scale,
            "skinwidth": 256,
            "skinheight": 256,
        }

        context.window_manager.progress_begin(0, 100)

        try:
            from . import extractor
            context.window_manager.progress_update(10)
            data = extractor.extract(obj, context, options)

            context.window_manager.progress_update(50)

            if self.pack_texture:
                from . import texture_utils
                dest_dir = os.path.dirname(self.filepath)
                texture_utils.export_texture(data, dest_dir, options)
                context.window_manager.progress_update(70)

            from . import md2_writer
            md2_writer.write_md2(self.filepath, data)
            context.window_manager.progress_update(100)
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.report({'ERROR'}, str(e))
            return {'CANCELLED'}
        finally:
            context.window_manager.progress_end()

        return {'FINISHED'}


def menu_func_import(self, context):
    self.layout.operator(ImportMD2.bl_idname, text="Quake 2 (.md2)")


def menu_func_export(self, context):
    self.layout.operator(ExportMD2.bl_idname, text="Quake 2 (.md2)")


def register():
    bpy.utils.register_class(ImportMD2)
    bpy.utils.register_class(ExportMD2)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
    bpy.utils.unregister_class(ExportMD2)
    bpy.utils.unregister_class(ImportMD2)


if __name__ == "__main__":
    register()
