"""Classes for exporting NIF particle blocks."""
# ***** BEGIN LICENSE BLOCK *****
#
# Copyright © 2025 NIF File Format Library and Tools contributors.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#    * Redistributions of source code must retain the above copyright
#      notice, this list of conditions and the following disclaimer.
#
#    * Redistributions in binary form must reproduce the above
#      copyright notice, this list of conditions and the following
#      disclaimer in the documentation and/or other materials provided
#      with the distribution.
#
#    * Neither the name of the NIF File Format Library and Tools
#      project nor the names of its contributors may be used to endorse
#      or promote products derived from this software without specific
#      prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# ***** END LICENSE BLOCK *****

import bpy
import math

import io_scene_niftools.modules.nif_export.particle.modifier as Modifier

from nifgen.formats.nif import classes as NifClasses

from io_scene_niftools.utils.logging import NifLog, NifError

from io_scene_niftools.modules.nif_export.block_registry import block_store

from io_scene_niftools.modules.nif_export.particle.emitter import Emitter

from io_scene_niftools.modules.nif_export.property.material import MaterialProperty
from io_scene_niftools.modules.nif_export.property.object import ObjectProperty
from io_scene_niftools.modules.nif_export.property.texture import TextureProperty

from io_scene_niftools.modules.nif_export.property.texture.common import get_input_node_of_type

from io_scene_niftools.modules.nif_export.object import DICT_NAMES


class Particle:
    """Main interface class for exporting NIF particle blocks."""

    def __init__(self):
        self.target_game = bpy.context.scene.niftools_scene.game
        self.fps = bpy.context.scene.render.fps

        self.material_property_helper = MaterialProperty()
        self.object_property_helper = ObjectProperty()
        self.texture_property_helper = TextureProperty()

        self.emitter_helper = Emitter()
        self.modifier_helper = Modifier.Modifier()

    def export_particles(self, b_particle_objects, b_force_field_objects, n_root_node):
        """Export particle blocks."""

        for b_p_obj in b_particle_objects:
            if not b_p_obj.parent:
                NifLog.warn(f"Particle object {b_p_obj.name} has no parent! "
                            f"It will not be exported.")
                continue

            n_parent_node = DICT_NAMES[b_p_obj.parent.name]

            for b_particle_system in b_p_obj.particle_systems:
                b_particle_system_settings = b_particle_system.settings
                nif_particle_settings = b_particle_system_settings.nif_particle_system
                b_material = b_p_obj.active_material

                n_ni_particle_system = self.export_base_ni_particle_system(b_p_obj, b_particle_system, nif_particle_settings, b_material, n_parent_node, n_root_node)

                for b_force_field_object in b_force_field_objects:
                    field_settings = b_force_field_object.field

                    if field_settings.type == 'VORTEX':
                        vortex_modifier = self.modifier_helper.export_ni_p_sys_vortex_field_modifier(b_force_field_object, b_particle_system, n_ni_particle_system)
                        Modifier.add_modifier(n_ni_particle_system, vortex_modifier)
                    elif field_settings.type == 'DRAG':
                        drag_modifier = self.modifier_helper.export_ni_p_sys_drag_field_modifier(b_force_field_object, b_particle_system, n_ni_particle_system)
                        Modifier.add_modifier(n_ni_particle_system, drag_modifier)
                    elif field_settings.type == 'TURBULENCE':
                        turbulence_modifier = self.modifier_helper.export_ni_p_sys_turbulence_field_modifier(b_force_field_object, b_particle_system, n_ni_particle_system)
                        Modifier.add_modifier(n_ni_particle_system, turbulence_modifier)
                    elif field_settings.type == 'WIND':
                        air_modifier = self.modifier_helper.export_ni_p_sys_air_field_modifier(b_force_field_object, b_particle_system, n_ni_particle_system)
                        Modifier.add_modifier(n_ni_particle_system, air_modifier)
                    elif field_settings.type == 'FORCE':
                        if field_settings.use_gravity_falloff and bpy.context.scene.use_gravity:
                            gravity_modifier = self.modifier_helper.export_ni_p_sys_gravity_field_modifier(b_force_field_object, b_particle_system, n_ni_particle_system)
                            Modifier.add_modifier(n_ni_particle_system, gravity_modifier)
                        
                if b_particle_system_settings.use_rotations:
                    ni_p_sys_rotation_modifier = self.modifier_helper.export_ni_p_sys_rotation_modifier(b_p_obj, b_particle_system, nif_particle_settings, n_ni_particle_system)
                    Modifier.add_modifier(n_ni_particle_system, ni_p_sys_rotation_modifier)

                if b_particle_system_settings.object_factor != 0:
                    bs_parent_velocity_modifier = self.modifier_helper.export_bs_parent_velocity_modifier(b_p_obj, b_particle_system, n_ni_particle_system)
                    Modifier.add_modifier(n_ni_particle_system, bs_parent_velocity_modifier)

                if b_particle_system_settings.effector_weights.wind != 0:
                    bs_wind_modifier = self.modifier_helper.export_bs_wind_modifier(b_p_obj, b_particle_system, n_ni_particle_system)
                    Modifier.add_modifier(n_ni_particle_system, bs_wind_modifier)

    # export a particle system with the bare minimum functionality
    def export_base_ni_particle_system(self, b_p_obj, b_particle_system, nif_particle_settings, b_material, n_parent_node, n_root_node):
        n_ni_particle_system = block_store.create_block(nif_particle_settings.particle_system_type, b_p_obj)
        n_ni_particle_system.flags = b_p_obj.nif_object.flags
        n_ni_particle_system.name = b_p_obj.name

        DICT_NAMES[b_p_obj.name] = n_ni_particle_system

        n_emitter = None

        if nif_particle_settings.particle_emitter_type == "NiPSysSphereEmitter":
            n_emitter = self.emitter_helper.export_ni_p_sys_sphere_emitter(b_p_obj, b_particle_system, nif_particle_settings, n_ni_particle_system)
        elif nif_particle_settings.particle_emitter_type == "NiPSysBoxEmitter":
            n_emitter = self.emitter_helper.export_ni_p_sys_box_emitter(b_p_obj, b_particle_system, nif_particle_settings, n_ni_particle_system)
        elif nif_particle_settings.particle_emitter_type == "NiPSysCylinderEmitter":
            n_emitter = self.emitter_helper.export_ni_p_sys_cylinder_emitter(b_p_obj, b_particle_system, nif_particle_settings, n_ni_particle_system)
        elif nif_particle_settings.particle_emitter_type == "NiPSysMeshEmitter":
            n_emitter = self.emitter_helper.export_ni_p_sys_mesh_emitter(b_p_obj, b_particle_system, nif_particle_settings, n_ni_particle_system, n_root_node)
        else:
            n_emitter = self.emitter_helper.export_bs_p_sys_array_emitter(b_p_obj, b_particle_system, nif_particle_settings, n_ni_particle_system)
        
        ni_p_sys_data = self.export_ni_p_sys_data(b_p_obj, b_material, b_particle_system, n_ni_particle_system)

        ni_p_sys_emitter_ctlr = block_store.create_block("NiPSysEmitterCtlr")
        ni_p_sys_emitter_ctlr.modifier_name = n_emitter.name

        ni_float_interpolator = block_store.create_block("NiFloatInterpolator")
        ni_bool_interpolator = block_store.create_block("NiBoolInterpolator")

        ni_p_sys_emitter_ctlr.interpolator = ni_float_interpolator
        ni_p_sys_emitter_ctlr.visibility_interpolator = ni_bool_interpolator

        ni_p_sys_emitter_ctlr.start_time = 0
        ni_p_sys_emitter_ctlr.stop_time = 0

        ni_p_sys_update_ctlr = block_store.create_block("NiPSysUpdateCtlr")
        ni_p_sys_update_ctlr.start_time = 0
        ni_p_sys_update_ctlr.stop_time = 0

        n_ni_particle_system.add_controller(ni_p_sys_emitter_ctlr)
        n_ni_particle_system.add_controller(ni_p_sys_update_ctlr)

        if isinstance(n_ni_particle_system, NifClasses.BSStripParticleSystem):
            n_strip_update_modifier = self.modifier_helper.export_bs_p_sys_strip_update_modifier(b_p_obj, nif_particle_settings, n_ni_particle_system)
            Modifier.add_modifier(n_ni_particle_system, n_strip_update_modifier)

        self.object_property_helper.export_alpha_property(b_material, n_ni_particle_system)
        self.material_property_helper.export_ni_material_property(b_material, n_ni_particle_system)
        self.texture_property_helper.export_texture_properties(b_material, n_ni_particle_system)

        ni_p_sys_position_modifier = self.modifier_helper.export_ni_p_sys_position_modifier(b_p_obj, nif_particle_settings, n_ni_particle_system)
        ni_p_sys_bound_update_modifier = self.modifier_helper.export_ni_p_sys_bound_update_modifier(b_p_obj, nif_particle_settings, n_ni_particle_system)
        ni_p_sys_spawn_modifier = self.modifier_helper.export_ni_p_sys_spawn_modifier(b_p_obj, b_particle_system, n_ni_particle_system)
        ni_p_sys_age_death_modifier = self.modifier_helper.export_ni_p_sys_age_death_modifier(b_p_obj, nif_particle_settings, n_ni_particle_system, ni_p_sys_spawn_modifier)

        Modifier.add_modifier(n_ni_particle_system, n_emitter)
        Modifier.add_modifier(n_ni_particle_system, ni_p_sys_position_modifier)
        Modifier.add_modifier(n_ni_particle_system, ni_p_sys_bound_update_modifier)
        Modifier.add_modifier(n_ni_particle_system, ni_p_sys_spawn_modifier)
        Modifier.add_modifier(n_ni_particle_system, ni_p_sys_age_death_modifier)

        n_parent_node.add_child(n_ni_particle_system)

        return n_ni_particle_system

    @staticmethod
    def set_subtexture_offsets(n_ni_p_sys_data, b_particle_system, b_material, num_subtexture_offsets):
        # https://geckwiki.com/index.php?title=NiParticleSystem#NiPSysData
        # Subtexture Offsets: Sections are split into four vectors and start from the upper-left corner of the texture.
        # X and Z specify the horizontal and vertical position and positive values move rightward and downward respectively.
        # Y and W define the height and width of the section in relation to the texture's height and width, respectively.

        principled_bsdf = next((node for node in b_material.node_tree.nodes if isinstance(node, bpy.types.ShaderNodeBsdfPrincipled)), None)

        if principled_bsdf is None:
            raise NifError(f"{b_material.name} must have a single Principled BSDF for particle emitter export!")

        color_input = principled_bsdf.inputs[0]
        alpha_input = principled_bsdf.inputs[4]

        b_image_node = get_input_node_of_type(color_input, bpy.types.ShaderNodeTexImage)

        if b_image_node is None:
            b_image_node = get_input_node_of_type(alpha_input, bpy.types.ShaderNodeTexImage)

            if b_image_node is None:
                raise NifError(f"{b_material.name} needs a image node connected to a color or alpha socket to export particle systems!")
        
        #ai slop programming

        image_size_x, image_size_y = b_image_node.image.size

        cols = int(math.sqrt(num_subtexture_offsets))
        rows = int(math.sqrt(num_subtexture_offsets))

        if num_subtexture_offsets == 2:
            if image_size_x > image_size_y:
                rows += 1
            elif image_size_x < image_size_y:
                cols += 1
            else:
                NifLog.warn(f"{b_image_node.name} has a square resolution while {b_particle_system.name}'s Subtexture Offset Count is set to 2.\nThis may not behave predictably or function at all.")

        sub_width = 1.0 / cols
        sub_height = 1.0 / rows

        offsets = []

        for row in range(rows):
            for col in range(cols):
                x = col * sub_width
                z = row * sub_height
                y = sub_height
                w = sub_width

                offset = (x, y, z, w)

                offsets.append(offset)

        n_ni_p_sys_data.num_subtexture_offsets = len(offsets)
        n_ni_p_sys_data.reset_field("subtexture_offsets")

        for n_offset, b_offset in zip(n_ni_p_sys_data.subtexture_offsets, offsets):
            n_offset.x = b_offset[0]
            n_offset.y = b_offset[1]
            n_offset.z = b_offset[2]
            n_offset.w = b_offset[3]

    def export_ni_p_sys_data(self, b_p_obj, b_material, b_particle_system, n_ni_particle_system):
        b_particle_system_settings = b_particle_system.settings
        nif_particle_settings = b_particle_system_settings.nif_particle_system

        n_ni_p_sys_data = None

        if isinstance(n_ni_particle_system, NifClasses.BSStripParticleSystem):
            n_ni_p_sys_data = block_store.create_block("BSStripPSysData")
            n_ni_p_sys_data.max_point_count = nif_particle_settings.bs_strip_max_point_count

        else:
            n_ni_p_sys_data = block_store.create_block("NiPSysData")
        
        n_ni_p_sys_data.num_particles = b_particle_system_settings.count

        n_ni_p_sys_data.has_vertices = True
        n_ni_p_sys_data.reset_field("vertices")

        n_ni_p_sys_data.has_normals = False
        n_ni_p_sys_data.bs_data_flags.has_tangents = True if n_ni_p_sys_data.has_normals == True else False

        n_ni_particle_system.data = n_ni_p_sys_data

        num_subtexture_offsets = nif_particle_settings.num_subtexture_offsets

        if num_subtexture_offsets > 0:
            if num_subtexture_offsets % 2 != 0:
                raise NifError(f"{b_particle_system.name}'s Subtexture Offset Count must be zero or a multiple of two!")

            n_ni_p_sys_data.has_texture_indices = True
            self.set_subtexture_offsets(n_ni_p_sys_data, b_particle_system, b_material, num_subtexture_offsets)

        
                
        return n_ni_p_sys_data
