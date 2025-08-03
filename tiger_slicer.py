import bpy
import bmesh
from mathutils import Vector
import math

cm2unit = 1
unit2cm = 1

def fill_closed_loops(bm, edges):
    
    for edge in edges:
        edge.select = True

    bpy.ops.mesh.fill()
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    
    for edge in bm.edges: # deselect everything
        edge.select = False
            

def make_disk(bm, edges, direction):
    
    input_edges = [e for e in edges]
    
    fill_closed_loops(bm, edges[:])
    
    extrude_result = bmesh.ops.extrude_edge_only(bm, edges=input_edges)
    
    new_verts = [v for v in extrude_result["geom"] if isinstance(v, bmesh.types.BMVert)]
    new_edges = [e for e in extrude_result["geom"] if isinstance(e, bmesh.types.BMEdge)]
    bmesh.ops.translate(bm, vec=direction, verts=new_verts)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
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


def create_atlas(collection, axis):
    def create_pos(a, b, axis):
        if axis == "X":
            return (0, a, b)
        if axis == "Y":
            return (a, 0, b)
        if axis == "Z":
            return (a, b, 0)
    
    x_factor = 0.4
    y_factor = 1.05
    num = len(collection.objects)
    width = 11
    height = math.ceil(num / width)
    for y in range(height):
        for x in range(width):
            i = x + y * width
            if i < num:
                collection.objects[i].location = create_pos(x * x_factor, y * y_factor, axis)
    
    # the plane object with a shader that shows how the 
    # physical size corresponds to virtual size
    scaleref = bpy.data.objects.get("scale_reference")
    if not scaleref:
        print("no scale reference object found")
        return
    
    material = scaleref.material_slots[0].material
    if not material:
        print("no scale reference material found")
        return
    
    if material.use_nodes and material.node_tree.nodes is not None:
        for node in material.node_tree.nodes:
            if node.label == "Scale" and node.type == "VALUE":
                node.outputs["Value"].default_value = unit2cm
        


def print_metrics(obj):
    for axis in ('X', 'Y', 'Z'):
        axis_index = {'X': 0, 'Y': 1, 'Z': 2}.get(axis.upper(), 2)
        min_bound = obj.location[axis_index] + min(v[axis_index] for v in obj.bound_box)
        max_bound = obj.location[axis_index] + max(v[axis_index] for v in obj.bound_box)
        length = max_bound - min_bound
        print(f"length in {axis} axis is {length}u ({min_bound} to {max_bound}) ({length * unit2cm}cm)")


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
    iters = abs(int(math.ceil(length / step)))
    print(f"total length: {length}u with {iters} disks")
    for i in range(iters):
        slice_positions.append(min_bound + i * step)
        
    collection = create_collection("Disks")
    
    print_metrics(obj)
    
    for i, position in enumerate(slice_positions):
        new_obj = obj.copy()
        new_obj.data = obj.data.copy()
        collection.objects.link(new_obj)
        new_obj.name = f"{obj.name}-({i})"
        new_obj.hide_render = False
        
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
        create_atlas(collection, axis)


def set_scale(cm, units):
    global cm2unit, unit2cm
    cm2unit = units / cm
    unit2cm = 1.0 / cm2unit
    print(f"cm2unit = {cm2unit}")
    print(f"unit2cm = {unit2cm}")


def real_world_to_blender(cm):
    return cm * cm2unit


def blender_to_real_world(units):
    return units * unit2cm


set_scale(17, 1.1769512295722961)
step = real_world_to_blender(0.2)
print("step is", step)
print("3.7mm is", real_world_to_blender(0.37))
print("current stick is", blender_to_real_world(0.02))

split_model_to_disks("tiger", step, 'Z', False)