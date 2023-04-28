# Properties for Sakura Poselib
import bpy
from bpy.types import PropertyGroup
from bpy.props import *
from mathutils import Vector, Matrix
from typing import Optional

from .internal import update_combined_pose

###################################################
# Internal Functions
###################################################


# Resolve naming collision in the collection. self is the item just renamed.
def resolve_naming_collision(self, collection):
	except_me = [item for item in collection if item != self]
	name_set = {item.name for item in except_me}

	# Check for duplicate names and change the name accordingly
	self_name = self.name[:]

	for counter in range(1, 1000):
		if self.name not in name_set:
			break
		self['name'] = "{0}.{1:03}".format(self_name, counter)
		# print("Renamed {0} to {1}".format(self_name, self.name))

	return

# callback for pose name change
def posename_resolve_collision_callback(self, context):
	arm = self.id_data
	spl = get_poselib(arm)
	posebook = spl.get_active_book()
	resolve_naming_collision(self, posebook.poses)

# callback for pose book name change
def posebookname_resolve_collision_callback(self, context):
	print(self)
	arm = self.id_data
	spl = get_poselib(arm)
	resolve_naming_collision(self, spl.books)

# callback for pose value change
def update_pose_value(self, context):
	arm = self.id_data
	spl = get_poselib(arm)
	book = spl.get_active_book()
	update_combined_pose(book)


###################################################
# Property Groups
###################################################

# Transform Data for each bone
class BoneTransform(PropertyGroup):
	name: StringProperty(name="Bone Name")
	location: FloatVectorProperty(name="Location", size=3, default=(0, 0, 0), subtype='TRANSLATION' )
	rotation: FloatVectorProperty(name="Rotation", size=4, default=(1, 0, 0, 0), subtype='QUATERNION') # Quartanion
	scale: FloatVectorProperty(name="Scale", size=3, default=(1, 1, 1), subtype='XYZ')

	def copy_from(self, bone):
		self.name = bone.name
		self.location = bone.location
		self.rotation = bone.rotation
		self.scale = bone.scale

# Data for each pose  
class PoseData(PropertyGroup):
	name: StringProperty(name="Pose Name", default="New Pose", update=posename_resolve_collision_callback)

	category: EnumProperty(
		name="Category", 
		items=[
			("NONE", "None", "Category is unset"), 
			("EYEBROW", "Eyebrow", "Eyebrow"), 
			("EYE", "Eye", "Eye"),
			("MOUTH", "Mouth", "Mouth"), 
			("OTHER", "Other", "Other (Body, FX, etc)"),
			], 
		default="OTHER", 
		options=set()
	)

	value: FloatProperty(name="Value", default=0.0, soft_min=0.0, soft_max=1.0, update=update_pose_value, options=set()) # not keyframable
	bones: CollectionProperty(type=BoneTransform)
	active_bone_index: IntProperty()

	def get_active_bone(self) -> Optional[BoneTransform]:
		if self.active_bone_index < 0 or self.active_bone_index >= len(self.bones):
			return None
		return self.bones[self.active_bone_index]

	def add_bone(self, name:str) -> BoneTransform:
		bone = self.bones.add()
		bone.name = name
		self.active_bone_index = len(self.bones) - 1
		return bone

	def copy_from(self, pose: "PoseData"):
		self.name = pose.name
		self.category = pose.category
		self.value = pose.value

		self.bones.clear()
		for bone in pose.bones:
			new_bone = self.add_bone()
			new_bone.copy_from(bone)

# PoseBook (Collection of Poses)
class PoseBook(PropertyGroup):
	name: StringProperty(name="Book Name", default="New Book", update=posebookname_resolve_collision_callback)
	poses: CollectionProperty(type=PoseData)
	active_pose_index: IntProperty()

	def get_active_pose(self) -> Optional[PoseData]:
		if self.active_pose_index < 0 or self.active_pose_index >= len(self.poses):
			return None
		return self.poses[self.active_pose_index]

	def get_pose_by_name(self, name) -> Optional[PoseData]:
		for pose in self.poses:
			if pose.name == name:
				return pose
		return None

	def add_pose(self, name:str = None) -> PoseData:
		pose = self.poses.add()
		if name:
			pose.name = name
		self.active_pose_index = len(self.poses) - 1
		return pose
	
	def remove_pose_by_index(self, index):
		if index < 0 or index >= len(self.poses):
			return

		self.poses.remove(index)
		if index >= self.active_pose_index:
			self.active_pose_index -= 1
		if self.active_pose_index < 0:
			self.active_pose_index = 0

	def remove_pose(self, pose: PoseData):
		index = self.poses.find(pose.name)
		if index >= 0:
			self.remove_pose_by_index(index)


# Root Container
class PoselibData(PropertyGroup):
	books: CollectionProperty(type=PoseBook) # PoseBooks
	active_book_index: IntProperty()

	# add a new book
	def add_book(self, name:str = None ) -> PoseBook:
		if len(self.books) == 0:
			# create bone name backups
			arm = self.id_data
			for bone in arm.data.bones:
				bone["spl_bone_name_backup"] = bone.name

		book = self.books.add()
		if not name:
			name = 'New Book'
		
		# resolve naming collision

		self.active_book_index = len(self.books) - 1
		return book

	# remove book by index
	def remove_book_by_index(self, index):
		if index < 0 or index >= len(self.books):
			return

		self.books.remove(index)
		if index >= self.active_book_index:
			self.active_book_index -= 1
		if self.active_book_index < 0:
			self.active_book_index = 0

	# remove book
	def remove_book(self, book: PoseBook):
		index = self.books.find(book.name)
		if index >= 0:
			self.remove_book_by_index(index)

	# get active book
	def get_active_book(self) -> Optional[PoseBook]:
		if self.active_book_index < 0 or self.active_book_index >= len(self.books):
			return None
		return self.books[self.active_book_index]

	# get book by name
	def get_book_by_name(self, name) -> Optional[PoseBook]:
		for book in self.books:
			if book.name == name:
				return book
		return None


###################################################
# Helpers for user of this module
###################################################

# Get Root PropertyGroup from Context
def get_poselib_from_context( context: bpy.types.Context ) -> Optional[PoselibData]:
	obj = context.object
	if not obj:
		return None
	arm = obj if obj.pose else obj.find_armature()
	if not arm:
		return None

	return arm.sakura_poselib

# Get Root PropertyGroup from Object
def get_poselib( obj: bpy.types.Object ) -> Optional[PoselibData]:
	if not obj:
		return None

	arm = obj if obj.pose else obj.find_armature()
	if not arm:
		return None

	return arm.sakura_poselib


class PoseLibPlusScreen(PropertyGroup):
	category_filter: EnumProperty(
		name="Category", 
		items=[
			("ALL", "All", "Show All"), 
			("EYEBROW", "Eyebrow", "Show Eyebrow Poses"), 
			("EYE", "Eye", "Show Eye Poses"),
			("MOUTH", "Mouth", "Show Mouth Poses"), 
			("OTHER", "Other", "Show Other Poses (Body, FX, etc)"),
			], 
		default="ALL",
		options=set(), 
	)


###################################################
# Register & Unregister (called from __init__.py)
###################################################

classes = (
	BoneTransform,
	PoseData,
	PoseBook,
	PoselibData,
	PoseLibPlusScreen,
)

def register():
	for cls in classes:
		bpy.utils.register_class(cls)
	bpy.types.Object.sakura_poselib = PointerProperty(type=PoselibData)
	bpy.types.Screen.sakura_poselib = PointerProperty(type=PoseLibPlusScreen)

def unregister():
	for cls in classes:
		bpy.utils.unregister_class(cls)
	del bpy.types.Object.sakura_poselib
	del bpy.types.Screen.sakura_poselib

