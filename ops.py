# Description: Operator definitions for Sakura Poselib

import bpy
import sys, inspect
from bpy.props import *
from mathutils import Vector, Quaternion, Matrix
import math

from . import mmd
from . import internal

from .props import get_active_poselib, get_active_book, get_active_pose, get_active_bone

# checkver: Check blender if pose_library attribute 
def checkver(armature: bpy.types.Object) -> bool:
	return hasattr(armature, "pose_library")


# check armature: Check if the active object is an armature
def is_armature(obj: bpy.types.Object) -> bool:
	if not obj or not obj.pose:
		return False
	return True

# Operator: Convert from Pose Library
class SPL_OT_LoadFromPoseLibrary( bpy.types.Operator ):
	bl_idname = "spl.load_from_poselibrary"
	bl_label = "Load from Pose Library"
	bl_description = "Load the active Pose Library to PoseBook"
	bl_options = {'REGISTER', 'UNDO'}

	@classmethod
	def poll(cls, context):
		# Check active object is an armature
		obj = context.object
		if not is_armature(obj):
			return False

		# Check Blender version if pose_library attribute is available
		if not checkver(context.object):
			return False

		# Check if the armature has Pose Library
		if not obj.pose_library:
			return False

		# All checks passed
		return True

	# Execute the operator
	def execute(self, context):
		spl = get_active_poselib(context)
		book = spl.add_book()
		spl.active_book_index = len(spl.books) - 1

		internal.convert_from_poselib(book)
		return {'FINISHED'}


# Operator: Convert PoseBook to Pose Library 
class SPL_OT_ConvertToPoseLibrary( bpy.types.Operator ):
	bl_idname = "spl.convert_to_poselibrary"
	bl_label = "Convert to Pose Library"
	bl_description = "Convert the active PoseBook to Pose Library format"
	bl_options = {'REGISTER', 'UNDO'}

	@classmethod
	def poll(cls, context):
		arm = context.object
		# Check Blender version if pose_library attribute is available
		if not checkver(arm):
			return False

		# Check if the pose library is not empty
		book = get_active_book(arm.sakura_poselib)
		if not book or not book.poses:
			return False

		# All checks passed
		return True

	# Execute the operator
	def execute(self, context):
		arm = context.object
		book = get_active_book(arm.sakura_poselib)
		if not book:
			self.report({'ERROR'}, "No active PoseBook")
			return {'CANCELLED'}

		internal.convert_to_poselib(book)
		return {'FINISHED'}

# Operator: Send to mmd_tools Bone Morph operator
class SPL_OT_SendToMMDTools( bpy.types.Operator ):
	bl_idname = "spl.send_to_mmdtools"
	bl_label = "Send to mmd_tools"
	bl_description = "Send active PoseBook to mmd_tools Bone Morphs"
	bl_options = {'REGISTER', 'UNDO'}

	@classmethod
	def poll(cls, context):
		# Check active object is an armature
		arm = context.object
		if not is_armature(arm):
			return False

		# Check if mmd_tools is installed and the armature is an MMD model
		if not mmd.is_mmd_tools_installed() or not mmd.get_model_root(arm):
			return False

		book = get_active_book(arm.sakura_poselib)
		if not book or not book.poses:
			return False

		# All checks passed
		return True

	# Execute the operator
	def execute(self, context):
		spl = get_active_poselib(context)
		book = get_active_book(spl)
		if not book or not book.poses:
			self.report({'ERROR'}, "PoseBook is not selected or empty")
		
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
	def poll(cls, context):
		# Check active object is an armature
		arm = context.object
		if not is_armature(arm):
			return False

		# Check if mmd_tools is installed and the armature is an MMD model
		if not mmd.is_mmd_tools_installed() or not mmd.get_model_root(arm):
			return False

		# All checks passed
		return True

	# Execute the operator
	def execute(self, context):
		arm = context.object
		spl = get_active_poselib(context)

		book = spl.add_book()
		book.name = f"{arm.name}+_bonemorph"
		spl.active_book_index = len(spl.books) - 1

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
	def poll(cls, context):
		spl = get_active_poselib(context)
		book = get_active_book(spl)
		return book and book.poses

	# Execute the operator
	def execute(self, context):
		spl = get_active_poselib(context)
		book = get_active_book(spl)
		if not book or not book.poses:
			self.report({'ERROR'}, "PoseBook is not selected or empty")
			return False

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
	def poll(cls, context):
		return context.object and is_armature(context.object)

	# Execute the operator
	def execute(self, context):
		spl = get_active_poselib(context)
		book = spl.add_book()
		spl.active_book_index = len(spl.books) - 1

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

	@classmethod
	def poll(cls, context):
		spl = get_active_poselib(context)
		book = get_active_book(spl)
		return book and book.poses

	# Execute the operator
	def execute(self, context):
		spl = get_active_poselib(context)
		book = get_active_book(spl)
		if not book or not book.poses:
			self.report({'ERROR'}, "PoseBook is not selected or empty")
			return False

		# Save poses to file
		internal.save_book_to_csv(book, self.filepath, self.scale )

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
	def poll(cls, context):
		return context.object and is_armature(context.object)

	# Execute the operator
	def execute(self, context):
		spl = get_active_poselib(context)
		book = spl.add_book()
		spl.active_book_index = len(spl.books) - 1

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
	def poll(cls, context):
		return is_armature(context.object)

	# Execute the operator
	def execute(self, context):
		spl = get_active_poselib(context)

		# Add a new category
		book = spl.add_book()
		book.name = "New PoseBook"
		spl.active_book_index = len(spl.books) - 1

		return {'FINISHED'}

# Operator: Remove Category
class SPL_OT_RemovePoseBook( bpy.types.Operator ):
	bl_idname = "spl.remove_book"
	bl_label = "Remove PoseBook"
	bl_description = "Remove active PoseBook"
	bl_options = {'REGISTER', 'UNDO'}


	@classmethod
	def poll(cls, context):
		return is_armature(context.object)

	# Execute the operator
	def execute(self, context):
		spl = get_active_poselib(context)

		# Remove the selected category
		index = spl.active_book_index
		if index >= 0:
			spl.books.remove(index)
		else:
			self.report({'ERROR'}, "No active PoseBook")
			return {'CANCELLED'}

		spl.active_book_index = max(0, index - 1)
		

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
	def poll(cls, context):
		arm = context.object
		if not is_armature(arm):
			return False
		
		book = get_active_book(arm.sakura_poselib)
		if not book or not book.poses:
			return False

		if get_active_pose(book) is None:
			return False

		return True

	def execute(self, context):
		arm = context.object
		book = get_active_book(arm.sakura_poselib)
		pose = book.poses[self.pose_index] if self.pose_index >= 0 else get_active_pose(book)

		if pose is None:
			self.report({'WARNING'}, "Pose not found")
			return {'CANCELLED'}

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

	def execute(self, context):
		arm = context.object
		spl = get_active_poselib(context)
		book = get_active_book(spl)

		if not book: # Create new
			book = spl.add_book()
			book.name = "New PoseBook"

		# Create new pose container
		new_pose = book.poses.add()
		new_pose.name = self.pose_name

		# Save only bones contributing to the deformation
		for bone in arm.pose.bones:
			if self.only_visible_bones:
				if not internal.is_pose_bone_visible(bone):
					continue

			if bone.matrix_basis != Matrix.Identity(4): # Check if the bone is affected by the pose
				bd = new_pose.bones.add()
				bd.name = bone.name
				bd.location = bone.location
				bd.rotation = internal.get_pose_bone_rotation_quaternion(bone)
				bd.scale = bone.scale
		
		# Set the new pose as active
		book.active_pose_index = len(book.poses) - 1
		
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

	def execute(self, context):
		# print("Replace Pose", self.pose_index)
		arm = context.object
		book = get_active_book(arm.sakura_poselib)

		# Get the target pose, if pose_index is negative, use the active pose
		pose_index = self.pose_index if self.pose_index >= 0 else book.active_pose_index

		# check index is valid
		if pose_index < 0 or pose_index >= len(book.poses):
			self.report({'WARNING'}, "Invalid pose index")
			return {'CANCELLED'}

		# Replace (Overwrite) selected pose
		target_pose = book.poses[pose_index]
		target_pose.bones.clear()

		# Save only bones contributing to the deformation
		for bone in arm.pose.bones:
			if self.only_visible_bones:
				if not internal.is_pose_bone_visible(bone):
					continue

			if bone.matrix_basis != Matrix.Identity(4):
				bd = target_pose.bones.add()
				bd.name = bone.name
				bd.location = bone.location
				bd.rotation = internal.get_pose_bone_rotation_quaternion(bone)
				bd.scale = bone.scale

		return {'FINISHED'}

# Operator: Remove Active Pose from Pose List
class SPL_OT_RemovePose(bpy.types.Operator):
	bl_idname = "spl.remove_pose"
	bl_label = "Remove Pose"
	bl_description = "Remove the selected pose from the PoseBook"
	bl_options = {'REGISTER', 'UNDO'}

	@classmethod
	def poll(cls, context):
		arm = context.object
		book = get_active_book(arm.sakura_poselib)
		if not book or not book.poses:
			return False
		
		pose = get_active_pose(book)
		if not pose:
			return False
		
		return True
	def execute(self, context):
		arm = context.object
		book = get_active_book(arm.sakura_poselib)

		# Remove the active pose from the poses collection
		book.poses.remove(book.active_pose_index)

		# Decrement the active_pose_index
		book.active_pose_index -= 1
		if book.active_pose_index < 0:
			book.active_pose_index = 0

		return {'FINISHED'}



# Opereator: Auto set pose category
class SPL_OT_AutoSetPoseCategory( bpy.types.Operator ):
	bl_idname = "spl.auto_set_pose_category"
	bl_label = "Auto Set Pose Category"
	bl_description = "Automatically set the category of the poses in the PoseBook (guess from the pose name)"
	bl_options = {'REGISTER', 'UNDO'}

	@classmethod
	def poll(cls, context):
		arm = context.object
		if not is_armature(arm):
			return False
		
		book = get_active_book(arm.sakura_poselib)
		if not book or not book.poses:
			return False

		return True

	def execute(self, context):
		spl = get_active_poselib(context)
		book = get_active_book(spl)

		if not book:
			return {'CANCELLED'}

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

	def execute(self, context):
		arm = context.object
		book = get_active_book(arm.sakura_poselib)

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



# helper: check if the quaternion is less than minimal
def is_rotation_minimal(q, threshold=1e-6):
    q_normalized = q.normalized()
    dot_product = q_normalized.dot(Quaternion())
    angle_diff = 2 * math.acos(min(1.0, abs(dot_product))) 
    return angle_diff < threshold


# Operator: Clean Poses (remove unused/invalid bones in poses within the active posebook)
class SPL_OT_CleanPoses( bpy.types.Operator ):
	bl_idname = "spl.clean_poses"
	bl_label = "Clean Poses"
	bl_description = "Remove unused/invalid bones in poses within the active posebook"
	bl_options = {'REGISTER', 'UNDO'}

	report_only: BoolProperty(
		name="Report Only",
		description="Only report unused/invalid bones, do not remove them",
		default=False
	)

	@classmethod
	def poll(cls, context):
		arm = context.object
		book = get_active_book(arm.sakura_poselib)
		if not book or not book.poses:
			return False
		return True

	# Show Options first
	def invoke(self, context, event):
		return context.window_manager.invoke_props_dialog(self)

	def execute(self, context):
		arm = context.object
		book = get_active_book(arm.sakura_poselib)

		# Remove unused/invalid bones in poses within the active posebook
		for pose in book.poses:
			bone_to_remove = {} # {bone_name: reason for removal}
			for bone in pose.bones:

				# Remove bones that are not in the armature
				if not bone.name in arm.data.bones:
					bone_to_remove[bone.name] = "Not in armature"
					continue

				# Remove bones that are not contributing to the deformation
				if bone.location.length < 1e-6 and is_rotation_minimal(bone.rotation) and (bone.scale - Vector((1,1,1))).length < 1e-6:
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

	def execute(self, context):
		arm = context.object
		book = get_active_book(arm.sakura_poselib)
		pose = get_active_pose(book)


		# Remove the bone from the pose
		if self.bone_index >= 0 and self.bone_index < len(pose.bones):
			pose.bones.remove(self.bone_index)
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
	def poll(cls, context):
		return context.selected_pose_bones

	def execute(self, context):
		arm = context.object
		book = get_active_book(arm.sakura_poselib)
		pose = get_active_pose(book)

		# Add selected bones to the pose
		for bone in context.selected_pose_bones:
			bd = pose.bones.get(bone.name) # Use existing bone data if exists

			if not bd: # Create new bone data if not exists
				bd = pose.bones.add()
				bd.name = bone.name

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
		poselilst = get_active_book(context.object.sakura_poselib)
		pose_index = poselilst.active_pose_index

		# Check index is valid
		if pose_index < 0 or pose_index >= len(poselilst.poses):
			self.report({'WARNING'}, "Invalid pose index")
			return {'CANCELLED'}
		
		# Move the pose
		if self.direction == 'UP' and pose_index > 0:
			poselilst.poses.move(pose_index, pose_index - 1)
			poselilst.active_pose_index -= 1
		elif self.direction == 'DOWN' and pose_index < len(poselilst.poses) - 1:
			poselilst.poses.move(pose_index, pose_index + 1)
			poselilst.active_pose_index += 1
		elif self.direction == 'TOP' and pose_index > 0:
			poselilst.poses.move(pose_index, 0)
			poselilst.active_pose_index = 0
		elif self.direction == 'BOTTOM' and pose_index < len(poselilst.poses) - 1:
			poselilst.poses.move(pose_index, len(poselilst.poses) - 1)
			poselilst.active_pose_index = len(poselilst.poses) - 1

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
		spl = get_active_poselib(context)
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

	def execute(self, context):
		spl = get_active_poselib(context)
		book = get_active_book(spl)

		# Reset all pose values
		for pose in book.poses:
			pose['value'] = 0.0
		
		internal.update_combined_pose(book)

		return {'FINISHED'}



# Callback: Draw pose name in the 3D View
import bgl
import blf

def draw_pose_name_callback(self, context):
	if context.mode != 'POSE':
		return
	if context.object.type != 'ARMATURE':
		return

	arm = context.object
	book = get_active_book(arm.sakura_poselib)
	pose = get_active_pose(book)

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
		spl = get_active_poselib(context)
		book = get_active_book(spl)

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
				book = get_active_book(spl)
				pose = get_active_pose(book)
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
		spl = get_active_poselib(context)
		book = get_active_book(spl)
		if not book:
			self.report({'WARNING'}, "No PoseBook found, cannot run operator")
			return {'CANCELLED'}
		
		pose = get_active_pose(book)
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
	bl_description = "Batch rename bones in the all PoseBooks within the active Armature (for retargeting)"
	bl_options = {'REGISTER', 'UNDO'}

	search: bpy.props.StringProperty(name="Search", default="")
	replace: bpy.props.StringProperty(name="Replace", default="")
	use_regex: bpy.props.BoolProperty(name="Use Regular Expressions", default=False)


	def draw(self, context):
		layout = self.layout
		layout.use_property_split = True
		layout.use_property_decorate = False

		layout.prop(self, "search")
		layout.prop(self, "replace")
		layout.prop(self, "use_regex")

	def invoke(self, context, event):
		return context.window_manager.invoke_props_dialog(self)


	@classmethod
	def poll(cls, context):
		return context.object is not None and context.object.type == 'ARMATURE'

	def execute(self, context):
		spl = get_active_poselib(context)

		# Get all pose lists
		for posebook in spl.books:
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
