import bpy
import bmesh
from mathutils import Vector

obj = bpy.context.active_object
bpy.ops.object.mode_set(mode="EDIT")
bm = bmesh.from_edit_mesh(obj.data)
bpy.ops.mesh.fill()