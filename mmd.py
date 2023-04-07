# mmd_tools related functions

import bpy

# get mmd root object
def get_model_root(obj: bpy.types.Object) -> bpy.types.Object:
	if not obj:
		return None
	if obj.mmd_type == 'ROOT':
		return obj
	return get_model_root(obj.parent)


# Check if mmd_tools is installed
def is_mmd_tools_installed():
	return bpy.context.preferences.addons.get("mmd_tools")


# Bone Converter
# code from mmd_tools.core.vmd.importer.py

from mathutils import Matrix, Quaternion, Vector

class _InterpolationHelper:
    def __init__(self, mat):
        self.__indices = indices = [0, 1, 2]
        l = sorted((-abs(mat[i][j]), i, j) for i in range(3) for j in range(3))
        _, i, j = l[0]
        if i != j:
            indices[i], indices[j] = indices[j], indices[i]
        _, i, j = next(k for k in l if k[1] != i and k[2] != j)
        if indices[i] != j:
            idx = indices.index(j)
            indices[i], indices[idx] = indices[idx], indices[i]

    def convert(self, interpolation_xyz):
        return (interpolation_xyz[i] for i in self.__indices)


class BoneConverter:
    def __init__(self, pose_bone:bpy.types.PoseBone, scale:float, invert=False):
        mat = pose_bone.bone.matrix_local.to_3x3()
        mat[1], mat[2] = mat[2].copy(), mat[1].copy() # swap y and z
        self.__mat = mat.transposed()
        self.__scale = scale
        if invert:
            self.__mat.invert()
        self.convert_interpolation = _InterpolationHelper(self.__mat).convert

    def convert_location(self, location):
        return (self.__mat @ Vector(location)) * self.__scale

    def convert_rotation(self, rotation_xyzw):
        rot = Quaternion()
        rot.x, rot.y, rot.z, rot.w = rotation_xyzw
        return Quaternion( (self.__mat @ rot.axis) * -1, rot.angle).normalized()


class BoneConverterPoseMode:
    def __init__(self, pose_bone:bpy.types.PoseBone, scale:float, invert:bool=False):
        mat:Matrix = pose_bone.matrix.to_3x3()
        mat[1], mat[2] = mat[2].copy(), mat[1].copy() # swap y and z
        self.__mat = mat.transposed()
        self.__scale = scale
        self.__mat_rot = pose_bone.matrix_basis.to_3x3()
        self.__mat_loc = (self.__mat_rot @ self.__mat)
        self.__offset = pose_bone.location.copy()
        self.convert_location = self._convert_location
        self.convert_rotation = self._convert_rotation
        if invert:
            self.__mat.invert()
            self.__mat_rot.invert()
            self.__mat_loc.invert()
            self.convert_location = self._convert_location_inverted
            self.convert_rotation = self._convert_rotation_inverted
        self.convert_interpolation = _InterpolationHelper(self.__mat_loc).convert

    def _convert_location(self, location):
        return self.__offset + (self.__mat_loc @ Vector(location)) * self.__scale

    def _convert_rotation(self, rotation_xyzw):
        rot = Quaternion()
        rot.x, rot.y, rot.z, rot.w = rotation_xyzw
        rot = Quaternion((self.__mat @ rot.axis) * -1, rot.angle)
        return (self.__mat_rot @ rot.to_matrix()).to_quaternion()

    def _convert_location_inverted(self, location):
        return (self.__mat_loc @ Vector(location) - self.__offset) * self.__scale

    def _convert_rotation_inverted(self, rotation_xyzw):
        rot = Quaternion()
        rot.x, rot.y, rot.z, rot.w = rotation_xyzw
        rot = (self.__mat_rot @ rot.to_matrix()).to_quaternion()
        return Quaternion((self.__mat @ rot.axis) * -1, rot.angle).normalized()


# Quaternion to Euler degrees. BoneConverter.convert_rotation() returns a Quaternion
def quaternion_to_degrees( q:Quaternion ) -> Vector:
    euler = q.to_euler()
    return Vector( (euler.x, euler.y, euler.z) ) * (180 / 3.141592653589793)

# Euler degrees to Quaternion. BoneConverter.convert_rotation() needs xyzw
def degrees_to_quaternion( v:Vector ) -> Quaternion:
    euler = Vector( (v.x, v.y, v.z) ) * (3.141592653589793 / 180)
    return Quaternion( euler )
