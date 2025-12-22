"""Nif User Interface, custom nif properties store for animation settings"""

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

from bpy.props import (EnumProperty, FloatProperty, IntProperty, BoolProperty)
from bpy.types import PropertyGroup

from io_scene_niftools.utils.decorators import register_classes, unregister_classes


class ParticleSystemProperty(PropertyGroup):
    """Group of Havok related properties, which gets attached to objects through a property pointer."""

    particle_system_type: EnumProperty(
        name='Particle System Type',
        description='Particle system to export.',
        items=[("NiParticleSystem", "NiParticleSystem", "2D sprite-based particle system.", 0), ("BSStripParticleSystem", "BSStripParticleSystem", "Primitive Bethesda mesh particle system.", 1)],
        default = 'NiParticleSystem'
    )

    particle_emitter_type: EnumProperty(
        name='Particle Emitter Type',
        description='Particle emitter to export.',
        items=[("NiPSysSphereEmitter", "NiPSysSphereEmitter", "Randomly spawns particles within the radius of a sphere centered on a NiNode.", 0), 
               ("NiPSysBoxEmitter", "NiPSysBoxEmitter", "Randomly spawns particles within a bounding box centered on a NiNode.", 1), 
               ("NiPSysCylinderEmitter", "NiPSysCylinderEmitter", "Randomly spawns particles within the radius of a cylinder centered on a NiNode.", 2),
               ("NiPSysMeshEmitter", "NiPSysMeshEmitter", "Randomly spawns particles from a specifiable parts of the parent mesh.", 3), 
               ("BSPSysArrayEmitter", "BSPSysArrayEmitter", "Evenly spawns particles across a NiNode and its children Nodes recursively.\nRandomizes the position, rotation, and scale of each NiNode when each particle is spawned.", 4)],
        default = 'NiPSysSphereEmitter'
    )

    bs_strip_max_point_count: IntProperty(
        name='Max Point Count',
        description='Amount of points a strip particle will be defined with.\nBSStripPSysData::Max Point Count',
        default=4,
    )

    num_spawn_generations: IntProperty(
        name='Particle Generation Count',
        description='How many times each particle is spawned. \nCan leave at 0.\nNiPSysSpawnModifier::Num Spawn Generations',
        default=0,
    )

    percentage_spawned: FloatProperty(
        name='Spawn Chance',
        description='A 0-1 float percentage that determines how many particles are actually spawned each generation.\nNiPSysSpawnModifier::Percentage Spawned',
        default=1,
        min=0,
        max=1,
    )

    min_num_to_spawn: IntProperty(
        name='Minimum Spawn Count',
        description='The minimum number of particles that spawn each generation if they pass the percentage check.\nNiPSysSpawnModifier::Min Num To Spawn',
        default=1,
        min=0,
        max=255,
    )

    max_num_to_spawn: IntProperty(
        name='Maximum Spawn Count',
        description='The maximum number of particles that spawn each generation if they pass the percentage check.\nNiPSysSpawnModifier::Max Num To Spawn',
        default=1,
        min=0,
        max=255,
    ) 

    num_subtexture_offsets: IntProperty(
        name='Subtexture Offset Count',
        description='Number of subtextures in the texture file.\nUsed for exporting flipbooks/spritesheets.\nMust be 0 or a multiple of 2.\nNiParticlesData::Num Subtexture Offsets',
        default=0,
        min=0,
        step=2,
    )

    spawn_on_death: BoolProperty(
        name='Spawn On Death',
        description='Generate new particles when the old ones die.\nNiPSysAgeDeathModifier::Spawn On Death',
        default=False,
    )

    random_rot_speed_sign: BoolProperty(
        name='Randomly Negate Angular Velocity',
        description='Randomly negate the initial speed of particle rotations upon spawning. \nNiPSysRotationModifier::Random Rot Speed Sign',
        default=False,
    )

CLASSES = [
    ParticleSystemProperty
]


def register():
    register_classes(CLASSES, __name__)

    bpy.types.ParticleSettings.nif_particle_system = bpy.props.PointerProperty(type=ParticleSystemProperty)


def unregister():
    del bpy.types.ParticleSettings.nif_particle_system

    unregister_classes(CLASSES, __name__)
