"""Main module for exporting shader animation blocks."""

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

from io_scene_niftools.modules.nif_export.animation.shader.shader_fo3 import export_fo3_effect_shader_animation

from io_scene_niftools.modules.nif_export.animation.common import AnimationCommon
from io_scene_niftools.modules.nif_export.block_registry import block_store

from io_scene_niftools.modules.nif_export.object import DICT_NAMES

from io_scene_niftools.utils.logging import NifError, NifLog
from nifgen.formats.nif import classes as NifClasses

class ShaderAnimation(AnimationCommon):

    def __init__(self):
        super().__init__()

        self.niftools_scene = bpy.context.scene.niftools_scene

    def export_shader_animations(self, b_controlled_blocks, n_ni_controller_sequence=None):
        """Export shader animations for given geometry."""

        scene_is_fo3 = self.niftools_scene.is_fo3()
        scene_is_skyrim = self.niftools_scene.is_skyrim()

        for b_controlled_block in b_controlled_blocks:
            b_strip, b_obj = b_controlled_block

            if b_obj.particle_systems:
                continue

            b_action = b_strip.action

            b_material = b_obj.active_material
            n_ni_geometry = DICT_NAMES[b_obj.name]

            n_shader_prop = None

            if scene_is_fo3:
                n_shader_prop = next((prop for prop in n_ni_geometry.properties if isinstance(prop, NifClasses.BSShaderProperty)), None)
            elif scene_is_skyrim:
                bs_shadertype = b_material.nif_shader.bs_shadertype

                if bs_shadertype == "BSEffectShaderProperty":
                    n_shader_prop = next((prop for prop in n_ni_geometry.properties if isinstance(prop, NifClasses.BSEffectShaderProperty)), None)
                else:
                    n_shader_prop = next((prop for prop in n_ni_geometry.properties if isinstance(prop, NifClasses.BSLightingShaderProperty)), None)

            if not n_shader_prop:
                NifLog.warn(
                    f"Object {b_obj.name} has no BSShaderProperty! "
                    f"Shader animation for {b_action.name} will not be exported "
                    f"(ensure that an unsupported shader property is not applied)."
                )
                continue
            
            if scene_is_fo3:
                export_fo3_effect_shader_animation(n_ni_geometry, n_shader_prop, b_material, b_action, n_ni_controller_sequence)
            elif scene_is_skyrim:
                self.export_skyrim_effect_shader_animation(n_shader_prop, b_material, b_action, n_ni_controller_sequence)

    def export_skyrim_effect_shader_animation(self, n_shader_prop, b_material, b_action, n_ni_controller_sequence=None):
        return
        # TODO [shader][animation] Do some form of check to ensure that we actually have data
        effect_control = block_store.create_block("BSEffectShaderPropertyFloatController", n_shader_prop)
        effect_control.flags = b_material.nif_material.texture_flags