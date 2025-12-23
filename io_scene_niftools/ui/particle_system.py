"""Nif User Interface, connect custom properties from properties.py into Blenders UI"""

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


from bpy.types import Panel

from io_scene_niftools.utils.decorators import register_classes, unregister_classes


class ParticleSystemPanel(Panel):
    bl_idname = "NIFTOOLS_PT_ParticleSystemPanel"
    bl_label = "NifTools Particle System"

    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "particle"

    external_object_emitters = [
        "NiPSysMeshEmitter",
        "BSPSysArrayEmitter"
    ]

    @classmethod
    def poll(cls, context):
        if context.particle_settings:
            return True
        return False

    def draw(self, context):
        particle_setting = context.particle_settings.nif_particle_system
        
        layout = self.layout

        box = layout.box()

        box.prop(particle_setting, "particle_system_type")
        box.prop(particle_setting, "particle_emitter_type")

        if particle_setting.particle_emitter_type in self.external_object_emitters:
            box.prop(particle_setting, "particle_emitter_object")

        if particle_setting.particle_system_type == "BSStripParticleSystem":
            box.prop(particle_setting, "bs_strip_max_point_count")


        box.prop(particle_setting, "num_spawn_generations")
        box.prop(particle_setting, "percentage_spawned")
        box.prop(particle_setting, "spawn_on_death")
        
        box.prop(particle_setting, "min_num_to_spawn")
        box.prop(particle_setting, "max_num_to_spawn")

        box.prop(particle_setting, "num_subtexture_offsets")

        box.prop(particle_setting, "random_rot_speed_sign")


classes = [
    ParticleSystemPanel
]

def register():
    register_classes(classes, __name__)

def unregister():
    unregister_classes(classes, __name__)
