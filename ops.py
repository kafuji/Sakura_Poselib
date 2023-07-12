# Description: Operator definitions for Sakura Poselib

import bpy
import sys, inspect
from bpy.props import *
from mathutils import Vector, Quaternion, Matrix
import math

from . import mmd
from . import internal

from .props import get_poselib, get_poselib_from_context
from .poll_requirements import *


# Operator: Convert from Pose Library
class SPL_OT_LoadFromPoseLibrary( bpy.types.Operator ):
    bl_idname = "spl.load_from_poselibrary"
    bl_label = "Load from Pose Library"
    bl_description = "Load the active Pose Library to PoseBook"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    @requires_active_armature
    @requires_blender_pose_library
    def poll(cls, context):
        return context.object.pose_library

    # Execute the operator
    def execute(self, context):
        spl = get_poselib_from_context(context)
        book = spl.add_book()

        internal.convert_from_poselib(book)
        return {'FINISHED'}


# Operator: Convert PoseBook to Pose Library 
class SPL_OT_ConvertToPoseLibrary( bpy.types.Operator ):
    bl_idname = "spl.convert_to_poselibrary"
    bl_label = "Convert to Pose Library"
    bl_description = "Convert the active PoseBook to Pose Library format"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    @requires_active_posebook
    @requires_blender_pose_library
    def poll(cls, context):
        return context.object.pose_library

    # Execute the operator
    def execute(self, context):
        spl = get_poselib_from_context(context)
        book = spl.get_active_book()

        internal.convert_to_poselib(book)
        return {'FINISHED'}

# Operator: Send to mmd_tools Bone Morph operator
class SPL_OT_SendToMMDTools( bpy.types.Operator ):
    bl_idname = "spl.send_to_mmdtools"
    bl_label = "Send to mmd_tools"
    bl_description = "Send active PoseBook to mmd_tools Bone Morphs"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    @requires_poses
    def poll(cls, context):
        return True

    # Execute the operator
    def execute(self, context):
        spl = get_poselib_from_context(context)
        book = spl.get_active_book()

        # Convert the pose to mmd_tools Bone Morph
        internal.convert_poses_to_mmdtools(book)

        return {'FINISHED'}

# Operator: Load from mmd_tools Bone Morphs
class SPL_OT_LoadFromMMDTools( bpy.types.Operator ):
    bl_idname = "spl.load_from_mmdtools"
    bl_label = "Load from mmd_tools"
    bl_description = "Load mmd_tools Bone Morphs as new PoseBook"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    @requires_active_armature
    def poll(cls, context):
        # Check if mmd_tools is installed and the armature is an MMD model
        if not mmd.is_mmd_tools_installed() or not mmd.get_model_root(context.object):
            return False

        # All checks passed
        return True

    # Execute the operator
    def execute(self, context):
        arm = context.object
        spl = get_poselib_from_context(context)
        book = spl.add_book(name=f"{arm.name}+_bonemorph")

        # Convert from mmd_tools Bone Morph
        internal.load_poses_from_mmdtools(book)

        return {'FINISHED'}


from bpy_extras.io_utils import ExportHelper, ImportHelper

# Operator: Save Poses to Json
class SPL_OT_SaveToJson( bpy.types.Operator, ExportHelper ):
    bl_idname = "spl.save_to_json"
    bl_label = "Save to Json"
    bl_description = "Save active PoseBook to a Json file"
    bl_options = {'REGISTER', 'UNDO'}

    filter_glob: StringProperty(default="*.json", options={'HIDDEN'})
    filename_ext = '.json'

    @classmethod
    @requires_poses
    def poll(cls, context):
        return True

    # set self.filepath using book.name
    def invoke(self, context, event):
        arm = context.object
        spl = get_poselib_from_context(context)
        book = spl.get_active_book()
        self.filepath = arm.name + "_posebook_" + book.name
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    # Execute the operator
    def execute(self, context):
        spl = get_poselib_from_context(context)
        book = spl.get_active_book()
        # Save poses to file
        internal.save_book_to_json(book, self.filepath)

        return {'FINISHED'}


# Operator: Load PoseBook from file
class SPL_OT_LoadFromJson( bpy.types.Operator, ImportHelper ):
    bl_idname = "spl.load_from_json"
    bl_label = "Load from Json"
    bl_description = "Load a PoseBook from a Json file"
    bl_options = {'REGISTER', 'UNDO'}

    filter_glob: StringProperty(default="*.json", options={'HIDDEN'})
    filename_ext = '.json'

    @classmethod
    @requires_active_armature
    def poll(cls, context):
        return True

    # Execute the operator
    def execute(self, context):
        spl = get_poselib_from_context(context)
        book = spl.add_book()

        # Load poses from file
        internal.load_book_from_json(book, self.filepath)
        return {'FINISHED'}

    # Invoke the operator
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}



# Operator: Save Poses to CSV
class SPL_OT_SaveToCSV( bpy.types.Operator, ExportHelper ):
    bl_idname = "spl.save_to_csv"
    bl_label = "Save to CSV"
    bl_description = "Save active PoseBook to a CSV file (compatible with PMX Editor)"
    bl_options = {'REGISTER', 'UNDO'}

    filter_glob: StringProperty(default="*.csv", options={'HIDDEN'})
    filename_ext = '.csv'

    scale: FloatProperty(
        name="Scale",
        description="Scale factor (Blender -> MMD)",
        default=12.5,
        min=1.0,
        max=100.0,
    )

    use_mmd_bone_names: BoolProperty(
        name="Use MMD Bone Names",
        description="Use MMD bone names (mmd_tools:mmd_bone.name) instead of Blender bone names",
        default=True,
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "scale")
        layout.prop(self, "use_mmd_bone_names")

    @classmethod
    @requires_poses
    def poll(cls, context):
        return True

    # set self.filepath using book.name
    def invoke(self, context, event):
        arm = context.object
        spl = get_poselib_from_context(context)
        book = spl.get_active_book()
        self.filepath = arm.name + "_posebook_" + book.name
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    # Execute the operator
    def execute(self, context):
        spl = get_poselib_from_context(context)
        book = spl.get_active_book()

        # Save poses to file
        internal.save_book_to_csv(book, self.filepath, self.scale, self.use_mmd_bone_names )

        return {'FINISHED'}


# Operator: Load PoseBook from CSV
class SPL_OT_LoadFromCSV( bpy.types.Operator, ImportHelper ):
    bl_idname = "spl.load_from_csv"
    bl_label = "Load from CSV"
    bl_description = "Load a PoseBook from a CSV file (compatible with PMX Editor)"
    bl_options = {'REGISTER', 'UNDO'}

    filter_glob: StringProperty(default="*.csv", options={'HIDDEN'})
    filename_ext = '.csv'

    scale: FloatProperty(
        name="Scale",
        description="Scale factor (MMD -> Blender)",
        default=0.08,
        min=1.0,
        max=100.0,
    )

    @classmethod
    @requires_active_armature
    def poll(cls, context):
        return True

    # Execute the operator
    def execute(self, context):
        spl = get_poselib_from_context(context)
        book = spl.add_book()

        # Load poses from file
        internal.load_book_from_csv(book, self.filepath, self.scale )
        return {'FINISHED'}

    # Invoke the operator
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


# Operator: Add PoseBook
class SPL_OT_AddPoseBook( bpy.types.Operator ):
    bl_idname = "spl.add_book"
    bl_label = "Add PoseBook"
    bl_description = "Add a new PoseBook. PoseBook is a collection of poses"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    @requires_active_armature
    def poll(cls, context):
        return True

    # Execute the operator
    def execute(self, context):
        spl = get_poselib_from_context(context)

        # Add a new PoseBook
        spl.add_book("New PoseBook")

        return {'FINISHED'}

# Operator: Remove PoseBook
class SPL_OT_RemovePoseBook( bpy.types.Operator ):
    bl_idname = "spl.remove_book"
    bl_label = "Remove PoseBook"
    bl_description = "Remove active PoseBook"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    @requires_active_posebook
    def poll(cls, context):
        return True

    # Execute the operator
    def execute(self, context):
        spl = get_poselib_from_context(context)
        spl.remove_active_book()

        return {'FINISHED'}



# Operator: Apply Pose
class SPL_OT_ApplyPose( bpy.types.Operator ):
    bl_idname = "spl.apply_pose"
    bl_label = "Apply"
    bl_description = "Apply the selected pose to armature"
    bl_options = {'REGISTER', 'UNDO'}

    pose_index: IntProperty(default=-1)
    influence: FloatProperty(
        name="Influence",
        description="Influence of the pose on the armature (0.0 to 1.0)",
        default=1.0,
        min=0.0,
        max=1.0,
    )

    @classmethod
    @requires_active_pose
    def poll(cls, context):
        return True

    def execute(self, context):
        spl = get_poselib_from_context(context)
        book = spl.get_active_book()
        pose = book.get_active_pose()

        internal.apply_pose(pose, self.influence, reset_others=True )
        return {'FINISHED'}


# Operator: Add Pose from current Armature
class SPL_OT_AddPose( bpy.types.Operator ):
    bl_idname = "spl.add_pose"
    bl_label = "Add Pose"
    bl_description = "Add a new pose from the current armature pose"
    bl_options = {'REGISTER', 'UNDO'}

    pose_name: StringProperty(
        name="New Pose",
        description="Name of the new pose",
        default="New Pose",
    )

    only_visible_bones: BoolProperty(
        name="Only Visible Bones", 
        description="Evaluate only bones visible in the viewport",
        default=True
    )

    @classmethod
    @requires_active_armature
    def poll(cls, context):
        return True


    def execute(self, context):
        arm = context.object
        spl = get_poselib_from_context(context)
        book = spl.get_active_book()

        if not book: # Create new
            book = spl.add_book("New PoseBook")

        # Create new pose container
        new_pose = book.add_pose( self.pose_name )

        # Save only bones contributing to the deformation
        for bone in arm.pose.bones:
            if self.only_visible_bones:
                if not internal.is_pose_bone_visible(bone):
                    continue

            if bone.matrix_basis != Matrix.Identity(4): # Check if the bone is affected by the pose
                bd = new_pose.add_bone(bone.name)
                bd.location = bone.location
                bd.rotation = internal.get_pose_bone_rotation_quaternion(bone)
                bd.scale = bone.scale
        
        return {'FINISHED'}


# Operator: Replace existing pose
class SPL_OT_ReplacePose( bpy.types.Operator ):
    bl_idname = "spl.replace_pose"
    bl_label = "Replace"
    bl_description = "Replace the selected pose with the current armature pose (overwrite)"
    bl_options = {'UNDO'}

    pose_index: IntProperty(default=-1)

    only_visible_bones: BoolProperty(
        name="Only Visible Bones", 
        description="Evaluate only bones visible in the viewport",
        default=True
    )

    @classmethod
    @requires_poses
    def poll(cls, context):
        return True

    def execute(self, context):
        # print("Replace Pose", self.pose_index)
        arm = context.object
        spl = get_poselib_from_context(context)
        book = spl.get_active_book()

        # Get the target pose, if pose_index is negative, use the active pose
        pose_index = self.pose_index if self.pose_index >= 0 else book.active_pose_index

        # check index is valid
        if pose_index < 0 or pose_index >= len(book.poses):
            self.report({'WARNING'}, "Invalid pose index")
            return {'CANCELLED'}

        # Replace (Overwrite) selected pose
        target_pose = book.get_pose_by_index(pose_index)

        # Save only bones contributing to the deformation
        for bone in arm.pose.bones:
            if self.only_visible_bones:
                if not internal.is_pose_bone_visible(bone):
                    continue

            if bone.matrix_basis != Matrix.Identity(4):
                bd = target_pose.get_bone_by_name(bone.name) or target_pose.add_bone(bone.name)
                bd.location = bone.location
                bd.rotation = internal.get_pose_bone_rotation_quaternion(bone)
                bd.scale = bone.scale
            else: # Remove bone from pose if it is not affected by the pose
                bd = target_pose.get_bone_by_name(bone.name)
                if bd:
                    target_pose.remove_bone(bd.name)


        return {'FINISHED'}

# Operator: Remove Active Pose from Pose List
class SPL_OT_RemovePose(bpy.types.Operator):
    bl_idname = "spl.remove_pose"
    bl_label = "Remove Pose"
    bl_description = "Remove the selected pose from the PoseBook"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    @requires_active_pose
    def poll(cls, context):
        return True

    def execute(self, context):
        spl = get_poselib_from_context(context)
        book = spl.get_active_book()

        # Remove the active pose from the poses collection
        book.remove_pose_by_index(book.active_pose_index)

        return {'FINISHED'}


# Operator: Move Pose to another PoseBook
class SPL_OT_MovePoseToPoseBook(bpy.types.Operator):
    bl_idname = "spl.move_pose_to_posebook"
    bl_label = "Move Pose to PoseBook"
    bl_description = "Move the active pose to another PoseBook"
    bl_options = {'REGISTER', 'UNDO'}

    posebook_name: StringProperty(
        name="PoseBook",
        description="Name of the target PoseBook",
        default="",
    )

    do_copy: BoolProperty(
        name="Copy",
        description="Copy the pose instead of moving it",
        default=False
    )

    @classmethod
    @requires_active_pose
    def poll(cls, context):
        return True

    # show Options first
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)
    
    # Draw the options
    def draw(self, context):
        l = self.layout
        l.use_property_split = True
        l.prop_search(self, "posebook_name", context.object.sakura_poselib, "books", text="PoseBook")
        l.prop(self, "do_copy")

    def execute(self, context):
        spl = get_poselib_from_context(context)
        book = spl.get_active_book()
        pose = book.get_active_pose()

        # Get the target posebook
        target_book = spl.get_book_by_name(self.posebook_name)
        if not target_book:
            self.report({'WARNING'}, "PoseBook not found")
            return {'CANCELLED'}
        if target_book == book:
            self.report({'WARNING'}, "Cannot move to the same PoseBook")
            return {'CANCELLED'}

        # Move the pose to the target posebook
        active_book_index = spl.active_book_index
        spl.active_book_index = spl.books.find(target_book.name)
        newpose = target_book.add_pose()
        newpose.copy_from(pose)
        spl.active_book_index = active_book_index

        # Remove the pose from the current posebook
        if not self.do_copy:
            book.remove_pose(pose)

        return {'FINISHED'}


# Opereator: Auto set pose category
class SPL_OT_AutoSetPoseCategory( bpy.types.Operator ):
    bl_idname = "spl.auto_set_pose_category"
    bl_label = "Auto Set Pose Category"
    bl_description = "Automatically set the category of the poses in the PoseBook (guess from the pose name)"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    @requires_poses
    def poll(cls, context):
        return True

    def execute(self, context):
        spl = get_poselib_from_context(context)
        book = spl.get_active_book()

        for pose in book.poses:
            pose.category = internal.guess_pose_category(pose.name)

        return {'FINISHED'}



# Operator: Select bones used in the pose
class SPL_OT_SelectBonesInPose( bpy.types.Operator ):
    bl_idname = "spl.select_bones_in_pose"
    bl_label = "Select Pose Bones"
    bl_description = "Select bones used in the pose"
    bl_options = {'REGISTER', 'UNDO'}

    pose_index: IntProperty()

    @classmethod
    @requires_poses
    def poll(cls, context):
        return True

    def execute(self, context):
        arm = context.object
        spl = get_poselib_from_context(context)
        book = spl.get_active_book()

        # Get the target pose, if pose_index is negative, use the active pose
        pose_index = self.pose_index if self.pose_index >= 0 else book.active_pose_index

        # check index is valid
        if pose_index < 0 or pose_index >= len(book.poses):
            self.report({'WARNING'}, "Invalid pose index")
            return {'CANCELLED'}

        # Deselect all bones
        for bone in arm.data.bones:
            bone.select = False

        # Select bones used in the pose
        pose = book.poses[pose_index]

        for bone_name in pose.bones.keys():
            if not bone_name in arm.data.bones:
                continue

            pbone = arm.pose.bones[bone_name]
            pbone.bone.hide_select = False
            pbone.bone.select = True

            # Show the bone in the viewport
            pbone.bone.hide = False

            # show armature layer if the bone is on it
            for i in range(32):
                if pbone.bone.layers[i]:
                    arm.data.layers[i] = True

        return {'FINISHED'}


def is_matrix_almost_equal(m1, m2, threshold=1e-6):
    """Check if two matrices are almost equal"""
    return all(abs(x1 - x2) < threshold for x1, x2 in zip(m1, m2))

def is_vector_almost_equal(v1, v2, threshold=1e-6):
    """Check if two vectors are almost equal"""
    return all(abs(x1 - x2) < threshold for x1, x2 in zip(v1, v2))

def is_rotation_minimal(q, threshold=1e-6):
    """Check if the quaternion is less than minimal"""
    q_normalized = q.normalized()
    dot_product = q_normalized.dot(Quaternion())
    angle_diff = 2 * math.acos(min(1.0, abs(dot_product))) 
    return angle_diff < threshold

def is_translation_minimal(v, threshold=1e-6):
    """Check if the location vector is less than minimal"""
    return any(abs(x) > threshold for x in v)

def is_scale_minimal(v, threshold=1e-6):
    """Check if the scale vector is less than minimal"""
    return any(abs(x - 1) > threshold for x in v)

def is_transform_minimal( loc, rot, scale, threshold=1e-6 ):
    """Check if the transform is less than minimal"""
    return is_translation_minimal(loc, threshold) or is_rotation_minimal(rot, threshold) or is_scale_minimal(scale, threshold)


# Operator: Clean Poses (remove unused/invalid bones in poses within the active posebook)
class SPL_OT_CleanPoses( bpy.types.Operator ):
    bl_idname = "spl.clean_poses"
    bl_label = "Clean Poses"
    bl_description = "Remove/report unused/invalid bones in poses within the active posebook"
    bl_options = {'REGISTER', 'UNDO'}

    check_name: BoolProperty(
        name="Check Bone Name",
        description="Remove/report bones with invalid names (which are not in the armature)",
        default=True
    )

    check_transform: BoolProperty(
        name="Check Bone Transform",
        description="Remove bones which are not contributing to the pose (i.e. bones with minimal transform)",
        default=True
    )

    threshold: FloatProperty(
        name="Threshold",
        description="Lower than this threshold, the bone is considered as not contributing to the pose",
        default=1e-5,
        min=1e-6,
        max=1e-3,
        soft_min=1e-6,
        soft_max=1e-3,
        precision=6
    )

    report_only: BoolProperty(
        name="Report Only",
        description="Show the report only (in the Inforation view), don't remove any bones",
        default=False
    )

    @classmethod
    @requires_poses
    def poll(cls, context):
        return True

    # Show Options first
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    # Draw options
    def draw(self, context):
        l = self.layout
        l.use_property_split = True
        l.use_property_decorate = False

        l.prop(self, "check_name")
        l.prop(self, "check_transform")
        if self.check_transform:
            l.prop(self, "threshold")
        l.prop(self, "report_only")

    def execute(self, context):
        arm = context.object
        spl = get_poselib_from_context(context)
        book = spl.get_active_book()

        # Remove unused/invalid bones in poses within the active posebook
        for pose in book.poses:
            bone_to_remove = {} # {bone_name: reason for removal}
            for bone in pose.bones:
                if self.check_name:
                    # Remove bones that are not in the armature
                    if not bone.name in arm.data.bones:
                        bone_to_remove[bone.name] = "Not in armature"
                        continue
                if self.check_transform:
                    # Remove bones that are not contributing to the deformation
                    if is_transform_minimal(bone.location, bone.rotation, bone.scale, self.threshold):
                        bone_to_remove[bone.name] = "No deformation"
                        continue

            # Remove the bones
            for bone_name,reason in bone_to_remove.items():
                if not self.report_only:
                    pose.bones.remove(pose.bones.find(bone_name))
                self.report({'INFO'}, "Bone '{}' in pose '{}' - {}".format(bone_name, pose.name, reason))

            if not self.report_only:
                pose.active_bone_index = max( 0, min(pose.active_bone_index, len(pose.bones)-1) )

        return {'FINISHED'}


# Oerator: Remove Bone from Pose
class SPL_OT_RemoveBoneFromPose( bpy.types.Operator ):
    bl_idname = "spl.remove_bone_from_pose"
    bl_label = "Remove Bone from Pose"
    bl_options = {'REGISTER', 'UNDO'}

    bone_index: IntProperty()

    @classmethod
    @requires_active_pose
    def poll(cls, context):
        return True

    def execute(self, context):
        spl = get_poselib_from_context(context)
        book = spl.get_active_book()
        pose = book.get_active_pose()

        # Remove the bone from the pose
        if self.bone_index >= 0 and self.bone_index < len(pose.bones):
            pose.bones.remove(self.bone_index)
            pose.active_bone_index = max( 0, min(pose.active_bone_index, len(pose.bones)-1) )
        else:
            self.report({'WARNING'}, "Bone not found")
            return {'CANCELLED'}

        return {'FINISHED'}


# Operator: Add selected bone to pose
class SPL_OT_AddSelectedBoneToPose( bpy.types.Operator ):
    bl_idname = "spl.add_selected_bone_to_pose"
    bl_label = "Add Selected Bone to Pose"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    @requires_active_pose
    def poll(cls, context):
        return context.selected_pose_bones

    def execute(self, context):
        arm = context.object
        spl = get_poselib_from_context(context)
        book = spl.get_active_book()
        pose = book.get_active_pose()

        # Add selected bones to the pose
        for bone in context.selected_pose_bones:
            bd = pose.bones.get(bone.name) # Use existing bone data if exists

            if not bd: # Create new bone data if not exists
                bd = pose.add_bone(bone.name)

            # Update bone data
            bd.location = bone.location
            bd.rotation = internal.get_pose_bone_rotation_quaternion(bone)
            bd.scale = bone.scale

        return {'FINISHED'}

# Operator: Move Pose Up/Down Top/Bottom in the Pose List
class SPL_OT_MovePose( bpy.types.Operator ):
    bl_idname = "spl.move_pose"
    bl_label = "Move Pose"

    direction: EnumProperty(
        items = (
            ('UP', "Up", ""),
            ('DOWN', "Down", ""),
            ('TOP', "Top", ""),
            ('BOTTOM', "Bottom", ""),
        )
    )

    def execute(self, context):
        spl = get_poselib_from_context(context)
        book = spl.get_active_book()
        pose_index = book.active_pose_index

        # Check index is valid
        if pose_index < 0 or pose_index >= len(book.poses):
            self.report({'WARNING'}, "Invalid pose index")
            return {'CANCELLED'}
        
        # Move the pose
        if self.direction == 'UP' and pose_index > 0:
            book.poses.move(pose_index, pose_index - 1)
            book.active_pose_index -= 1
        elif self.direction == 'DOWN' and pose_index < len(book.poses) - 1:
            book.poses.move(pose_index, pose_index + 1)
            book.active_pose_index += 1
        elif self.direction == 'TOP' and pose_index > 0:
            book.poses.move(pose_index, 0)
            book.active_pose_index = 0
        elif self.direction == 'BOTTOM' and pose_index < len(book.poses) - 1:
            book.poses.move(pose_index, len(book.poses) - 1)
            book.active_pose_index = len(book.poses) - 1

        return {'FINISHED'}


# Operator: Move PoseBook Up/Down in the PoseLib
class SPL_OT_MovePoseBook( bpy.types.Operator ):
    bl_idname = "spl.move_book"
    bl_label = "Move PoseBook"

    direction: EnumProperty(
        items = (
            ('UP', "Up", ""),
            ('DOWN', "Down", ""),
        )
    )

    def execute(self, context):
        spl = get_poselib_from_context(context)
        book_index = spl.active_book_index

        # Check index is valid
        if book_index < 0 or book_index >= len(spl.books):
            self.report({'WARNING'}, "Invalid pose index")
            return {'CANCELLED'}
        
        # Move the pose
        if self.direction == 'UP' and book_index > 0:
            spl.books.move(book_index, book_index - 1)
            spl.active_book_index -= 1
        elif self.direction == 'DOWN' and book_index < len(spl.books) - 1:
            spl.books.move(book_index, book_index + 1)
            spl.active_book_index += 1

        return {'FINISHED'}


# Operator: Reset all value of the poses in the PoseBook
class SPL_OT_ResetPoseBook( bpy.types.Operator ):
    bl_idname = "spl.reset_book"
    bl_label = "Reset PoseBook"
    bl_description = "Reset all pose values to zero in the PoseBook"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    @requires_active_posebook
    def poll(cls, context):
        return True
   
    def execute(self, context):
        spl = get_poselib_from_context(context)
        book = spl.get_active_book()

        # Reset all pose values
        for pose in book.poses:
            pose['value'] = 0.0
        
        internal.update_combined_pose(book)
        return {'FINISHED'}


# Callback: Draw pose name in the 3D View
import blf

def draw_pose_name_callback(self, context):
    if context.mode != 'POSE':
        return
    if not context.object or not context.object.pose:
        return

    spl = get_poselib_from_context(context)
    book = spl.get_active_book()
    pose = book.get_active_pose()

    font_id = 0  # default font

    y_pos = 24
    y_step = 32

    # draw pose name
    blf.enable(font_id, blf.SHADOW)
    blf.shadow(font_id, 5, 0.0, 0.0, 0.0, 1.0)
    blf.shadow_offset(font_id, 3, -3)

    # draw from bottom
    blf.size(font_id, 24, 72)
    blf.position(font_id, 15, y_pos, 0)
    blf.draw(font_id, f"Up/Down: Change Pose, Left/Right: Change Category")
    y_pos += y_step

    blf.size(font_id, 30, 72)
    blf.position(font_id, 15, y_pos, 0)
    if pose:
        blf.draw(font_id, f"PoseBook: {book.name}  Pose: {pose.name}")
    else:
        blf.draw(font_id, f"PoseBook: {book.name}  Pose: None")
    y_pos += y_step

    blf.size(font_id, 32, 72)
    blf.position(font_id, 15, y_pos, 0)
    blf.draw(font_id, f"Pose Preview")


    blf.disable(font_id, blf.SHADOW)
    return

# Operator: Preview Pose (Modal Operator)
class POSELIBPLUS_OT_pose_preview( bpy.types.Operator ):
    bl_idname = "spl.pose_preview"
    bl_label = "Sakura Poselib Pose Preview"

    def modal(self, context, event):
        spl = get_poselib_from_context(context)
        book = spl.get_active_book()

        if not book:
            return {'CANCELLED'}

        # Events to handle
        MOVEUP = ('UP_ARROW', 'PAGE_UP', 'WHEELUPMOUSE')
        MOVEDOWN = ('DOWN_ARROW','PAGE_DOWN', 'WHEELDOWNMOUSE')
        CAT_UP = ('LEFT_ARROW', 'END')
        CAT_DOWN = ('RIGHT_ARROW', 'HOME')
        ALL_EVENTS = MOVEUP + MOVEDOWN + CAT_UP + CAT_DOWN

        #print(f"POSELIBPLUS_OT_pose_preview modal event.type: {event.type}, event.value: {event.value}")

        if event.value == 'PRESS':
            # Pose Index Up/Down Control
            if event.type in ALL_EVENTS:
                if event.type in MOVEUP:
                    book.active_pose_index = max( 0, book.active_pose_index - 1 )
                elif event.type in MOVEDOWN:
                    book.active_pose_index = min( len(book.poses) - 1, book.active_pose_index + 1 )
                elif event.type in CAT_UP:
                    spl.active_book_index = max( 0, spl.active_book_index - 1 )
                elif event.type in CAT_DOWN:
                    spl.active_book_index = min( len(spl.books) - 1, spl.active_book_index + 1 )

                # Apply the active pose			
                book = spl.get_active_book()
                pose = book.get_active_pose()
                if pose:
                    internal.apply_pose( pose, 1.0, reset_others=True )


                return {'RUNNING_MODAL'}
            else:
                # Remove the preview handler
                bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
                return {'CANCELLED'}

        # Exit if the user presses keys other than the ones we handle or if the mode is not pose
        if context.mode != 'POSE':
            # Remove the preview handler
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            return {'CANCELLED'}

        # Check if the mouse cursor is inside the 3D View region
        region = context.region
        if not (0 <= event.mouse_region_x < region.width and 0 <= event.mouse_region_y < region.height):
            # Remove the preview handler
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            return {'CANCELLED'}


        return {'PASS_THROUGH'}

    def invoke(self, context, event):

        # Apply the active pose
        spl = get_poselib_from_context(context)
        book = spl.get_active_book()
        if not book:
            self.report({'WARNING'}, "No PoseBook found, cannot run operator")
            return {'CANCELLED'}
        
        pose = book.get_active_pose()
        if pose:
            internal.apply_pose( pose, 1.0, reset_others=True )

        if context.area.type == 'VIEW_3D':
            context.window_manager.modal_handler_add(self)
            # Add the pose name drawer handler
            args = (self, context)
            self._handle = bpy.types.SpaceView3D.draw_handler_add(draw_pose_name_callback, args, 'WINDOW', 'POST_PIXEL')
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "View3D not found, cannot run operator")
            return {'CANCELLED'}

    def cancel(self, context):
        # Remove the preview handler
        bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')

        return {'CANCELLED'}


import re
# Operator: Batch Rename Bones
class SPL_OT_BatchRenameBones(bpy.types.Operator):
    bl_idname = "spl.batch_rename_bones"
    bl_label = "Batch Rename Bones"
    bl_description = "Rename bones within all Pose Data in the active PoseBook (useful for retargeting)"
    bl_options = {'REGISTER', 'UNDO'}

    all_books: bpy.props.BoolProperty(name="Process All PoseBooks", default=False)
    search: bpy.props.StringProperty(name="Search", default="")
    replace: bpy.props.StringProperty(name="Replace", default="")
    use_regex: bpy.props.BoolProperty(name="Use Regex", default=False)

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        layout.prop(self, "all_books")
        layout.prop(self, "search")
        layout.prop(self, "replace")
        layout.prop(self, "use_regex")

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


    @classmethod
    @requires_active_posebook
    def poll(cls, context):
        return True

    def execute(self, context):
        spl = get_poselib_from_context(context)

        if self.all_books:
            books = spl.books # All posebooks
        else:
            books = [spl.get_active_book()] # Only the active posebook

        # Iterate through posebooks
        for posebook in books:
            for pose in posebook.poses:
                for bone_transform in pose.bones:
                    if self.use_regex:
                        try:
                            bone_transform.name = re.sub(self.search, self.replace, bone_transform.name)
                        except re.error as e:
                            self.report({'ERROR'}, f"Invalid regular expression: {e}")
                            return {'CANCELLED'}
                    else:
                        bone_transform.name = bone_transform.name.replace(self.search, self.replace)

        self.report({'INFO'}, "Batch renaming completed")
        return {'FINISHED'}


# Register & Unregister
import sys, inspect
def register():
    ops = [c[1] for c in inspect.getmembers(sys.modules[__name__], inspect.isclass) if issubclass(c[1], bpy.types.Operator)]

    for cls in ops:
        bpy.utils.register_class(cls)

    return

def unregister():
    ops = [c[1] for c in inspect.getmembers(sys.modules[__name__], inspect.isclass) if issubclass(c[1], bpy.types.Operator)]

    for cls in ops:
        bpy.utils.unregister_class(cls)
    
    return
