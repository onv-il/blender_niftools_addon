import bpy
import math
import mathutils

import io_scene_niftools.modules.nif_export.particle.modifier as Modifier

from nifgen.formats.nif import classes as NifClasses

from io_scene_niftools.utils.logging import NifLog, NifError
from io_scene_niftools.utils.math import color_blender_to_nif

from io_scene_niftools.modules.nif_export.block_registry import block_store

from io_scene_niftools.modules.nif_export.object import DICT_NAMES
from io_scene_niftools.modules.nif_export.geometry import Geometry
from io_scene_niftools.modules.nif_export.property.texture.common import get_input_node_of_type

class Emitter:
    def __init__(self):
        self.target_game = bpy.context.scene.niftools_scene.game
        self.fps = bpy.context.scene.render.fps

        self.geometry_helper = Geometry()

    def export_ni_p_sys_emitter(self, b_p_obj, b_particle_system, ni_modifier_type, order, n_ni_particle_system):
        
        ni_p_sys_emitter = Modifier.create_ni_p_sys_modifier(b_p_obj, ni_modifier_type, order, n_ni_particle_system)

        b_particle_system_settings = b_particle_system.settings

        b_material = b_p_obj.active_material

        b_x_velocity = b_particle_system_settings.object_align_factor[0]
        b_y_velocity = b_particle_system_settings.object_align_factor[1]
        b_z_velocity = b_particle_system_settings.object_align_factor[2]

        b_particle_speed = math.sqrt(abs(b_x_velocity ** 2 + b_y_velocity ** 2 + b_z_velocity ** 2))

        ni_p_sys_emitter.speed = b_particle_speed
        ni_p_sys_emitter.speed_variation = b_particle_system_settings.factor_random * b_particle_speed

        # ai slop math

        rx = b_p_obj.rotation_euler[0]
        ry = b_p_obj.rotation_euler[1]
        rz = b_p_obj.rotation_euler[2]

        dx =  math.sin(ry) * math.cos(rx)
        dy =  math.cos(ry) * math.cos(rx)
        dz =  math.sin(rx)

        object_vector_normalize = mathutils.Vector((rx, ry, rz))
        object_vector_normalize.normalize()

        b_particle_declination = math.acos(object_vector_normalize.z)
        b_particle_planar_angle = math.atan2(object_vector_normalize.x, object_vector_normalize.y)

        ni_p_sys_emitter.declination = b_particle_declination
        ni_p_sys_emitter.declination_variation = b_particle_declination * b_particle_system_settings.factor_random

        ni_p_sys_emitter.planar_angle = b_particle_planar_angle
        ni_p_sys_emitter.planar_angle_variation = b_particle_planar_angle * b_particle_system_settings.factor_random

        principled_bsdf = b_material.node_tree.nodes["Principled BSDF"]
        
        color_input = principled_bsdf.inputs[0]
        alpha_input = principled_bsdf.inputs[4]

        b_color_node = get_input_node_of_type(color_input, bpy.types.ShaderNodeRGB)
        b_alpha_node = get_input_node_of_type(alpha_input, bpy.types.ShaderNodeValue)

        b_color_value = None
        b_alpha_value = None

        if b_color_node:
            b_color_value = b_color_node.outputs[0].default_value
        else:
            b_color_value = color_input.default_value

        if b_alpha_node:
            b_alpha_value = b_alpha_node.outputs[0].default_value
        else:
            b_alpha_value = alpha_input.default_value

        b_color_object = mathutils.Color(b_color_value[0:3]).from_scene_linear_to_srgb()

        color_blender_to_nif(ni_p_sys_emitter.initial_color, (b_color_object[0], b_color_object[1], b_color_object[2], b_alpha_value))

        ni_p_sys_emitter.initial_radius = math.ceil(b_particle_system_settings.display_size / 2)
        ni_p_sys_emitter.radius_variation = math.ceil(b_particle_system_settings.size_random * ni_p_sys_emitter.initial_radius)

        ni_p_sys_emitter.life_span = b_particle_system_settings.lifetime / self.fps
        ni_p_sys_emitter.life_span_variation = b_particle_system_settings.lifetime_random / self.fps

        ni_p_sys_emitter.emitter_object = DICT_NAMES[b_p_obj.parent.name]

        return ni_p_sys_emitter

    def export_ni_p_sys_sphere_emitter(self, b_p_obj, b_particle_system, nif_particle_settings, n_ni_particle_system):
        ni_p_sys_sphere_emitter = self.export_ni_p_sys_emitter(b_p_obj, b_particle_system, "NiPSysSphereEmitter", NifClasses.NiPSysModifierOrder.ORDER_EMITTER, n_ni_particle_system)
        return ni_p_sys_sphere_emitter
    
    def export_ni_p_sys_box_emitter(self, b_p_obj, b_particle_system, nif_particle_settings, n_ni_particle_system):
        ni_p_sys_box_emitter = self.export_ni_p_sys_emitter(b_p_obj, b_particle_system, "NiPSysBoxEmitter", NifClasses.NiPSysModifierOrder.ORDER_EMITTER, n_ni_particle_system)
        return ni_p_sys_box_emitter
    
    def export_ni_p_sys_cylinder_emitter(self, b_p_obj, b_particle_system, nif_particle_settings, n_ni_particle_system):
        ni_p_sys_cylinder_emitter = self.export_ni_p_sys_emitter(b_p_obj, b_particle_system, "NiPSysCylinderEmitter", NifClasses.NiPSysModifierOrder.ORDER_EMITTER, n_ni_particle_system)
        return ni_p_sys_cylinder_emitter
    
    def export_ni_p_sys_mesh_emitter(self, b_p_obj, b_particle_system, nif_particle_settings, n_ni_particle_system, n_root_node):
        b_emitter_object = nif_particle_settings.particle_emitter_object

        if b_emitter_object is None:
            raise NifError(f"{b_particle_system.name} does not have a emitter object!")
        
        if b_emitter_object.type != 'MESH':
            raise NifError(f"NiPSysMeshEmitter {b_particle_system.name}'s emitter object must be a mesh")

        ni_p_sys_mesh_emitter = self.export_ni_p_sys_emitter(b_p_obj, b_particle_system, "NiPSysMeshEmitter", NifClasses.NiPSysModifierOrder.ORDER_EMITTER, n_ni_particle_system)

        n_emitter_parent = block_store.create_block("NiNode")
        n_emitter_parent.name = f"EmitterMesh-{ni_p_sys_mesh_emitter.name}"

        ni_emitter_mesh = self.geometry_helper.export_geometry(b_emitter_object, n_emitter_parent, n_root_node)

        ni_p_sys_mesh_emitter.num_emitter_meshes = 1
        ni_p_sys_mesh_emitter.emitter_meshes.append(ni_emitter_mesh)

        n_parent_node = DICT_NAMES[b_p_obj.parent.name]

        n_parent_node.add_child(n_emitter_parent)

        return ni_p_sys_mesh_emitter
    
    def export_bs_p_sys_array_emitter(self, b_p_obj, b_particle_system, nif_particle_settings, n_ni_particle_system):
        b_emitter_object = nif_particle_settings.particle_emitter_object

        if b_emitter_object is None:
            raise NifError(f"{b_particle_system.name} does not have a emitter object!")
        
        if b_emitter_object.type != 'EMPTY':
            raise NifError(f"BSPSysArrayEmitter {b_particle_system.name}'s emitter object must be an empty!")

        ni_p_sys_array_emitter = self.export_ni_p_sys_emitter(b_p_obj, b_particle_system, "BSPSysArrayEmitter", NifClasses.NiPSysModifierOrder.ORDER_EMITTER, n_ni_particle_system)

        ni_p_sys_array_emitter.emitter_object = DICT_NAMES[b_emitter_object.name]

        return ni_p_sys_array_emitter