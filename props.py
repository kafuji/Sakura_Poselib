# Properties for Sakura Poselib
import bpy
from bpy.types import PropertyGroup
from bpy.props import *

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
	spl = arm.sakura_poselib
	posebook = get_active_book(spl)
	resolve_naming_collision(self, posebook.poses)

# callback for pose list name change
def posebookname_resolve_collision_callback(self, context):
	arm = self.id_data
	spl = arm.sakura_poselib
	spl.active_list_name = self.name
	resolve_naming_collision(self, spl.books)


# callback for pose value change
def update_pose_value(self, context):
	arm = self.id_data
	spl = arm.sakura_poselib
	book = get_active_book(spl)
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

# Transforms for each Pose  
class PoseItem(PropertyGroup):
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

# PoseBook (Collection of Poses)
class PoseBook(PropertyGroup):
	name: StringProperty(name="Book Name", default="New Book", update=posebookname_resolve_collision_callback)
	poses: CollectionProperty(type=PoseItem)
	active_pose_index: IntProperty()

# Root Container
class PoselibData(PropertyGroup):
	books: CollectionProperty(type=PoseBook) # PoseBooks
	active_book_index: IntProperty()

	# wrapper for adding new posebook, ensure creating backup bone names and set active book index
	def add_book(self):
		if len(self.books) == 0:
			# create bone name backups
			arm = self.id_data
			for bone in arm.data.bones:
				bone["spl_bone_name_backup"] = bone.name

		book = self.books.add()
		self.active_book_index = len(self.books) - 1

		return book


###################################################
# Helpers for user of this module
###################################################

# Get Root Property from Object
def get_poselib( obj: bpy.types.Object ) -> PoselibData:
	if not obj or obj.type != 'ARMATURE':
		return None
	return obj.sakura_poselib

# Get Root Property from Context
def get_active_poselib( context: bpy.types.Context ) -> PoselibData:
	armature = context.object
	if not armature or armature.type != 'ARMATURE':
		return None

	return armature.sakura_poselib

# Get Active Category
def get_active_book( spl: PoselibData ) -> PoseBook:
	if not spl.books:
		return None

	if spl.active_book_index < 0 or spl.active_book_index >= len(spl.books):
		return None
	
	return spl.books[spl.active_book_index]


# Get Active Pose
def get_active_pose( posebook: PoseBook ) -> PoseItem:
	if posebook is None:
		return None
	if posebook.active_pose_index < 0 or posebook.active_pose_index >= len(posebook.poses):
		return None

	return posebook.poses[posebook.active_pose_index]


# Get Active Bone
def get_active_bone( pose: PoseItem ) -> BoneTransform:
	if pose is None:
		return None
	if pose.active_bone_index < 0 or pose.active_bone_index >= len(pose.bones):
		return None
	
	return pose.bones[pose.active_bone_index]


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
	PoseItem,
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

