import bpy
import bmesh
from mathutils import Vector
import math

def make_disk(bm, edges, direction):
    bmesh.ops.edgeloop_fill(bm, edges=edges[:])
    extrude_result = bmesh.ops.extrude_edge_only(bm, edges=edges)
    new_verts = [v for v in extrude_result["geom"] if isinstance(v, bmesh.types.BMVert)]
    new_edges = [e for e in extrude_result["geom"] if isinstance(e, bmesh.types.BMEdge)]
    bmesh.ops.translate(bm, vec=direction, verts=new_verts)
    bmesh.ops.bridge_loops(bm, edges=new_edges[:])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bmesh.ops.edgeloop_fill(bm, edges=new_edges[:])


def split_model_to_disks(target_model_name, step, axis='Z'):  
    
    obj = bpy.data.objects.get(target_model_name)
    if not obj:
        print(f"Object '{target_model_name}' not found!")
        return
    
    # Apply transformations
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    axis_index = {'X': 0, 'Y': 1, 'Z': 2}.get(axis.upper(), 2)
    
    slice_positions = []
    min_bound = obj.location[axis_index] + min(v[axis_index] for v in obj.bound_box)
    max_bound = obj.location[axis_index] + max(v[axis_index] for v in obj.bound_box)
    length = max_bound - min_bound
    iters = int(math.ceil(length / step))
    for i in range(iters):
        slice_positions.append(min_bound + i * step)
    
    for position in slice_positions:
        obj.select_set(True)
        bpy.ops.object.duplicate()
        new_obj = bpy.context.selected_objects[0]
        
        bpy.context.view_layer.objects.active = new_obj
        bpy.ops.object.mode_set(mode='EDIT')
        bm = bmesh.from_edit_mesh(new_obj.data)
        
        plane_co = Vector([position if i == axis_index else 0 for i in range(3)])
        plane_no = Vector([1 if i == axis_index else 0 for i in range(3)])
        
        bmesh.ops.bisect_plane(
            bm,
            geom=bm.verts[:] + bm.edges[:] + bm.faces[:],
            plane_co=plane_co,
            plane_no=plane_no,
            clear_outer=True,
            clear_inner=True
        )
        make_disk(bm, bm.edges, Vector([step if i == axis_index else 0 for i in range(3)]))
        
        bmesh.update_edit_mesh(new_obj.data)
        bpy.ops.object.mode_set(mode='OBJECT')
    
    print("Model bisected at specified positions")


split_model_to_disks("Sphere", 0.1, axis='Y')
