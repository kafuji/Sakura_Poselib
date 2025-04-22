#############################################
# Helper functions
import bpy
from mathutils import Matrix, Vector, Quaternion, Euler
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

# Convert location, rotation, and scale from bone local space to armature space.
def to_armature_space(loc: Vector, rot: Quaternion, sca: Vector, pbone: bpy.types.PoseBone, invert:bool = False) -> Tuple[Vector, Quaternion, Vector]:
    if not pbone:
        return loc, rot, sca

    mtx = pbone.bone.matrix_local.to_3x3()

    if invert:
        mtx.invert()

    new_loc = mtx @ loc
    new_rot = Quaternion( (mtx @ rot.axis) *-1, rot.angle).normalized()
    new_sca = mtx @ (sca - Vector((1,1,1))) + Vector((1,1,1))

    return new_loc, new_rot, new_sca




def quaternion_to_degrees(q: Quaternion, order: str = "XYZ") -> Vector:
    """
    Convert a Quaternion to Euler angles in *degrees* (0~360 range).

    Parameters
    ----------
    q : Quaternion
        The source rotation.
    order : str, optional
        Axis order for the Euler conversion. Defaults to "XYZ",
        which corresponds to MMD's (X→Y→Z) display order.

    Returns
    -------
    Vector
        (x_deg, y_deg, z_deg) Euler angles in degrees.
    """
    euler_rad = q.to_euler(order)  # Blender returns radians
    return Vector((
        math.degrees(euler_rad.x) % 360.0,
        math.degrees(euler_rad.y) % 360.0,
        math.degrees(euler_rad.z) % 360.0,
    ))


def degrees_to_quaternion(rot_deg: Vector, order: str = "XYZ") -> Quaternion:
    """
    Convert Euler angles in degrees (0~360 notation) to a Quaternion.

    Parameters
    ----------
    rot_deg : Vector
        (x_deg, y_deg, z_deg) Euler angles in degrees.
    order : str, optional
        Axis order for the Euler conversion. Defaults to "XYZ".

    Returns
    -------
    Quaternion
        The resulting rotation.
    """
    euler_rad = Euler((
        math.radians(rot_deg.x),
        math.radians(rot_deg.y),
        math.radians(rot_deg.z),
    ), order)
    return euler_rad.to_quaternion().normalized()


def quat_to_euler_mmd(
    q: Tuple[float, float, float, float],
    degrees: bool = False
) -> Tuple[float, float, float]:
    """
    Convert quaternion (w, x, y, z) to Euler angles (x, y, z) in MMD space.

    Parameters
    ----------
    q : Tuple[float, float, float, float]
        Quaternion in the order (w, x, y, z).
    degrees : bool, optional
        If True, return angles in degrees instead of radians.

    Returns
    -------
    Tuple[float, float, float]
        Euler angles (x, y, z) following intrinsic X→Y→Z rotation order.
        • x: rotation around the local X‑axis (pitch)  
        • y: rotation around the local Y‑axis (yaw)  
        • z: rotation around the local Z‑axis (roll)
    """
    w, x, y, z = q

    # --- Z (roll) ---
    t0 = 2.0 * (w * z + x * y)
    t1 = 1.0 - 2.0 * (y * y + z * z)
    roll_z = math.atan2(t0, t1)

    # --- X (pitch) ---
    t2 = 2.0 * (w * x - y * z)
    # Clamp for numerical accuracy
    t2 = max(-1.0, min(1.0, t2))
    pitch_x = math.asin(t2)

    # --- Y (yaw) ---
    t3 = 2.0 * (w * y + z * x)
    t4 = 1.0 - 2.0 * (x * x + y * y)
    yaw_y = math.atan2(t3, t4)

    if degrees:
        pitch_x = math.degrees(pitch_x)
        yaw_y   = math.degrees(yaw_y)
        roll_z  = math.degrees(roll_z)

    return pitch_x, yaw_y, roll_z


def _normalize(q: Tuple[float, float, float, float]
) -> Tuple[float, float, float, float]:
    """Return a unit quaternion; avoid division by zero."""
    w, x, y, z = q
    n = math.sqrt(w*w + x*x + y*y + z*z) or 1.0
    return (w/n, x/n, y/n, z/n)

def euler_to_quat_mmd(
    euler: Tuple[float, float, float],
    *,
    degrees: bool = False
) -> Tuple[float, float, float, float]:
    """
    MMD 空間／内的 X→Y→Z 回転のオイラー角 (x, y, z)
    → クォータニオン (w, x, y, z) へ変換します。

    Parameters
    ----------
    euler : (x, y, z)
        回転角。pitch・yaw・roll に対応。
    degrees : bool
        True なら度数法入力、False ならラジアン入力。

    Returns
    -------
    (w, x, y, z) : 正規化済みクォータニオン
    """
    pitch_x, yaw_y, roll_z = euler
    if degrees:
        pitch_x, yaw_y, roll_z = map(math.radians, (pitch_x, yaw_y, roll_z))

    # 半角
    hx, hy, hz = (a * 0.5 for a in (pitch_x, yaw_y, roll_z))
    cx, cy, cz = math.cos(hx), math.cos(hy), math.cos(hz)
    sx, sy, sz = math.sin(hx), math.sin(hy), math.sin(hz)

    # 内的 X→Y→Z の直書き式
    w =  cx * cy * cz - sx * sy * sz
    qx =  sx * cy * cz + cx * sy * sz
    qy =  cx * sy * cz - sx * cy * sz
    qz =  cx * cy * sz + sx * sy * cz

    return Quaternion( _normalize((w, qx, qy, qz)) )

# Generic axis conversion function
def swap_axis( v:Vector, axis:Tuple[int, int, int] ) -> Vector:
    """
    Swap the axes of a vector based on the provided axis mapping.
    
    Args:
        v: Vector to swap axes.
        axis: Tuple of three integers representing the new axis order.
            e.g., (0, 2, 1) swaps the second and third axes.
        
    Returns:
        Vector with swapped axes.
    """

    if len(axis) != 3:
        raise ValueError("Axis must be a tuple of three integers.")
    if any(a < 0 or a > 2 for a in axis):
        raise ValueError("Axis values must be 0, 1, or 2.")
    if len(set(axis)) != 3:
        raise ValueError("Axis values must be unique.")
    
    return Vector( (v[axis[0]], v[axis[1]], v[axis[2]]) )
