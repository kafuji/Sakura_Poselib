# mmd_tools related functions

import bpy
from typing import Tuple

# Check if mmd_tools is installed
def is_mmd_tools_installed():
    addons = bpy.context.preferences.addons
    return 'mmd_tools' in addons or 'bl_ext.blender_org.mmd_tools' in addons # check addon and extension (Blender 4.2 or later)


# get mmd root object
def get_model_root(obj: bpy.types.Object) -> bpy.types.Object:
    if not is_mmd_tools_installed():
        return None

    if not obj:
        return None
    if obj.mmd_type == 'ROOT':
        return obj

    return get_model_root(obj.parent)


# Get mmd_bone.name and name_e if present, otherwise return bone.name
def get_mmd_bone_name_j_e(bone: bpy.types.Bone) -> Tuple[str, str]:
    if not bone:
        raise ValueError("bone is None")
    
    if not is_mmd_tools_installed():
        return bone.name, bone.name
    
    name_j, name_e = bone.mmd_bone.name_j or bone.name, bone.mmd_bone.name_e or bone.name

    return name_j, name_e

# Get pose bone by mmd_bone.name_e or name_j
def get_pose_bone_by_mmd_name(armature: bpy.types.Object, name: str) -> bpy.types.PoseBone:
    if not armature or armature.type != 'ARMATURE':
        raise ValueError("armature is None or not an armature")
    
    if not is_mmd_tools_installed():
        return armature.pose.bones.get(name)

    pbone = armature.pose.bones.get(name)
    if pbone:
        return pbone

    for pbone in armature.pose.bones:
        if pbone.mmd_bone.name_j == name or pbone.mmd_bone.name_e == name:
            return pbone

    return None


# Bone Transform converter classes from mmd_tools/vmd/importer.py
from mathutils import Vector, Quaternion

class BoneConverter:
    def __init__(self, pose_bone, scale, invert=False):
        mat = pose_bone.bone.matrix_local.to_3x3()
        mat[1], mat[2] = mat[2].copy(), mat[1].copy()
        self.__mat = mat.transposed()
        self.__scale = scale
        if invert:
            self.__mat.invert()

    def convert_location(self, location:Vector):
        return (self.__mat @ location) * self.__scale

    def convert_rotation(self, rot:Quaternion):
        return Quaternion((self.__mat @ rot.axis) * -1, rot.angle).normalized()


# VpdFile class, modified from mmd_tools/core/vpd/exporter.py
# Usage (Export):
# vpd = VpdFile()
# 

class InvalidFileError(Exception):
    pass


class VpdBone:
    def __init__(self, bone_name, location, rotation):
        self.bone_name = bone_name
        self.location = location
        self.rotation = rotation if any(rotation) else [0, 0, 0, 1]

    def __repr__(self):
        return "<VpdBone %s, loc %s, rot %s>" % (
            self.bone_name,
            str(self.location),
            str(self.rotation),
        )

class VpdMorph:
    def __init__(self, morph_name, weight):
        self.morph_name = morph_name
        self.weight = weight

    def __repr__(self):
        return "<VpdMorph %s, weight %f>" % (
            self.morph_name,
            self.weight,
        )


class VpdFile:
    def __init__(self):
        self.filepath = ""
        self.osm_name = None
        self.bones = []
        self.morphs = []

    def __repr__(self):
        return "<File %s, osm %s, bones %d, morphs %d>" % (
            self.filepath,
            self.osm_name,
            len(self.bones),
            len(self.morphs),
        )

    def load(self, **args):
        path = args["filepath"]

        encoding = "shift_jis"
        with open(path, "rt", encoding=encoding, errors="replace") as fin:
            self.filepath = path
            if not fin.readline().startswith("Vocaloid Pose Data file"):
                raise InvalidFileError

            fin.readline()
            self.osm_name = fin.readline().split(";")[0].strip()
            bone_counts = int(fin.readline().split(";")[0].strip())
            fin.readline()

            for line in fin:
                if line.startswith("Bone"):
                    bone_name = line.split("{")[-1].strip()

                    location = [float(x) for x in fin.readline().split(";")[0].strip().split(",")]
                    if len(location) != 3:
                        raise InvalidFileError

                    rotation = [float(x) for x in fin.readline().split(";")[0].strip().split(",")]
                    if len(rotation) != 4:
                        raise InvalidFileError

                    if not fin.readline().startswith("}"):
                        raise InvalidFileError

                    self.bones.append(VpdBone(bone_name, location, rotation))

                elif line.startswith("Morph"):
                    morph_name = line.split("{")[-1].strip()
                    weight = float(fin.readline().split(";")[0].strip())

                    if not fin.readline().startswith("}"):
                        raise InvalidFileError

                    self.morphs.append(VpdMorph(morph_name, weight))

            if len(self.bones) != bone_counts:
                raise InvalidFileError

    def save(self, **args):
        path = args.get("filepath", self.filepath)

        encoding = "shift_jis"
        with open(path, "wt", encoding=encoding, errors="replace", newline="") as fout:
            self.filepath = path
            fout.write("Vocaloid Pose Data file\r\n")

            fout.write("\r\n")
            fout.write("%s;\t\t// 親ファイル名\r\n" % self.osm_name)
            fout.write("%d;\t\t\t\t// 総ポーズボーン数\r\n" % len(self.bones))
            fout.write("\r\n")

            for i, b in enumerate(self.bones):
                fout.write("Bone%d{%s\r\n" % (i, b.bone_name))
                fout.write("  %f,%f,%f;\t\t\t\t// trans x,y,z\r\n" % tuple(b.location))
                fout.write("  %f,%f,%f,%f;\t\t// Quaternion x,y,z,w\r\n" % tuple(b.rotation))
                fout.write("}\r\n")
                fout.write("\r\n")

            for i, m in enumerate(self.morphs):
                fout.write("Morph%d{%s\r\n" % (i, m.morph_name))
                fout.write("  %f;\t\t\t\t// weight\r\n" % m.weight)
                fout.write("}\r\n")
                fout.write("\r\n")

