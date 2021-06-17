# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####
import bpy
import math

bl_info = {
    "name" : "Fast Lattice",
    "author" : "dskjal",
    "version" : (1, 0),
    "blender" : (2, 93, 0),
    "location" : "View3D > Toolshelf > Fast Lattice",
    "description" : "",
    "warning" : "",
    "wiki_url" : "",
    "tracker_url" : "",
    "category" : "Mesh"
}

vg_name = 'fast_lattice'

# return [xmin, xmax, ymin, ymax, zmin, zmax]
def get_bounding_box_world(vertices):
    x, y, z = vertices[0].co
    ret = [x, x, y, y, z, z]
    for v in vertices:
        x, y, z = v.co
        if ret[0] < x: ret[0] = x
        if ret[1] > x: ret[1] = x
        if ret[2] < y: ret[2] = y
        if ret[3] > y: ret[3] = y
        if ret[4] < z: ret[4] = z
        if ret[5] > z: ret[5] = z

    return ret

# return [xmin, xmax, ymin, ymax, zmin, zmax], is_select
# is_select is True when one or more vertices are selected
def get_bounding_box_world_select(object):
    vertices = [v for v in object.data.vertices if v.select]
    if not vertices:
        ret = get_bounding_box_world(object.data.vertices)
    else:
        ret = get_bounding_box_world(vertices=vertices)
    
    return (ret, not (not vertices))

class DSKJAL_OT_SET_LATTICE(bpy.types.Operator):
    bl_idname = "dskjal.createlattice"
    bl_label = "Create Lattice"
    
    def execute(self, context):
        # create aabb
        o = context.active_object
        is_select_mode = False
        if o.mode == 'EDIT':
            bpy.ops.object.mode_set(mode='OBJECT')
            aabb, is_select_mode = get_bounding_box_world_select(object=o)

            # add vertex group
            if is_select_mode:
                vg = o.vertex_groups.new(name=vg_name)
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.object.vertex_group_assign()
                bpy.ops.object.mode_set(mode='OBJECT')

        else:
            aabb = get_bounding_box_world(vertices=o.data.vertices)

        # set lattice
        bpy.ops.object.add(type='LATTICE')
        lattice = context.active_object
        lattice.name = vg_name
        xmin, xmax, ymin, ymax, zmin, zmax = aabb
        lattice.location = (xmin + (xmax-xmin)*0.5, ymin + (ymax-ymin)*0.5, zmin + (zmax-zmin)*0.5)
        lattice.scale = (xmax-xmin, ymax-ymin, zmax-zmin)

        # lattice modifier
        lattice_mod = o.modifiers.new(name='Fast Lattice', type='LATTICE')
        lattice_mod.object = lattice
        if is_select_mode:
            lattice_mod.vertex_group = vg.name
        
        bpy.ops.object.mode_set(mode='EDIT')
        return {'FINISHED'}

class DSKJAL_OT_APPLY_LATTICE(bpy.types.Operator):
    bl_idname = "dskjal.applylattice"
    bl_label = "Apply"
    
    def execute(self, context):
        lattice = context.active_object
        old_mode = lattice.mode
        bpy.ops.object.mode_set(mode='OBJECT')

        # find lattice mesh
        modifier = None
        object = None
        for o in bpy.data.objects:
            for m in o.modifiers:
                if m.type == 'LATTICE' and m.object == lattice:
                    bpy.context.view_layer.objects.active = o
                    object = o
                    modifier = m
                    break

        del_vg = modifier.vertex_group
        bpy.ops.object.modifier_apply(modifier=modifier.name)
        if del_vg:
            bpy.ops.object.vertex_group_set_active(group=del_vg)
            bpy.ops.object.vertex_group_remove(all=False, all_unlocked=False)

        # delete lattice
        bpy.context.view_layer.objects.active = lattice
        bpy.ops.object.delete(use_global=False)
        
        if old_mode == 'EDIT':
            bpy.context.view_layer.objects.active = object
            bpy.ops.object.mode_set(mode='EDIT')
        
        return {'FINISHED'}

class DSKJAL_PT_FAST_LATTICE_UI(bpy.types.Panel):
    bl_label = 'Fast Lattice'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Tool'
    
    @classmethod
    def poll(self, context):
        o = context.object
        return o and o.type in ('MESH', 'LATTICE') and o.mode in ('EDIT', 'OBJECT')
    
    def draw(self, context):
        o = context.object
        if o.type == 'LATTICE' and o.name.startswith(vg_name):
            col = self.layout.column()
            col.use_property_split = True
            col.prop(o.data, 'points_u')
            col.prop(o.data, 'points_v')
            col.prop(o.data, 'points_w')
            col.separator()
            col.prop(o.data, 'interpolation_type_u')
            col.prop(o.data, 'interpolation_type_v')
            col.prop(o.data, 'interpolation_type_w')
            col.separator()

            self.layout.operator('dskjal.applylattice')
        else:
            self.layout.operator('dskjal.createlattice')

classes = (
    DSKJAL_OT_SET_LATTICE,
    DSKJAL_OT_APPLY_LATTICE,
    DSKJAL_PT_FAST_LATTICE_UI
)
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()