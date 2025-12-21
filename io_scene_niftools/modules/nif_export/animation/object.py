"""Main module for exporting object animation blocks."""

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
import mathutils

import io_scene_niftools.modules.nif_export.animation.common as Common

from io_scene_niftools.modules.nif_export.object import DICT_NAMES
from io_scene_niftools.modules.nif_export.block_registry import block_store
from io_scene_niftools.utils import math, consts
from io_scene_niftools.utils.consts import QUAT, EULER, LOC, SCALE
from io_scene_niftools.utils.logging import NifError, NifLog
from nifgen.formats.nif import classes as NifClasses

class ObjectAnimation(Common.AnimationCommon):

    def __init__(self):
        super().__init__()

    def export_object_animations(self, b_controlled_blocks, n_ni_controller_sequence=None):
        NifLog.info(f"{b_controlled_blocks}")

        for b_controlled_block in b_controlled_blocks:
            b_strip, b_obj = b_controlled_block

            if type(b_obj.data) == bpy.types.Mesh:
                continue

            b_action = b_strip.action

            NifLog.warn("Trying to export NiTransformController!")

            if not b_action.slots[0].target_id_type == 'OBJECT':
                continue

            n_node = DICT_NAMES[b_obj.name]

            self.export_ni_object_controllers(b_obj, n_node, b_action, n_ni_controller_sequence)

    def export_ni_vis_controller(self, hide_curves, b_action, action_fcurves, n_node, n_ni_controller_sequence=None):
        """Export the visibility controller data."""

        start_frame, stop_frame = b_action.frame_range

        n_bool_data = block_store.create_block("NiBoolData")

        n_bool_data.data.interpolation = NifClasses.KeyType.CONST_KEY
        n_bool_data.data.num_keys = len(hide_curves)
        n_bool_data.data.reset_field("keys")

        for key, (frame, bool) in zip(n_bool_data.data.keys, hide_curves):
            key.time = frame / bpy.context.scene.render.fps
            key.value = bool

        n_vis_ctrl = block_store.create_block("NiVisController")
        n_vis_ipol = block_store.create_block("NiBoolInterpolator")

        n_vis_ipol.data = n_bool_data
        n_vis_ctrl.interpolator = n_vis_ipol

        self.set_flags_and_timing(n_vis_ctrl, action_fcurves, start_frame, stop_frame)

        n_node.add_controller(n_vis_ctrl)

        if n_ni_controller_sequence:
            n_ni_blend_bool_interpolator = block_store.create_block("NiBlendBoolInterpolator")

            n_ni_blend_bool_interpolator.array_size = 2
            n_ni_blend_bool_interpolator.reset_field("interp_array_items")

            n_ni_blend_bool_interpolator.value = consts.FLOAT_MIN
            n_ni_blend_bool_interpolator.flags.manager_controlled = True

            n_controlled_block = n_ni_controller_sequence.add_controlled_block()

            n_controlled_block.controller = n_vis_ctrl
            n_controlled_block.interpolator = n_vis_ipol

            n_vis_ctrl.interpolator = n_ni_blend_bool_interpolator
            
            n_controlled_block.node_name = n_node.name
            n_controlled_block.controller_type = "NiVisController"

    def export_kf_root(self, b_armature=None):
        """Creates and returns a KF root block and exports controllers for objects and bones"""
        scene = bpy.context.scene
        nif_scene = scene.niftools_scene
        game = nif_scene.game

        if game in ('MORROWIND', 'FREEDOM_FORCE'):
            kf_root = block_store.create_block("NiSequenceStreamHelper")
        elif nif_scene.is_bs() or game in (
                'CIVILIZATION_IV', 'ZOO_TYCOON_2', 'FREEDOM_FORCE_VS_THE_3RD_REICH',
                'SHIN_MEGAMI_TENSEI_IMAGINE', 'SID_MEIER_S_PIRATES'):
            kf_root = block_store.create_block("NiControllerSequence")
        else:
            raise NifError(f"Keyframe export for '{game}' is not supported.")

        anim_textextra = Common.create_text_keys(kf_root)
        targetname = "Scene Root"
        b_action = None

        # per-node animation
        if b_armature:
            b_action = self.get_active_action(b_armature)

            if not b_action:
                animData = b_armature.animation_data
                nlaTracks = animData.nla_tracks

                for track in nlaTracks:
                    if track.select:
                        b_action = track.strips[0].action

            for b_bone in b_armature.data.bones:
                self.export_ni_transform_controller(kf_root, b_armature, b_action, b_bone)
                self.export_ni_vis_controller(kf_root, b_action)
            if nif_scene.is_skyrim():
                targetname = "NPC Root [Root]"
            else:
                # quick hack to set correct target name
                if "Bip01" in b_armature.data.bones:
                    targetname = "Bip01"
                elif "Bip02" in b_armature.data.bones:
                    targetname = "Bip02"

        # per-object animation
        else:
            for b_obj in bpy.data.objects:
                b_action = self.get_active_action(b_obj)
                self.export_ni_transform_controller(kf_root, b_obj, b_action)

        Common.export_text_keys(b_action, anim_textextra)

        kf_root.name = b_action.name
        kf_root.unknown_int_1 = 1
        kf_root.weight = 1.0
        kf_root.cycle_type = NifClasses.CycleType.CYCLE_CLAMP
        
        kf_root.frequency = 1.0
        if nif_scene.is_bs() or game in ('SID_MEIER_S_PIRATES',):
            kf_root.accum_root_name = targetname

        if anim_textextra.num_text_keys > 0:
            kf_root.start_time = anim_textextra.text_keys[0].time
            kf_root.stop_time = anim_textextra.text_keys[anim_textextra.num_text_keys - 1].time
        else:
            kf_root.start_time = scene.frame_start / self.fps
            kf_root.stop_time = scene.frame_end / self.fps

        kf_root.target_name = targetname
        return kf_root

    def export_ni_object_controllers(self, b_obj, n_node, b_action, n_ni_controller_sequence=None):

        bind_matrix = b_obj.matrix_parent_inverse
        bind_scale, bind_rot, bind_trans = math.decompose_srt(bind_matrix)

        action_fcurves = self.get_fcurves_from_action(b_action)

        quaternion_data = [fcu for fcu in action_fcurves if fcu.data_path.endswith("quaternion")]
        translation_data = [fcu for fcu in action_fcurves if fcu.data_path.endswith("location")]
        euler_data = [fcu for fcu in action_fcurves if fcu.data_path.endswith("euler")]
        scale_data = [fcu for fcu in action_fcurves if fcu.data_path.endswith("scale")]

        hide_data = [fcu for fcu in action_fcurves if "hide" in fcu.data_path]

        # ensure that those groups that are present have all their fcurves
        for fcus, num_fcus in ((quaternion_data, 4), (euler_data, 3), (translation_data, 3), (scale_data, 3)):
            if fcus and len(fcus) != num_fcus:
                raise NifError(
                    f"Incomplete key set {n_node.name} for action {b_action.name}."
                    f"Ensure that if a bone is keyframed for a property, all channels are keyframed.")
            
        quat_curve = []
        euler_curve = []
        trans_curve = []
        scale_curve = []

        hide_curve = []

        for frame, quat in self.iter_frame_key(quaternion_data, mathutils.Quaternion):
            quat = math.export_keymat(bind_rot, quat.to_matrix().to_4x4()).to_quaternion()
            quat_curve.append((frame, quat))

        for frame, euler in self.iter_frame_key(euler_data, mathutils.Euler):
            keymat = math.export_keymat(bind_rot, euler.to_matrix().to_4x4())
            euler = keymat.to_euler("XYZ", euler)
            euler_curve.append((frame, euler))

        for frame, trans in self.iter_frame_key(translation_data, mathutils.Vector):
            keymat = math.export_keymat(bind_rot, mathutils.Matrix.Translation(trans))
            trans = keymat.to_translation() + bind_trans
            trans_curve.append((frame, trans))

        for frame, scale in self.iter_frame_key(scale_data, mathutils.Vector):
            # just use the first scale curve and assume even scale over all curves
            scale_curve.append((frame, scale[0]))

        for fcurve in hide_data:
            for keyframe in fcurve.keyframe_points:
                hide_curve.append((keyframe.co[0], keyframe.co[1]))

        if max(len(c) for c in (quat_curve, euler_curve, trans_curve, scale_curve)) > 0:
            # number of frames is > 0, so export transform data
            self.export_ni_transform_controller(quat_curve, euler_curve, trans_curve, scale_curve, b_action, action_fcurves, n_node, n_ni_controller_sequence)

        if hide_curve:
            self.export_ni_vis_controller(hide_curve, b_action, action_fcurves, n_node, n_ni_controller_sequence)


    def export_ni_transform_controller(self, quat_curves, euler_curves, trans_curves, scale_curves, b_action, action_fcurves, n_node, n_ni_controller_sequence=None):
        n_kfc = block_store.create_block("NiTransformController")
        n_kfi = block_store.create_block("NiTransformInterpolator")

        start_frame, stop_frame = b_action.frame_range

        self.set_flags_and_timing(n_kfc, action_fcurves, start_frame, stop_frame)

        n_kfd = block_store.create_block("NiTransformData")

        if euler_curves:
            n_kfd.rotation_type = NifClasses.KeyType.XYZ_ROTATION_KEY
            n_kfd.num_rotation_keys = 1  # *NOT* len(frames) this crashes the engine!
            n_kfd.reset_field("xyz_rotations")
            for i, coord in enumerate(n_kfd.xyz_rotations):
                coord.num_keys = len(euler_curves)
                coord.interpolation = NifClasses.KeyType.LINEAR_KEY
                coord.reset_field("keys")
                for key, (frame, euler) in zip(coord.keys, euler_curves):
                    key.time = frame / bpy.context.scene.render.fps
                    key.value = euler[i]

        elif quat_curves:
            n_kfd.rotation_type = NifClasses.KeyType.QUADRATIC_KEY
            n_kfd.num_rotation_keys = len(quat_curves)
            n_kfd.reset_field("quaternion_keys")
            for key, (frame, quat) in zip(n_kfd.quaternion_keys, quat_curves):
                key.time = frame / bpy.context.scene.render.fps
                key.value.w = quat.w
                key.value.x = quat.x
                key.value.y = quat.y
                key.value.z = quat.z

        n_kfd.translations.interpolation = NifClasses.KeyType.LINEAR_KEY
        n_kfd.translations.num_keys = len(trans_curves)
        n_kfd.translations.reset_field("keys")

        for key, (frame, trans) in zip(n_kfd.translations.keys, trans_curves):
            key.time = frame / bpy.context.scene.render.fps
            key.value.x, key.value.y, key.value.z = trans

        n_kfd.scales.interpolation = NifClasses.KeyType.LINEAR_KEY
        n_kfd.scales.num_keys = len(scale_curves)
        n_kfd.scales.reset_field("keys")

        for key, (frame, scale) in zip(n_kfd.scales.keys, scale_curves):
            key.time = frame / bpy.context.scene.render.fps
            key.value = scale

        self.set_flags_and_timing(n_kfc, action_fcurves)

        n_kfi.data = n_kfd
        n_kfc.interpolator = n_kfi

        n_node.add_controller(n_kfc)

        if n_ni_controller_sequence:
            n_controlled_block = n_ni_controller_sequence.add_controlled_block()
            n_controlled_block.controller = n_kfc
            n_controlled_block.interpolator = n_kfi
            
            n_controlled_block.node_name = n_node.name
            n_controlled_block.controller_type = "NiTransformController"

    def add_dummy_controllers(self, b_armature):
        NifLog.info("Adding controllers and interpolators for skeleton")
        # note: block_store.block_to_obj changes during iteration, so need list copy
        for n_block in list(block_store.block_to_obj.keys()):
            if isinstance(n_block, NifClasses.NiNode) and n_block.name == "Bip01":
                for n_bone in n_block.tree(block_type=NifClasses.NiNode):
                    n_kfc, n_kfi = b_armature.transform_anim.create_controller(n_bone, n_bone.name)
                    # todo [anim] use self.nif_export.animationhelper.set_flags_and_timing
                    n_kfc.flags = 12
                    n_kfc.frequency = 1.0
                    n_kfc.phase = 0.0
                    n_kfc.start_time = consts.FLOAT_MAX
                    n_kfc.stop_time = consts.FLOAT_MIN
