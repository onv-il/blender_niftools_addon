import bpy
import math
import mathutils

from nifgen.formats.nif import classes as NifClasses

from io_scene_niftools.modules.nif_export.object import DICT_NAMES
from io_scene_niftools.modules.nif_export.particle.modifier import Modifier
from io_scene_niftools.modules.nif_export.property.texture.common import get_output_node_of_type

class Emitter:
    def __init__(self):
        self.target_game = bpy.context.scene.niftools_scene.game
        self.fps = bpy.context.scene.render.fps

        self.modifier_helper = Modifier()

    def export_ni_p_sys_emitter(self, b_p_obj, b_particle_system, ni_modifier_type, order, n_ni_particle_system):
        ni_p_sys_emitter = self.modifier_helper.create_ni_p_sys_modifier(b_p_obj, ni_modifier_type, order, n_ni_particle_system)

        b_particle_system_settings = b_particle_system.settings

        ni_p_sys_emitter.speed = b_particle_system_settings.normal_factor
        ni_p_sys_emitter.speed_variation = b_particle_system_settings.factor_random

        b_material = b_p_obj.active_material

        principled_bsdf = b_material.node_tree.nodes["Principled BSDF"]
        color_input = principled_bsdf.inputs[0]
        alpha_input = principled_bsdf.inputs[4]

        b_color_output = color_input or get_output_node_of_type(color_input, bpy.types.ShaderNodeRGB)
        b_alpha_output = alpha_input or get_output_node_of_type(alpha_input, bpy.types.ShaderNodeValue)

        (ni_p_sys_emitter.initial_color.r, ni_p_sys_emitter.initial_color.g, ni_p_sys_emitter.initial_color.b, ni_p_sys_emitter.initial_color.a) = (1,1,1,1)

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
    
    def export_ni_p_sys_mesh_emitter(self, b_p_obj, b_particle_system, nif_particle_settings, n_ni_particle_system):
        ni_p_sys_mesh_emitter = self.export_ni_p_sys_emitter(b_p_obj, b_particle_system, "NiPSysMeshEmitter", NifClasses.NiPSysModifierOrder.ORDER_EMITTER, n_ni_particle_system)
        return ni_p_sys_mesh_emitter
    
    def export_bs_p_sys_array_emitter(self, b_p_obj, b_particle_system, nif_particle_settings, n_ni_particle_system):
        ni_p_sys_array_emitter = self.export_ni_p_sys_emitter(b_p_obj, b_particle_system, "BSPSysArrayEmitter", NifClasses.NiPSysModifierOrder.ORDER_EMITTER, n_ni_particle_system)
        return ni_p_sys_array_emitter