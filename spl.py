# Properties for Sakura Poselib
import re
import bpy
from bpy.types import PropertyGroup
from bpy.props import *
from mathutils import Vector, Quaternion, Euler, Matrix
from typing import Optional
import time

from . import utils

# pose categories definition
POSE_CATEGORIES = [
			("ALL", "All", "Show All"), 
			("EYEBROW", "Eyebrow", "Show Eyebrow Poses"), 
			("EYE", "Eye", "Show Eye Poses"),
			("MOUTH", "Mouth", "Show Mouth Poses"), 
			("OTHER", "Other", "Show Other Poses (Body, FX, etc)"),
]


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


# Get armature object from ID datablock
def get_armature_from_id( data:bpy.types.ID ) -> Optional[bpy.types.Object]:
	obj:bpy.types.Object = data.id_data

	if obj.pose:
		return obj
	
	if obj.get(__PROXY_IDENTIFIER):
		return obj.get(__PROXY_OWNER)
	
	print("Sakura Poselib - get_armature_from_id: Could not find armature object. Possibly corrupted data.")
	return None

# Reset pose of armature
def armature_reset_pose(arm: bpy.types.Armature):
	for pbone in arm.pose.bones:
		pbone.location = (0,0,0)
		pbone.rotation_quaternion = (1,0,0,0)
		pbone.rotation_euler = (0,0,0)
		pbone.rotation_axis_angle = (0,0,0,0)
		pbone.scale = (1,1,1)
	return


# Update Combined Pose
def update_combined_pose( book: "PoseBook" ):
	arm = get_armature_from_id(book)
	spl = get_poselib(arm)

	if spl.enable_animation:
		return # blender animation system do the job
	
	accum_dic = {} # {bone_name: (loc, rot, sca)}
	zero_vector = Vector((0,0,0))
	ident_quat = Quaternion((1,0,0,0))
	zero_euler = Euler((0,0,0))
	ident_scale = Vector((1,1,1))

	# accumulate all influences of poses
	book: PoseBook
	pose: PoseData
	for pose in book.poses:
		influence = pose.value
		bone_data: BoneTransform
		for bone_data in pose.bones:
			if bone_data.name not in accum_dic:
				accum_dic[bone_data.name] = [zero_vector.copy(), zero_euler.copy(), ident_scale.copy()]

			if influence == 0.0:
				continue

			loc, rot, sca = accum_dic[bone_data.name]

			if bone_data.location.length != 0.0:
				loc += bone_data.location * influence

			if bone_data.rotation != ident_quat:
				euler = bone_data.rotation.to_euler()
				rot.x += euler.x * influence
				rot.y += euler.y * influence
				rot.z += euler.z * influence

			if bone_data.scale != ident_scale:
				sca += (bone_data.scale - ident_scale) * influence

	# apply accumulated values to bones
	for bone_name, (loc, rot, sca) in accum_dic.items():
		pbone:bpy.types.PoseBone = arm.pose.bones.get(bone_name)
		if pbone:
			org_rotation_mode = pbone.rotation_mode
			pbone.rotation_mode = 'QUATERNION'
			pbone.location = loc
			pbone.rotation_quaternion = rot.to_quaternion()
			pbone.scale = sca
			pbone.rotation_mode = org_rotation_mode

	return


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
	# callback for pose name change
	def update_pose_name(self, context):
		book = self.get_book()
		resolve_naming_collision(self, book.poses)

		# Update action name
		action =  self.get_action()
		self.action_name = self.make_action_name()
		if action:
			action.name = self.action_name
		else:
			self.action_uptodate = False
		return

	########################################################################################
	# Properties
	name: StringProperty(
		name="Pose Name", 
		default="New Pose", 
		update=update_pose_name,
		options={'LIBRARY_EDITABLE'},
		override={'LIBRARY_OVERRIDABLE'},
	)

	
	name_alt: StringProperty(
		name="Pose Name (Alt)", 
		description="Alternative name. Mainly intended for translation. Not used as idetifier in blender", 
		default="",
		options={'LIBRARY_EDITABLE'},
		override={'LIBRARY_OVERRIDABLE'},
	)

	category: EnumProperty(
		name="Category", 
		items=POSE_CATEGORIES,
		default="OTHER", 
		options={'LIBRARY_EDITABLE'},
		override={'LIBRARY_OVERRIDABLE'},
	)

	# callback for pose value change
	def update_pose_value(self, context):
		if self.get('obj') and self.get('constraint_name'):
			return

		book = self.get_book()			
		update_combined_pose(book)
		return

	# callback for pose value change
	def set_pose_value(self, value):
		self['value'] = value

		if self.get('obj') and self.get('constraint_name'):
			obj = self['obj']
			con = obj.constraints.get(self['constraint_name'])
			con.influence = value
		return

	def get_pose_value(self):
		if self.get('obj') and self.get('constraint_name'):
			obj = self['obj']
			con = obj.constraints.get(self['constraint_name'])
			return con.influence
		val = self['value'] if 'value' in self else 0.0

		return val

	value: FloatProperty(
			name="Value", default=0.0, soft_min=0.0, soft_max=1.0,
			# get=get_pose_value, set=set_pose_value, 
			update=update_pose_value,
			options=set(),
			override={'LIBRARY_OVERRIDABLE'},
		)
	bones: CollectionProperty(
		type=BoneTransform,
		options={'LIBRARY_EDITABLE'},
		override={'LIBRARY_OVERRIDABLE', 'USE_INSERTION'},
	)
	active_bone_index: IntProperty(
		override={'LIBRARY_OVERRIDABLE'},
	)

	########################################################################################
	# Basic Operations

	# returns the armature object of the pose belongs to
	def get_armature(self) -> Optional[bpy.types.Object]:
		return get_armature_from_id(self)
	
	def get_poselib(self) -> Optional["PoselibData"]:
		return self.id_data.sakura_poselib

	# returns the PoseBook object of the pose belongs to
	def get_book(self) -> Optional["PoseBook"]:
		path = self.path_from_id() # sakura_poselib.books[x].poses[x]

		# strip the last part
		path = re.sub(r"\.[^.]*$", "", path)

		# resolve the path
		book = self.id_data.path_resolve(path)
		return book

	def get_active_bone(self) -> Optional[BoneTransform]:
		if self.active_bone_index < 0 or self.active_bone_index >= len(self.bones):
			return None
		return self.bones[self.active_bone_index]

	def add_bone(self, name:str) -> BoneTransform:
		bone = self.bones.add()
		bone.name = name
		self.active_bone_index = len(self.bones) - 1
		return bone

	def remove_bone(self, name:str):
		for idx, bone in enumerate(self.bones):
			if bone.name == name:
				self.bones.remove(idx)
				break
		self.active_bone_index = max(0, min(self.active_bone_index, len(self.bones) - 1) )
		self.action_uptodate = False

	def get_bone_by_name(self, name:str) -> Optional[BoneTransform]:
		for bone in self.bones:
			if bone.name == name:
				return bone
		return None

	def copy_from(self, pose: "PoseData"):
		self.name = pose.name
		self.name_alt = pose.name_alt
		self.category = pose.category

		self.bones.clear()
		for bone in pose.bones:
			new_bone = self.add_bone(bone.name)
			new_bone.copy_from(bone)

		self.action_uptodate = False
		self.ensure_action()
		return

	# helper: check if bone is driven by a driver
	def __is_bone_driver_driven( self, bone:bpy.types.PoseBone, valid_datapaths: list) -> bool:
		return any(f'bones["{bone.name}"]' in dp for dp in valid_datapaths)

	def from_current_pose(self, ignore_hidden_bones:bool = False, ignore_driven_bones: bool = True ):
		arm = self.get_armature()

		# Get valid data paths for driven bones
		valid_datapaths = []	
		if ignore_driven_bones and arm.animation_data:
			for fc in arm.animation_data.drivers:
				if not fc.is_valid:
					continue

				if '.loc' in fc.data_path or '.rot' in fc.data_path or '.sca' in fc.data_path:
					valid_datapaths.append(fc.data_path)

		# clear all bones
		self.bones.clear()

		# Save only bones contributing to the deformation
		for bone in arm.pose.bones:
			if bone.matrix_basis != Matrix.Identity(4): # Check if the bone is affected by the pose
				if ignore_hidden_bones and not utils.is_pose_bone_visible(bone):
					continue
				if ignore_driven_bones and self.__is_bone_driver_driven(bone, valid_datapaths):
					continue

				bd = self.add_bone(bone.name)
				bd.location = bone.location
				bd.rotation = utils.get_pose_bone_rotation_quaternion(bone)
				bd.scale = bone.scale

		self.ensure_action( force_update = True )
		return

	def apply_pose(self):
		if self.value != 1.0:
			self.value = 1.0

		con_name = self.get('constraint_name')
		if con_name:
			arm = self.get_armature()
			if con_name in arm.keys():
				arm[con_name] = 1.0
				arm.hide_render = arm.hide_render

	def reset_pose(self):
		if self.value != 0.0:
			self.value = 0.0

		con_name = self.get('constraint_name')
		if con_name:
			arm = self.get_armature()
			if con_name in arm.keys():
				arm[con_name] = 0.0
				arm.hide_render = arm.hide_render # hacky way to update the pose

	########################################################################################
	# Action related properties
	action_uptodate: BoolProperty(
		default=False,
		options={'HIDDEN', 'SKIP_SAVE', 'LIBRARY_EDITABLE'},
		override={'LIBRARY_OVERRIDABLE'},
	) # This should be resetted on every load
	
	action_name: StringProperty(
		default="", 
		options={'HIDDEN', 'SKIP_SAVE', 'LIBRARY_EDITABLE'},
		override={'LIBRARY_OVERRIDABLE'},
	) # This should be resetted on every load

	# Create action name
	def make_action_name( self ) -> str:
		arm = self.get_armature()
		book = self.get_book()
		return "SPL_" + arm.name.rstrip("_arm") + "/" + book.name + "/" + self.name

	# Return action for pose
	def get_action(self) -> Optional[bpy.types.Action]:
		return bpy.data.actions.get(self.action_name)
	
	# Create action for pose
	def ensure_action(self, force_update:bool = False) -> Optional[bpy.types.Action]:
		#print("Ensure Action", self.name)

		spl = self.get_poselib()
		if not spl.enable_animation:
			return None

		action = self.get_action()
		if not action:
			self.action_uptodate = False

		if self.action_uptodate and force_update == False:
			return

		action_name = self.make_action_name()
		if self.action_name != action_name:
			if bpy.data.actions.get(self.action_name):
				#print("Remove Action", self.action_name)
				bpy.data.actions.remove(bpy.data.actions[self.action_name])

		self.action_name = action_name

		# Delete if the action already exists
		if action_name in bpy.data.actions:
			if force_update:
				#print("Remove Action (Forced)", action_name)
				bpy.data.actions.remove(bpy.data.actions[action_name])
			else:
				self.action_uptodate = True
				return bpy.data.actions[action_name]

		arm = self.get_armature()
		action = bpy.data.actions.new(name=action_name)
		for bone in self.bones:
			bone_name = bone.name
			transforms = {
				'location': bone.location,
				'rotation': bone.rotation,
				'scale': bone.scale,
			}
			bone = arm.pose.bones.get(bone_name)
			if bone:
				# Create channel group
				channel_group = action.groups.new(name=bone_name)

				for attr, values in transforms.items() :
					if attr == 'name':
						continue

					# Convert rotation to euler if needed
					if attr == 'rotation':
						pbone = arm.pose.bones.get(bone_name)
						rot_mode = pbone.rotation_mode if pbone else 'QUATERNION' # Default to quaternion
						if rot_mode == 'QUATERNION':
							attr = 'rotation_quaternion'
							rot_conv = lambda x: x
						elif rot_mode == 'AXIS_ANGLE':
							attr = 'rotation_axis_angle'
							rot_conv = lambda x: x.to_axis_angle()
						elif rot_mode in ('XYZ', 'XZY', 'YXZ', 'YZX', 'ZXY', 'ZYX'):
							attr = 'rotation_euler'
							rot_conv = lambda x: x.to_euler(rot_mode)

						values = rot_conv(Quaternion(values))

					# Create fcurve for each value
					for i, value in enumerate(values):
						if attr == 'scale' or (attr == 'rotation_quaternion' and i == 0):
							if value == 1.0:
								continue
						else:
							if value == 0.0:
								continue

						fcurve = action.fcurves.new(data_path='pose.bones["'+bone_name+'"].'+attr, index=i)
						fcurve.keyframe_points.add(1)
						fcurve.keyframe_points[0].co = 0, value
						fcurve.keyframe_points[0].interpolation = 'LINEAR'
						fcurve.group = channel_group

		if True: # This will make the action available for action constraints for some reason
			orig_action = arm.animation_data.action
			arm.animation_data.action = action 
			arm.animation_data.action = orig_action # restore original action

		self.action_uptodate = True
		# print("Action Created", action_name)

		# Create constraints for each bone
		book = self.get_book()
		con_name = "SPL/" + book.name + "/" + self.name
		self['constraint_name'] = con_name

		for bone_data in self.bones:
			pbone: bpy.types.PoseBone = arm.pose.bones.get(bone_data.name)
			if not pbone:
				continue

			# Create constraints for each bone
			con: bpy.types.ActionConstraint = pbone.constraints.get(con_name) or pbone.constraints.new('ACTION')
			con.name = con_name
			con.use_eval_time = True
			con.mix_mode = 'BEFORE_FULL'
			con.action = action
			con.influence = 0.0

			# Create drivers for influence
			fc: bpy.types.FCurve = con.driver_add('influence')
			drv = fc.driver
			drv.type = 'SUM'
			drv.use_self = True
			drv.expression = "var"
			drv.variables.new()
			drv.variables[0].name = "var"
			drv.variables[0].targets[0].id_type = 'OBJECT'
			drv.variables[0].targets[0].id = arm

			# Create custom property for influence
			arm[con_name] = self.value
			ui_data = arm.id_properties_ui(con_name)
			ui_data.update(
				subtype='FACTOR',
				min=0.0,
				max=1.0,
				default=0.0,
				description="Pose Influence for "+con_name,
				precision = 2,
			)

			# Make this property overridable
			arm.property_overridable_library_set('["%s"]' % bpy.utils.escape_identifier(con_name), True)

			# Set driver variable
			drv.variables[0].targets[0].data_path = '["'+con_name+'"]'
		# end for bone_data

		return action
	
	def invalidate_action(self):
		self.action_uptodate = False

	def remove_action(self):
		con_name = self.get('constraint_name')
		if not con_name:
			return

		# Remove action constraints from pose bones
		arm = self.get_armature()
		for pbone in arm.pose.bones:
			con:bpy.types.ActionConstraint = pbone.constraints.get(con_name)
			if con:
				con.driver_remove('influence')
				pbone.constraints.remove(con)

		# Remove custom properties
		if con_name in arm.keys():
			del arm[con_name]
		if 'constraint_name' in self.keys():
			del self['constraint_name']

		# Remove action
		if self.action_name in bpy.data.actions:
			bpy.data.actions.remove(bpy.data.actions[self.action_name])

		self.action_name = ""
		self.action_uptodate = False

		return





# PoseBook (Collection of Poses)
class PoseBook(PropertyGroup):

	# callback for pose book name change
	def on_posebook_name_update(self, context):
		arm = get_armature_from_id(self)
		spl = get_poselib(arm)

		# clear actions
		for pose in self.poses:
			pose.remove_action()

		resolve_naming_collision(self, spl.books)

		# recreate actions
		if spl.enable_animation:
			pose: PoseData
			for pose in self.poses:
				pose.ensure_action()

	name: StringProperty(
		name="Book Name", 
		default="New Book", 
		update=on_posebook_name_update,
		options={'LIBRARY_EDITABLE'},
		override={'LIBRARY_OVERRIDABLE'},

	)

	poses: CollectionProperty(
		type=PoseData,
		options={'LIBRARY_EDITABLE'},
		override={'LIBRARY_OVERRIDABLE', 'USE_INSERTION'},
	)

	active_pose_index: IntProperty(
			override={'LIBRARY_OVERRIDABLE'},
	)


	category_filter: EnumProperty(
		name="Category", 
		items=POSE_CATEGORIES,
		default="ALL",
		override={'LIBRARY_OVERRIDABLE'},
	)

	show_alt_pose_names: BoolProperty(
		name="Show Alt Names",
		description="Show alternative pose names. Mainly intended for translation. Not used as idetifier in blender",
		default=False, 
		options=set()
		)

	########################################################################################
	# Basic Operations

	def get_armature(self) -> Optional[bpy.types.Object]:
		return get_armature_from_id(self)

	def get_active_pose(self) -> Optional[PoseData]:
		if self.active_pose_index < 0 or self.active_pose_index >= len(self.poses):
			return None
		return self.poses[self.active_pose_index]

	def get_pose_by_name(self, name) -> Optional[PoseData]:
		for pose in self.poses:
			if pose.name == name:
				return pose
		return None
	
	def get_pose_by_index(self, index) -> Optional[PoseData]:
		if index < 0 or index >= len(self.poses):
			return None
		return self.poses[index]

	def add_pose(self, name:str = None) -> PoseData:
		pose = self.poses.add()
		if name:
			pose.name = name
		
		return pose
	
	def remove_pose_by_index(self, index):
		if index < 0 or index >= len(self.poses):
			return

		# Remove action
		pose:PoseData = self.poses[index]
		pose.remove_action()

		# Remove pose
		self.poses.remove(index)
		if index >= self.active_pose_index:
			self.active_pose_index -= 1
		if self.active_pose_index < 0:
			self.active_pose_index = 0
		return

	def remove_pose(self, pose: PoseData):
		index = self.poses.find(pose.name)
		if index >= 0:
			self.remove_pose_by_index(index)
		return
	
	# Copy entire data from another PoseBook
	def copy_from(self, src: "PoseBook"):
		self.poses.clear()
		for pose in src.poses:
			new_pose = self.add_pose(pose.name)
			new_pose.copy_from(pose)
		
		self.active_pose_index = src.active_pose_index
		self.category_filter = src.category_filter
		self.show_alt_pose_names = src.show_alt_pose_names
		return
	
	# Apply single pose
	def apply_single_pose(self, pose: PoseData):
		for p in self.poses:
			p: PoseData
			if p == pose:
				p.apply_pose()
			else:
				p.reset_pose()
		return
	
	# Applly entire book
	def apply_poses(self, reset_current_pose: bool = True):
		if reset_current_pose:
			arm = get_armature_from_id(self)
			armature_reset_pose(arm)
		update_combined_pose(self)
		return

	# Reset entire book
	def reset_poses(self):
		for pose in self.poses:
			pose: PoseData
			pose.reset_pose()
		return



# Root PoseLib Container
class PoselibData(PropertyGroup):
	books: CollectionProperty(
		type = PoseBook, 
		override = {'LIBRARY_OVERRIDABLE', 'USE_INSERTION'},
	) # PoseBooks

	# callback for active book index change
	def on_update_active_book_index(self, context):
		# apply new book
		book = self.get_active_book()
		if book:
			book.apply_poses( reset_current_pose = False )

	active_book_index: IntProperty(
		override = {'LIBRARY_OVERRIDABLE'},
		update = on_update_active_book_index,
	)

	# controller name generator
	def make_controller_name(self) -> str:
		arm = self.get_armature()
		return arm.name + "_SPL_Controller"

	# callback for enable_animation change
	def on_enable_animation_update(self, context):
		if self.enable_animation:
			# reset pose
			armature_reset_pose(self.get_armature())

			# create actions for all poses (and this will constrain pose bones using the actions)
			self.ensure_actions()

		else: # animation disabled
			# remove all actions (and this will remove constraints from pose bones)
			self.purge_actions()
			# restore combined pose
			update_combined_pose(self.get_active_book())

		return

	enable_animation: BoolProperty(
		name="Enable Animation",
		description= "Make this Poselib animatable/keyable. Pose editing will be disabled in this mode. Armature bones will be constrained by Actions",
		default=False,
		update=on_enable_animation_update,
		override={'LIBRARY_OVERRIDABLE'},
	)

	########################################################################################
	# Basic Operations

	# Get Armature Object
	def get_armature(self) -> Optional[bpy.types.Object]:
		return get_armature_from_id(self)

	# add a new book
	def add_book(self, name:str = None ) -> PoseBook:
		if len(self.books) == 0:
			# create bone name backups
			#print(self, self.id_data)
			arm = get_armature_from_id(self)
			#print(arm)
			for bone in arm.data.bones:
				bone["spl_bone_name_backup"] = bone.name

		book = self.books.add()
		if not name:
			name = 'New Book'
		book.name = name
		
		# resolve naming collision
		self.active_book_index = len(self.books) - 1
		return book

	# remove book by index
	def remove_book_by_index(self, index):
		if index < 0 or index >= len(self.books):
			return

		# Remove all actions
		book: PoseBook = self.books[index]
		for pose in book.poses:
			pose.remove_action()

		self.books.remove(index)
		if index >= self.active_book_index:
			self.active_book_index -= 1
		if self.active_book_index < 0:
			self.active_book_index = 0

	# remove active book
	def remove_active_book(self):
		if self.active_book_index < 0 or self.active_book_index >= len(self.books):
			return
		self.remove_book_by_index(self.active_book_index)

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
	
	
	# Copy entire data from another PoselibData
	def copy_from(self, src: "PoselibData"):
		self.books.clear()
		for book in src.books:
			new_book = self.add_book(book.name)
			new_book.copy_from(book)
		
		self.active_book_index = src.active_book_index
	
	# Ensure the armature has proper actions
	def ensure_actions(self):
		#t = time.perf_counter()

		if self.enable_animation == False:
			return

		# Create actions for each pose
		book: PoseBook = self.get_active_book()
		pose: PoseData
		for book in self.books:
			for pose in book.poses:
				pose.ensure_action()
		
		# in milli seconds
		#print("Ensure Actions Time: ", (time.perf_counter() - t) * 1000, "ms")
		return
	
	def purge_actions(self):
		arm = self.get_armature()
		if not arm:
			return

		for book in self.books:
			for pose in book.poses:
				pose.remove_action()
		return


###################################################
# Helpers for user of this module
###################################################

__PROXY_SUFFIX = "_SPL_Proxy"
__PROXY_IDENTIFIER = "is_spl_proxy"
__PROXY_OWNER = "spl_proxy_owner"

# Get proxy object for a linked armature
def get_proxy_obj(arm: bpy.types.Armature) -> Optional[bpy.types.Object]:
	proxy_name = arm.name + __PROXY_SUFFIX
	proxy = bpy.data.objects.get(proxy_name)
	if proxy and proxy.get(__PROXY_IDENTIFIER) and proxy.get(__PROXY_OWNER):
		return proxy

	return None

# get or create a proxy object for a linked armature
def ensure_proxy_obj(arm: bpy.types.Armature) -> bpy.types.Object:
	return None
	"""
	Create/Get a proxy empty object for a linked armature to store Sakura Poselib data.

	Args:
		arm (bpy.types.Armature): The linked armature object to create a proxy for.

	Returns:
		bpy.types.Object: The created or retrieved proxy empty object.
	"""	

	# Check if a proxy object already exists
	proxy_name = arm.name + __PROXY_SUFFIX
	proxy = bpy.data.objects.get(proxy_name)
	if proxy:
		proxy_owner = proxy.get(__PROXY_OWNER)
		if proxy.get(__PROXY_IDENTIFIER) and proxy_owner and proxy_owner.name == arm.name:
			return proxy
		else:
			# Remove the object if it's not a valid proxy
			bpy.data.objects.remove(proxy)

	# Create a new proxy object
	proxy = bpy.data.objects.new(proxy_name, None)
	bpy.context.scene.collection.objects.link(proxy)

	# Set display type to 'PLAIN_AXES' for visibility
	proxy.empty_display_type = 'PLAIN_AXES'

	# Set the proxy's parent to the armature
	proxy.parent = arm

	# Add a custom property to identify this as a Sakura Poselib proxy
	proxy[__PROXY_IDENTIFIER] = True
	proxy[__PROXY_OWNER] = arm

	# Copy Sakura Poselib data if it exists
	proxy.sakura_poselib.copy_from(arm.sakura_poselib)

	return proxy


# Get Root PropertyGroup from Context
def get_poselib_from_context( context: bpy.types.Context ) -> Optional[PoselibData]:
	obj = context.object
	if not obj:
		return None
	
	return get_poselib(obj)

# Get Root PropertyGroup from Object
def get_poselib( obj: bpy.types.Object ) -> Optional[PoselibData]:
	if not obj:
		return None

	arm = obj if obj.pose else obj.find_armature()
	if not arm:
		return None

	# Check if the object is library or override library
	if arm.library or arm.override_library:
		# create proxy object(Empty) to contain the PoseLib data
		proxy_obj = get_proxy_obj(arm)
		if proxy_obj:
			return proxy_obj.sakura_poselib

	return arm.sakura_poselib


###################################################
# Register & Unregister (called from __init__.py)
###################################################

classes = (
	BoneTransform,
	PoseData,
	PoseBook,
	PoselibData,
)

def register():
	for cls in classes:
		bpy.utils.register_class(cls)
	bpy.types.Object.sakura_poselib = PointerProperty(type=PoselibData)

def unregister():
	for cls in classes:
		bpy.utils.unregister_class(cls)
	del bpy.types.Object.sakura_poselib
