import bpy

from io_scene_niftools.utils import consts

from io_scene_niftools.modules.nif_export.animation.common import AnimationCommon
from io_scene_niftools.modules.nif_export.block_registry import block_store

from nifgen.formats.nif import classes as NifClasses
from io_scene_niftools.utils.logging import NifError, NifLog

def export_fo3_effect_shader_animation(n_ni_geometry, n_shader_prop, b_material, b_action, n_ni_controller_sequence=None):
    action_fcurves = AnimationCommon.get_fcurves_from_action(None, b_action)

    b_refraction_bsdf = next((node for node in b_material.node_tree.nodes if isinstance(node, bpy.types.ShaderNodeBsdfRefraction)), None)

    refraction_strength_data = []
    fire_period_data = []

    for fcurve in action_fcurves:
        data_path_lower = fcurve.data_path.lower()

        if "refraction_strength" in data_path_lower or (b_refraction_bsdf is not None and "inputs[2]" in data_path_lower):
            refraction_strength_data.append(fcurve)
        elif "refraction_fire_period" in data_path_lower:
            fire_period_data.append(fcurve)

    refraction_strength_curves = []
    fire_period_curves = []

    for fcurve in refraction_strength_data:
        for keyframe in fcurve.keyframe_points:
            refraction_strength_curves.append((keyframe.co[0], keyframe.co[1]))

    for fcurve in fire_period_data:
        for keyframe in fcurve.keyframe_points:
            fire_period_curves.append((keyframe.co[0], keyframe.co[1]))

    if refraction_strength_curves:
        export_bs_refraction_strength_controller(b_action, refraction_strength_curves, action_fcurves, b_material, n_ni_geometry, n_shader_prop, n_ni_controller_sequence)

    if fire_period_curves:
        export_bs_refraction_fire_period_controller(b_action, refraction_strength_curves, action_fcurves, b_material, n_ni_geometry, n_shader_prop, n_ni_controller_sequence)

def export_bs_refraction_strength_controller(b_action, refraction_strength_curves, action_fcurves, b_material, n_ni_geometry, n_shader_prop, n_ni_controller_sequence=None):
        scene_fps = bpy.context.scene.render.fps

        n_key_data = block_store.create_block("NiFloatData")
        n_key_data.data.num_keys = len(refraction_strength_curves)
        n_key_data.data.interpolation = NifClasses.KeyType.LINEAR_KEY
        n_key_data.data.reset_field("keys")

        for key, (frame, strength) in zip(n_key_data.data.keys, refraction_strength_curves):
            key.time = frame / scene_fps
            key.value = strength

        refraction_strength_controller = block_store.create_block("BSRefractionStrengthController")
        float_interpolator = block_store.create_block("NiFloatInterpolator")

        frame_start, frame_end = b_action.frame_range

        refraction_strength_controller.start_time = frame_start / scene_fps
        refraction_strength_controller.stop_time = frame_end / scene_fps

        float_interpolator.data = n_key_data
        refraction_strength_controller.interpolator = float_interpolator

        n_shader_prop.add_controller(refraction_strength_controller)

        if n_ni_controller_sequence:
            n_ni_blend_float_interpolator = block_store.create_block("NiBlendFloatInterpolator")

            n_ni_blend_float_interpolator.array_size = 2
            n_ni_blend_float_interpolator.reset_field("interp_array_items")

            n_ni_blend_float_interpolator.value = consts.FLOAT_MIN
            n_ni_blend_float_interpolator.flags.manager_controlled = True

            n_controlled_block = n_ni_controller_sequence.add_controlled_block()
            n_controlled_block.controller = refraction_strength_controller
            n_controlled_block.interpolator = float_interpolator

            refraction_strength_controller.interpolator = n_ni_blend_float_interpolator
            
            n_controlled_block.node_name = n_ni_geometry.name
            n_controlled_block.property_type = b_material.nif_shader.bs_shadertype
            n_controlled_block.controller_type = "BSRefractionStrengthController"

def export_bs_refraction_fire_period_controller(b_action, refraction_fire_period_curves, action_fcurves, b_material, n_ni_geometry, n_shader_prop, n_ni_controller_sequence=None):
    scene_fps = bpy.context.scene.render.fps

    n_key_data = block_store.create_block("NiFloatData")
    n_key_data.data.num_keys = len(refraction_fire_period_curves)
    n_key_data.data.interpolation = NifClasses.KeyType.LINEAR_KEY
    n_key_data.data.reset_field("keys")

    for key, (frame, strength) in zip(n_key_data.data.keys, refraction_fire_period_curves):
        key.time = frame / scene_fps
        key.value = strength

    refraction_fire_period_controller = block_store.create_block("BSRefractionFirePeriodController")
    float_interpolator = block_store.create_block("NiFloatInterpolator")

    float_interpolator.data = n_key_data
    refraction_fire_period_controller.interpolator = float_interpolator

    frame_start, frame_end = b_action.frame_range

    refraction_fire_period_controller.start_time = frame_start / scene_fps
    refraction_fire_period_controller.stop_time = frame_end / scene_fps

    n_shader_prop.add_controller(refraction_fire_period_controller)

    if n_ni_controller_sequence:
        n_ni_blend_float_interpolator = block_store.create_block("NiBlendFloatInterpolator")

        n_ni_blend_float_interpolator.array_size = 2
        n_ni_blend_float_interpolator.reset_field("interp_array_items")

        n_ni_blend_float_interpolator.value = consts.FLOAT_MIN
        n_ni_blend_float_interpolator.flags.manager_controlled = True

        n_controlled_block = n_ni_controller_sequence.add_controlled_block()
        n_controlled_block.controller = refraction_fire_period_controller
        n_controlled_block.interpolator = float_interpolator

        refraction_fire_period_controller.interpolator = n_ni_blend_float_interpolator
        
        n_controlled_block.node_name = n_ni_geometry.name
        n_controlled_block.property_type = b_material.nif_shader.bs_shadertype
        n_controlled_block.controller_type = "BSRefractionFirePeriodController"