#############################################
# Helper functions
import bpy
from mathutils import Matrix, Vector, Quaternion
import math
from typing import Tuple

# helper: check pose bone is visible
def is_pose_bone_visible( pbone: bpy.types.PoseBone ) -> bool:
    # check if bone is hidden
    if pbone.bone.hide or pbone.bone.hide_select:
        return False

    # check if bone is in visible layer
    arm = pbone.id_data
    if bpy.app.version < (4,0,0): # 2.x~3.x
        if not any(pbone.bone.layers[i] and arm.data.layers[i] for i in range(len(pbone.bone.layers))):
            return False
    else: # 4.x~
        attr = 'is_visible_effectively' if bpy.app.version > (4,2,0) else 'is_visible'
        if not any(getattr(bcoll, attr) for bcoll in pbone.bone.collections):
            return False

    return True

# Get pose bone rotation in quaternion
def get_pose_bone_rotation_quaternion( pbone: bpy.types.PoseBone ) -> Quaternion:
    rotation_mode = pbone.rotation_mode

    if rotation_mode == 'QUATERNION':
        return pbone.rotation_quaternion
    elif rotation_mode == 'AXIS_ANGLE':
        return pbone.rotation_axis_angle.to_quaternion()
    elif rotation_mode in ['XYZ', 'XZY', 'YXZ', 'YZX', 'ZXY', 'ZYX']:
        return pbone.rotation_euler.to_quaternion()
    else:
        print("Unknown rotation mode: ", rotation_mode)
        return Quaternion()


# Transform check functions
def is_matrix_almost_equal(m1, m2, threshold=1e-6):
    """Check if two matrices are almost equal"""
    return all(abs(x1 - x2) < threshold for x1, x2 in zip(m1, m2))

def is_vector_almost_equal(v1, v2, threshold=1e-6):
    """Check if two vectors are almost equal"""
    return all(abs(x1 - x2) < threshold for x1, x2 in zip(v1, v2))

def has_rotation(q, threshold=1e-6):
    """Check if the quaternion is less than minimal"""
    q_normalized = q.normalized()
    dot_product = q_normalized.dot(Quaternion())
    angle_diff = 2 * math.acos(min(1.0, abs(dot_product))) 
    return angle_diff > threshold

def has_translation(v, threshold=1e-6):
    """Check if the location vector has translation"""
    return any(abs(x) > threshold for x in v)

def has_scale(v, threshold=1e-6):
    """Check if the scale vector is less than minimal"""
    return any(abs(x-1.0) > threshold for x in v)

def has_transform( loc, rot, scale, threshold=1e-6 ):
    """Check if the transform is less than minimal"""
    return has_translation(loc, threshold) or has_rotation(rot, threshold) or has_scale(scale, threshold)


#############################################
# Conversion functions
#############################################

def to_armature_space(loc: Vector, rot: Quaternion, sca: Vector, pbone: bpy.types.PoseBone, invert:bool = False) -> Tuple[Vector, Quaternion]:
    if not pbone:
        return loc, rot, sca

    mtx = pbone.bone.matrix_local.to_3x3()

    if invert:
        mtx.invert()

    new_loc = mtx @ loc
    new_rot = Quaternion( (mtx @ rot.axis) * -1, rot.angle).normalized()
    new_sca = mtx @ (sca - Vector((1,1,1))) + Vector((1,1,1))

    return new_loc, new_rot, new_sca


