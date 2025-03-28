import bpy
import bmesh
from mathutils import Vector
import math

def fill_closed_loops(bm, edges):
    """
    Fills closed shapes formed by edges, treating them as independent rings and creating faces.
    """
    loops = []
    visited_edges = set()

    for edge in edges:
        if edge not in visited_edges:
            loop = [edge]
            visited_edges.add(edge)

            # Loop around the edges to find all connected edges
            while True:
                next_edge = None
                for e in edges:
                    if e not in visited_edges:
                        if any([v in edge.verts for v in e.verts]):
                            next_edge = e
                            visited_edges.add(e)
                            break
                if next_edge:
                    loop.append(next_edge)
                    edge = next_edge
                else:
                    break

            loops.append(loop)

    # Create faces from each loop
    for loop in loops:
        bmesh.ops.edgeloop_fill(bm, edges=loop)
            

def make_disk(bm, edges, direction):
    fill_closed_loops(bm, edges[:])
    extrude_result = bmesh.ops.extrude_edge_only(bm, edges=edges)
    new_verts = [v for v in extrude_result["geom"] if isinstance(v, bmesh.types.BMVert)]
    new_edges = [e for e in extrude_result["geom"] if isinstance(e, bmesh.types.BMEdge)]
    bmesh.ops.translate(bm, vec=direction, verts=new_verts)
    fill_closed_loops(bm, new_edges)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)


def create_collection(name):
    for myCol in bpy.data.collections:
        if myCol.name == name:
            for obj in myCol.objects:
                bpy.data.objects.remove(obj, do_unlink=True)
            return myCol
    myCol = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(myCol)
    return myCol


def create_atlas(collection):
    for i, object in enumerate(collection.objects):
        object.location = (i, 0, 0)


def split_model_to_disks(target_model_name, step, axis, do_create_atlas = False):  
    
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
        
    collection = create_collection("Disks")
    
    for i, position in enumerate(slice_positions):
        new_obj = obj.copy()
        new_obj.data = obj.data.copy()
        collection.objects.link(new_obj)
        new_obj.name = f"{obj.name}-({i})"
        
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
    
    if do_create_atlas:
        create_atlas(collection)


split_model_to_disks("Big cat statue", 0.008823529, 'Y', True)