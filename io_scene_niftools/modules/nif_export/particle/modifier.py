import bpy
import math

from io_scene_niftools.modules.nif_export.block_registry import block_store
from nifgen.formats.nif import classes as NifClasses

from io_scene_niftools.modules.nif_export.object import DICT_NAMES

@staticmethod
def add_modifier(n_ni_particle_system, n_modifier):
    num_props = n_ni_particle_system.num_modifiers
    n_ni_particle_system.num_modifiers = num_props + 1

    n_ni_particle_system.modifiers.append(n_modifier)

@staticmethod
def create_ni_p_sys_modifier(b_p_obj, ni_modifier_type, order, n_ni_particle_system):
    ni_p_sys_modifier = block_store.create_block(ni_modifier_type)

    ni_p_sys_modifier.name = f"{b_p_obj.name}-{ni_modifier_type}"
    ni_p_sys_modifier.order = order
    ni_p_sys_modifier.active = True
    ni_p_sys_modifier.target = n_ni_particle_system

    return ni_p_sys_modifier

@staticmethod
def create_ni_p_sys_field_modifier(b_p_obj, ni_modifier_type, n_ni_particle_system):
    ni_p_sys_field_modifier = create_ni_p_sys_modifier(b_p_obj, ni_modifier_type, NifClasses.NiPSysModifierOrder.ORDER_FORCE, n_ni_particle_system)

    ni_p_sys_field_modifier.field_object = DICT_NAMES[b_p_obj.name]
    ni_p_sys_field_modifier.magnitude = b_p_obj.field.strength
    ni_p_sys_field_modifier.attenuation = b_p_obj.field.falloff_power

    ni_p_sys_field_modifier.use_max_distance = b_p_obj.field.use_max_distance
    ni_p_sys_field_modifier.max_distance = b_p_obj.field.distance_max

    return ni_p_sys_field_modifier

class Modifier:
    def __init__(self):
        self.niftools_scene = bpy.context.scene.niftools_scene
        self.target_game = bpy.context.scene.niftools_scene.game
        self.fps = bpy.context.scene.render.fps
    
    def export_bs_p_sys_strip_update_modifier(self, b_p_obj, nif_particle_settings, n_ni_particle_system):
        
        priority = NifClasses.NiPSysModifierOrder.ORDER_FO3_BSSTRIPUPDATE if self.niftools_scene.is_fo3() else NifClasses.NiPSysModifierOrder.ORDER_SK_BSSTRIPUPDATE
 
        bs_p_sys_strip_update_modifier = create_ni_p_sys_modifier(b_p_obj, "BSPSysStripUpdateModifier", priority, n_ni_particle_system)
        bs_p_sys_strip_update_modifier.update_delta_time = 1 / self.fps

        return bs_p_sys_strip_update_modifier

    def export_ni_p_sys_bound_update_modifier(self, b_p_obj, nif_particle_settings, n_ni_particle_system):
        ni_p_sys_bound_update_modifier = create_ni_p_sys_modifier(b_p_obj, "NiPSysBoundUpdateModifier", NifClasses.NiPSysModifierOrder.ORDER_BOUND_UPDATE, n_ni_particle_system)

        return ni_p_sys_bound_update_modifier
    
    def export_ni_p_sys_position_modifier(self, b_p_obj, nif_particle_settings, n_ni_particle_system):
        ni_p_sys_position_modifier = create_ni_p_sys_modifier(b_p_obj, "NiPSysPositionModifier", NifClasses.NiPSysModifierOrder.ORDER_POS_UPDATE, n_ni_particle_system)

        return ni_p_sys_position_modifier

    def export_ni_p_sys_age_death_modifier(self, b_p_obj, nif_particle_settings, n_ni_particle_system, ni_p_sys_spawn_modifier):
        ni_p_sys_age_death_modifier = create_ni_p_sys_modifier(b_p_obj, "NiPSysAgeDeathModifier", NifClasses.NiPSysModifierOrder.ORDER_KILLOLDPARTICLES, n_ni_particle_system)


        ni_p_sys_age_death_modifier.spawn_modifier = ni_p_sys_spawn_modifier
        ni_p_sys_age_death_modifier.spawn_on_death = nif_particle_settings.spawn_on_death

        return ni_p_sys_age_death_modifier
    
    def export_ni_p_sys_spawn_modifier(self, b_p_obj, b_particle_system, n_ni_particle_system):
        b_particle_system_settings = b_particle_system.settings

        ni_p_sys_spawn_modifier = create_ni_p_sys_modifier(b_p_obj, "NiPSysSpawnModifier", NifClasses.NiPSysModifierOrder.ORDER_EMITTER, n_ni_particle_system)

        ni_p_sys_spawn_modifier.num_spawn_generations = b_particle_system_settings.nif_particle_system.num_spawn_generations
        ni_p_sys_spawn_modifier.percentage_spawned = b_particle_system_settings.nif_particle_system.percentage_spawned

        ni_p_sys_spawn_modifier.min_num_to_spawn = b_particle_system_settings.nif_particle_system.min_num_to_spawn
        ni_p_sys_spawn_modifier.max_num_to_spawn = b_particle_system_settings.nif_particle_system.max_num_to_spawn

        ni_p_sys_spawn_modifier.spawn_speed_variation = math.ceil(b_particle_system_settings.factor_random)
        ni_p_sys_spawn_modifier.spawn_dir_variation = math.ceil(b_particle_system_settings.rotation_factor_random)

        ni_p_sys_spawn_modifier.life_span = b_particle_system_settings.lifetime / self.fps
        ni_p_sys_spawn_modifier.life_span_variation = b_particle_system_settings.lifetime_random / self.fps

        return ni_p_sys_spawn_modifier

    def export_ni_p_sys_rotation_modifier(self, b_p_obj, b_particle_system, nif_particle_settings, n_ni_particle_system):
        b_particle_system_settings = b_particle_system.settings

        ni_p_sys_rotation_modifier = create_ni_p_sys_modifier(b_p_obj, "NiPSysRotationModifier", NifClasses.NiPSysModifierOrder.ORDER_GENERAL, n_ni_particle_system)

        ni_p_sys_rotation_modifier.rotation_speed = b_particle_system_settings.angular_velocity_factor
        ni_p_sys_rotation_modifier.rotation_speed_variation

        ni_p_sys_rotation_modifier.rotation_angle = math.radians(b_particle_system_settings.phase_factor * 180)

        phase_factor_random = b_particle_system_settings.phase_factor_random

        if phase_factor_random < 1:
            ni_p_sys_rotation_modifier.rotation_angle_variation = math.radians(phase_factor_random * 180)
        else:
            ni_p_sys_rotation_modifier.rotation_angle_variation = math.radians((phase_factor_random - 1) * 180)

        ni_p_sys_rotation_modifier.random_rot_speed_sign = nif_particle_settings.random_rot_speed_sign

        ni_p_sys_rotation_modifier.random_axis = True if b_particle_system_settings.angular_velocity_mode == 'VELOCITY' else False

        if b_particle_system_settings.rotation_mode.endswith("Y"):
            ni_p_sys_rotation_modifier.axis = (0, 1 ,0)
        elif b_particle_system_settings.rotation_mode.endswith("Z"):
            ni_p_sys_rotation_modifier.axis = (0, 0 ,1)
        else:
            ni_p_sys_rotation_modifier.axis = (1, 0,0)
        
        return ni_p_sys_rotation_modifier
    
    def export_bs_parent_velocity_modifier(self, b_p_obj, b_particle_system, n_ni_particle_system):
        b_particle_system_settings = b_particle_system.settings

        bs_parent_velocity_modifier = create_ni_p_sys_modifier(b_p_obj, "BSParentVelocityModifier", NifClasses.NiPSysModifierOrder.ORDER_GENERAL, n_ni_particle_system)

        bs_parent_velocity_modifier.damping = b_particle_system_settings.object_factor

        return bs_parent_velocity_modifier
    
    def export_bs_wind_modifier(self, b_p_obj, b_particle_system, n_ni_particle_system):
        b_particle_system_settings = b_particle_system.settings

        bs_wind_modifier = create_ni_p_sys_modifier(b_p_obj, "BSWindModifier", NifClasses.NiPSysModifierOrder.ORDER_GENERAL, n_ni_particle_system)

        bs_wind_modifier.strength = b_particle_system_settings.effector_weights.wind

        return bs_wind_modifier
    
    def export_ni_p_sys_color_modifier(self, b_p_obj, b_particle_system, n_ni_particle_system):
        b_particle_system_settings = b_particle_system.settings

        n_p_sys_color_modifier = create_ni_p_sys_modifier(b_p_obj, "NiPSysColorModifier", NifClasses.NiPSysModifierOrder.ORDER_GENERAL, n_ni_particle_system)

        return n_p_sys_color_modifier
    
    def export_bs_p_sys_subtex_modifier(self, b_p_obj, b_particle_system, n_ni_particle_system):
        b_particle_system_settings = b_particle_system.settings
        nif_particle_settings = b_particle_system_settings.nif_particle_system

        bs_p_sys_sub_modifier = create_ni_p_sys_modifier(b_p_obj, "BSPSysSubTexModifier", NifClasses.NiPSysModifierOrder.ORDER_GENERAL, n_ni_particle_system)

        bs_p_sys_sub_modifier.start_frame = 0
        bs_p_sys_sub_modifier.end_frame = nif_particle_settings.num_subtexture_offsets - 1

        bs_p_sys_sub_modifier.frame_count = nif_particle_settings.num_subtexture_offsets

        return bs_p_sys_sub_modifier
    
    def export_ni_p_sys_radial_field_modifier(self, b_p_obj, b_particle_system, n_ni_particle_system):
        ni_p_sys_radial_field_modifier = create_ni_p_sys_field_modifier(b_p_obj, "NiPSysRadialFieldModifier", n_ni_particle_system)

        ni_p_sys_radial_field_modifier.name = f"{b_p_obj.name}-RadialField"

        return ni_p_sys_radial_field_modifier
    
    def export_ni_p_sys_gravity_field_modifier(self, b_p_obj, b_particle_system, n_ni_particle_system):
        ni_p_sys_gravity_field_modifier = create_ni_p_sys_field_modifier(b_p_obj, "NiPSysGravityFieldModifier", n_ni_particle_system)

        b_gravity = bpy.context.scene.gravity

        ni_p_sys_gravity_field_modifier.name = f"{b_p_obj.name}-GravityField"

        ni_p_sys_gravity_field_modifier.magnitude = math.sqrt(abs(b_gravity[0] + b_gravity[1] + b_gravity[2]))
        ni_p_sys_gravity_field_modifier.direction.x, ni_p_sys_gravity_field_modifier.direction.y, ni_p_sys_gravity_field_modifier.direction.z  = (0, 0, 1)

        return ni_p_sys_gravity_field_modifier
    
    def export_ni_p_sys_turbulence_field_modifier(self, b_p_obj, b_particle_system, n_ni_particle_system):
        b_field_settings = b_p_obj.field

        ni_p_sys_turbulence_field_modifier = create_ni_p_sys_field_modifier(b_p_obj, "NiPSysTurbulenceFieldModifier", n_ni_particle_system)

        ni_p_sys_turbulence_field_modifier.name = f"{b_p_obj.name}-TurbulenceField"

        ni_p_sys_turbulence_field_modifier.frequency = bpy.context.scene.render.fps

        return ni_p_sys_turbulence_field_modifier
    
    def export_ni_p_sys_drag_field_modifier(self, b_p_obj, b_particle_system, n_ni_particle_system):
        ni_p_sys_drag_field_modifier = create_ni_p_sys_field_modifier(b_p_obj, "NiPSysDragFieldModifier", n_ni_particle_system)

        ni_p_sys_drag_field_modifier.name = f"{b_p_obj.name}-DragField"

        ni_p_sys_drag_field_modifier.use_direction = False

        return ni_p_sys_drag_field_modifier
    
    def export_ni_p_sys_air_field_modifier(self, b_p_obj, b_particle_system, n_ni_particle_system):
        b_field_settings = b_p_obj.field

        ni_p_sys_air_field_modifier = create_ni_p_sys_field_modifier(b_p_obj, "NiPSysAirFieldModifier", n_ni_particle_system)

        ni_p_sys_air_field_modifier.name = f"{b_p_obj.name}-AirField"

        ni_p_sys_air_field_modifier.direction = (0, 0, 1)

        if b_field_settings.flow > 1:
            ni_p_sys_air_field_modifier.inherit_velocity = 1
        elif b_field_settings.flow < 0:
            ni_p_sys_air_field_modifier.inherit_velocity = 0
        else:
            ni_p_sys_air_field_modifier.inherit_velocity = b_field_settings.flow

        if b_field_settings.apply_to_rotation:
            ni_p_sys_air_field_modifier.inherit_rotation = True

        if b_field_settings.use_radial_max:
            ni_p_sys_air_field_modifier.enable_spread = True
            ni_p_sys_air_field_modifier.spread = b_field_settings.radial_max

        return ni_p_sys_air_field_modifier
    
    def export_ni_p_sys_vortex_field_modifier(self, b_p_obj, b_particle_system, n_ni_particle_system):
        ni_p_sys_vortex_field_modifier = create_ni_p_sys_field_modifier(b_p_obj, "NiPSysVortexFieldModifier", n_ni_particle_system)

        ni_p_sys_vortex_field_modifier.direction = (0, 0, 1)

        return ni_p_sys_vortex_field_modifier