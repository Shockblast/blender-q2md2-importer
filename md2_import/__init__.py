bl_info = {
    "name": "Quake 2 MD2 Importer",
    "author": "Antigravity",
    "version": (1, 0, 0),
    "blender": (2, 80, 0),
    "location": "File > Import > Quake 2 (.md2)",
    "description": "Import Quake 2 MD2 models with animations",
    "warning": "",
    "doc_url": "",
    "category": "Import-Export",
}

import bpy
from bpy.props import StringProperty, BoolProperty
from bpy.types import Operator
from bpy_extras.io_utils import ImportHelper

class ImportMD2(Operator, ImportHelper):
    """Import a Quake 2 MD2 file"""
    bl_idname = "import_scene.md2"
    bl_label = "Import MD2"
    
    filename_ext = ".md2"
    filter_glob: StringProperty(
        default="*.md2",
        options={'HIDDEN'},
        maxlen=255,
    )
    
    one_object_per_frame: BoolProperty(
        name="One Object Per Frame",
        description="Create a separate object for each animation frame",
        default=False,
    )

    def execute(self, context):
        from . import builder
        return builder.load_md2(self.filepath, context, self.one_object_per_frame)

def menu_func_import(self, context):
    self.layout.operator(ImportMD2.bl_idname, text="Quake 2 (.md2)")

def register():
    bpy.utils.register_class(ImportMD2)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)

def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.utils.unregister_class(ImportMD2)

if __name__ == "__main__":
    register()
