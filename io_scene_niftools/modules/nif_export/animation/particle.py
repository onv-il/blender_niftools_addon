"""Main module for exporting particle animation blocks."""

import mathutils

import io_scene_niftools.modules.nif_export.particle.modifier as ParticleModifier

from io_scene_niftools.modules.nif_export.animation.common import AnimationCommon
from io_scene_niftools.modules.nif_export.block_registry import block_store
from io_scene_niftools.modules.nif_export.object import DICT_NAMES

from io_scene_niftools.utils.logging import NifError, NifLog

from nifgen.formats.nif import classes as NifClasses

class ParticleAnimation(AnimationCommon):

    def __init__(self):
        super().__init__()

        self.modifier_helper = ParticleModifier.Modifier()

    def export_particle_animations(self, b_controlled_blocks, n_ni_controller_sequence=None):
        
        for b_controlled_block in b_controlled_blocks:
            b_strip, b_obj = b_controlled_block

            if not b_obj.particle_systems:
                continue

            b_action = b_strip.action
            
            n_ni_particle_system = DICT_NAMES[b_obj.name]
            
            self.export_particle_system_controller(b_obj, b_action, n_ni_particle_system, n_ni_controller_sequence)

    def export_particle_system_controller(self, b_obj, b_action, n_ni_particle_system, n_ni_controller_sequence=None):
        action_fcurves = self.get_fcurves_from_action(b_action)

        color_data = []
        alpha_data = []

        for fcurve in action_fcurves:
            data_path_lower = fcurve.data_path.lower()

            if "color" in data_path_lower or "inputs[0]" in data_path_lower:
                color_data.append(fcurve)
            elif "alpha" in data_path_lower or "inputs[4]" in data_path_lower:
                alpha_data.append(fcurve)

        if len(color_data) + len(alpha_data) != 4:
            raise NifError(
                f"Incomplete particle color key set for action {b_action.name}."
                f"Ensure that all RGBA channels are keyframed, even if their values do not change.")
            
        color_fcurves = []
        alpha_fcurves = []

        for frame, color in self.iter_frame_key(color_data, mathutils.Color):
            color_fcurves.append((frame, color.from_scene_linear_to_srgb()))

        for fcurve in alpha_data:
            for keyframe in fcurve.keyframe_points:
                alpha_fcurves.append((keyframe.co[0], keyframe.co[1]))

        if max(len(c) for c in (color_fcurves, alpha_fcurves)) > 0:
            self.modifier_helper.export_ni_p_sys_color_modifier(b_obj, (color_fcurves, alpha_fcurves), n_ni_particle_system)