# Description: Internal functions for Sakura Poselib

import bpy
import math
import os

from mathutils import Vector, Quaternion, Euler

from . import mmd


# helper: check pose bone is visible
def is_pose_bone_visible( pbone: bpy.types.PoseBone ) -> bool:
	# check if bone is hidden
	if pbone.bone.hide or pbone.bone.hide_select:
		return False

	# check if bone is in visible layer
	arm = pbone.id_data
	if not any(pbone.bone.layers[i] and arm.data.layers[i] for i in range(len(pbone.bone.layers))):
		return False

	return True

# Get pose bone rotation in quaternion
def get_pose_bone_rotation_quaternion( pose_bone: bpy.types.PoseBone ) -> Quaternion:
	rotation_mode = pose_bone.rotation_mode

	if rotation_mode == 'QUATERNION':
		return pose_bone.rotation_quaternion.copy()
	elif rotation_mode == 'AXIS_ANGLE':
		return pose_bone.rotation_axis_angle.to_quaternion()
	elif rotation_mode == 'XYZ':
		return pose_bone.rotation_euler.to_quaternion()
	elif rotation_mode == 'XZY':
		return pose_bone.rotation_euler.to_quaternion()
	elif rotation_mode == 'YXZ':
		return pose_bone.rotation_euler.to_quaternion()
	elif rotation_mode == 'YZX':
		return pose_bone.rotation_euler.to_quaternion()
	elif rotation_mode == 'ZXY':
		return pose_bone.rotation_euler.to_quaternion()
	elif rotation_mode == 'ZYX':
		return pose_bone.rotation_euler.to_quaternion()
	else:
		print("Unknown rotation mode: ", rotation_mode)
		return Quaternion()


# Extract pose data from pose library, returns list of poses
def extract_pose_library_data( armature: bpy.types.Object ):
	pose_library = armature.pose_library

	if pose_library is None:
		print("No pose library found.")
		return None

	poses = []

	for marker in pose_library.pose_markers:
		pose_data = {}

		# Gather keyframes at marker.frame
		keyframes = {} # data_path : value

		for fc in pose_library.fcurves:
			if not fc.data_path.startswith("pose.bones"):
				continue

			for kf in fc.keyframe_points:
				if kf.co[0] == marker.frame:
					keyframes[fc.data_path + str(fc.array_index)] = kf.co[1]
					

		#print(marker.name, marker.frame)
		#for key, value in keyframes.items():
		#	print(key, value)

		# Iterate through keyframes to gather transform data for each bone
		for data_path, value in keyframes.items():
			bone_name = data_path.split('"')[1]

			# create new entry if not exist
			if not bone_name in pose_data:
				pose_data[bone_name] = {
					'location' : [0,0,0],
					'rotation_quaternion' :[1, 0, 0, 0],
					'rotation_euler': [0,0,0],
					'rotation_axis_angle': [0,0,0,0],
					'scale' : [1, 1, 1],
				}

			# Write value
			transforms = pose_data[bone_name]
			if "location" in data_path:
				transforms['location'][int(data_path[-1])] = value
			elif "rotation_quaternion" in data_path:
				transforms['rotation_quaternion'][int(data_path[-1])] = value
			elif "rotation_euler" in data_path:
				transforms['rotation_euler'][int(data_path[-1])] = value
			elif "rotation_axis_angle" in data_path:
				transforms['rotation_axis_angle'][int(data_path[-1])] = value
			elif "scale" in data_path:
				transforms['scale'][int(data_path[-1])] = value

		poses.append((marker.name,pose_data))

	return poses

# Convert from Poselib (works on earlier than 3.4)
def convert_from_poselib( book, remove_poselib = False ):
	armature = book.id_data

	poselib = getattr( armature, 'pose_library' )
	if not poselib:
		return

	poses = extract_pose_library_data( armature )
	if not poses:
		return

	# clear current data	
	book.poses.clear()
	book.poses_index = 0

	for pose_name, pose_data in poses:
		pose = book.poses.add()
		pose.name = pose_name

		for bone_name, transforms in pose_data.items():
			bone = pose.bones.add()
			bone.name = bone_name
			bone.location = transforms['location']
			bone.scale = transforms['scale']

			# store rotation as Quaternion
			euler = Euler(transforms['rotation_euler']).to_quaternion()
			quat = Quaternion(transforms['rotation_quaternion'])

			ident = Quaternion()
			angle_euler = math.acos( min(abs( ident.dot(euler) ), 1.0) )
			angle_quat = math.acos( min(abs( ident.dot(quat) ), 1.0) )
			if angle_euler > angle_quat:
				bone.rotation = euler
			else:
				bone.rotation = quat

	book.name = poselib.name if poselib.name else armature.name if armature.name else "PoseBook_from_PoseLib"

	# Remove the original pose library
	if remove_poselib:
		bpy.data.actions.remove(poselib)

	return


# Convert to Poselib (works on earlier than 3.4)
def convert_to_poselib( book ):
	armature = book.id_data

	basename = book.name if book.name else armature.name

	# Create new pose library
	poselib = bpy.data.actions.new( basename + "_pose_library" )
	armature.pose_library = poselib

	# Iterate through poses
	for pose in book.poses:
		# Add new marker
		marker = poselib.pose_markers.new( pose.name )

		# Iterate through bones
		for bone in pose.bones:
			# Set keyframes
			bone_path = 'pose.bones["' + bone.name + '"]'

			# Location
			poselib.fcurves.new( bone_path + ".location", index=0 )
			poselib.fcurves.new( bone_path + ".location", index=1 )
			poselib.fcurves.new( bone_path + ".location", index=2 )
			poselib.fcurves[-3].keyframe_points.insert( marker.frame, bone.location[0] )
			poselib.fcurves[-2].keyframe_points.insert( marker.frame, bone.location[1] )
			poselib.fcurves[-1].keyframe_points.insert( marker.frame, bone.location[2] )

			# Rotation
			poselib.fcurves.new( bone_path + ".rotation_quaternion", index=0 )
			poselib.fcurves.new( bone_path + ".rotation_quaternion", index=1 )
			poselib.fcurves.new( bone_path + ".rotation_quaternion", index=2 )
			poselib.fcurves.new( bone_path + ".rotation_quaternion", index=3 )
			poselib.fcurves[-4].keyframe_points.insert( marker.frame, bone.rotation[0] )
			poselib.fcurves[-3].keyframe_points.insert( marker.frame, bone.rotation[1] )
			poselib.fcurves[-2].keyframe_points.insert( marker.frame, bone.rotation[2] )
			poselib.fcurves[-1].keyframe_points.insert( marker.frame, bone.rotation[3] )

			# Scale
			poselib.fcurves.new( bone_path + ".scale", index=0 )
			poselib.fcurves.new( bone_path + ".scale", index=1 )
			poselib.fcurves.new( bone_path + ".scale", index=2 )
			poselib.fcurves[-3].keyframe_points.insert( marker.frame, bone.scale[0] )
			poselib.fcurves[-2].keyframe_points.insert( marker.frame, bone.scale[1] )
			poselib.fcurves[-1].keyframe_points.insert( marker.frame, bone.scale[2] )

	return


# Load from mmd_tools' bone morph
def load_poses_from_mmdtools( book ):
	armature = book.id_data
	root = mmd.get_model_root( armature )
	if not root:
		return
	
	bone_morphs = root.mmd_root.bone_morphs
	if not bone_morphs:
		return
	
	book.poses.clear()

	# Read bone morphs and convert to Sakura Poselib' pose	
	for morph in bone_morphs:
		pose_data = book.poses.add()
		pose_data.name = morph.name
		for bone_name, rotation, location in morph.data:
			bd = pose_data.bones.add()
			bd.name = bone_name
			bd.location = location
			bd.rotation = rotation

	return


# Convert to MMD Tools' Bone Morph
def convert_poses_to_mmdtools( book, clear_exsisting=False ):
	armature = book.id_data
	root = mmd.get_model_root( armature )
	if not root:
		return
	
	poses = book.poses
	bone_morphs = root.mmd_root.bone_morphs

	if clear_exsisting:
		bone_morphs.clear()

	for pose in poses:
		# find by name
		morph = bone_morphs.get( pose.name )
		if not morph:
			morph = bone_morphs.add()
			morph.name = pose.name
			morph.category = pose.category

		# clear bone data
		morph.data.clear()
		for bone in pose.bones:
			md = morph.data.add()
			md.name = bone.name
			pbone = armature.pose.bones.get( bone.name )
			if pbone:
				bone_id = pbone.mmd_bone.bone_id
				if bone_id < 0:
					# create bone id for mmd_tools
					# bone id is max( bone_id within armature ) + 1
					bone_id = max( [b.mmd_bone.bone_id for b in armature.pose.bones] ) + 1
					pbone.mmd_bone.bone_id = bone_id

				md.bone_id = pbone.mmd_bone.bone_id # finally we have bone_id
			md.location = bone.location
			md.rotation = bone.rotation
	return


# Json format
import json
# Save PoseBook into a file (JSON)
def save_book_to_json( book, filepath ):
	poses = book.poses

	# Convert to JSON
	data = []
	for pose in poses:
		pose_data = {
			'name' : pose.name,
			'category' : pose.category,
			'bones' : [],
		}
		for bone_data in pose.bones:
			bd = {
				'name' : bone_data.name,
				'location' : bone_data.location[:],
				'rotation' : bone_data.rotation[:],
			}
			pose_data['bones'].append(bd)
		data.append(pose_data)
	
	# Save to file
	with open(filepath, 'w') as f:
		json.dump(data, f, indent=2)
	
	return


EYEBROW = {'eyebrow', 'eyebrows', 'brow', 'brows', 'mayu'}
EYE = {'eye', 'eyes', 'iris', 'pupil', 'pupils', 'me' }
MOUTH = {'mouth', 'lips', 'lip', 'kuchibiru', 'kuchi'}
import re
# Helper: Guess pose category from pose name
def guess_pose_category( pose_name ):
	lower_name = pose_name.lower()
	split_name = re.split(r'[ ._/]', lower_name)

	if any( x in EYEBROW for x in split_name ):
		return 'EYEBROW'
	elif any( x in EYE for x in split_name ):
		return 'EYE'
	elif any( x in MOUTH for x in split_name ):
		return 'MOUTH'
	else:
		return 'OTHER'


# Load PoseBook from a file (JSON)
def load_book_from_json( book, filepath, clear_exsisting=False ):
	poses = book.poses

	poses.clear()
	
	# Load from file
	with open(filepath, 'r') as f:
		data = json.load(f)

	# Convert from JSON
	for pose_data in data:
		pose = poses.add()
		pose.name = pose_data.get('name')
		pose.category = pose_data.get('category', 'NONE')
		if pose.category == 'NONE': # Guess
			pose.category = guess_pose_category( pose.name )

		for bone_data in pose_data.get('bones'):
			bd = pose.bones.add()
			bd.name = bone_data.get('name')
			bd.location = bone_data.get('location')
			bd.rotation = bone_data.get('rotation')

	book.name = os.path.basename( filepath )

	return


# CSV format
import csv

_POSE_CATEGORIES = [
	'NONE', 'EYEBROW', 'EYE', 'MOUTH', 'OTHER'
]




# Save PoseBook into a file (CSV)
def save_book_to_csv( book, filename):
	poses = book.poses
	obj: bpy.types.Object = book.id_data
	arm: bpy.types.Armature = obj.data
	matrix_world = obj.matrix_world
	bone_util_cls = mmd.BoneConverterPoseMode if arm.pose_position != 'REST' else mmd.BoneConverter
	scale = 12.5

	class _RestBone:
		def __init__(self, b:bpy.types.PoseBone):
			self.matrix_local = matrix_world @ b.bone.matrix_local

	class _PoseBone: # world space
		def __init__(self, b:bpy.types.PoseBone):
			self.bone = _RestBone(b)
			self.matrix = matrix_world @ b.matrix
			self.matrix_basis = b.matrix_basis
			self.location = b.location

	converter_cache = {}
	def _get_converter(b):
		if b not in converter_cache:
			converter_cache[b] = bone_util_cls(_PoseBone(b), scale, invert=True)
		return converter_cache[b]


	with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
		# write header
		header = ';PmxMorph,モーフ名,モーフ名(英),パネル(0:無効/1:眉(左下)/2:目(左上)/3:口(右上)/4:その他(右下)),モーフ種類(0:グループモーフ/1:頂点モーフ/2:ボーンモーフ/3:UV(Tex)モーフ/4:追加UV1モーフ/5:追加UV2モーフ/6:追加UV3モーフ/7:追加UV4モーフ/8:材質モーフ/9:フリップモーフ/10:インパルスモーフ)\n'
		csvfile.write(header)

		# write data
		for pose in poses:
			# Write a pose header
			# format: f"PmxMorph,{pose.name},{pose.name},{category_index},2(BoneMorph)"
			if pose.category not in _POSE_CATEGORIES:
				category_index = 4
			else:
				category_index = _POSE_CATEGORIES.index(pose.category)
			pose_header = f'PmxMorph,"{pose.name}","",{category_index},2\n'
			csvfile.write(pose_header)

			# Write a bone list header
			# format: f";PmxBoneMorph,親モーフ名,オフセットIndex,ボーン名,移動量_x,移動量_y,移動量_z,回転量_x[deg],回転量_y[deg],回転量_z[deg]"
			bone_header = f';PmxBoneMorph,親モーフ名,オフセットIndex,ボーン名,移動量_x,移動量_y,移動量_z,回転量_x[deg],回転量_y[deg],回転量_z[deg]\n'
			csvfile.write(bone_header)

			# Write bone data
			for index, bone in enumerate(pose.bones):
				# Write a bone data
				# format: f"PmxBoneMorph,{pose.name},index,{bone.name},{loc.x},{loc.y},{loc.z},{rot.x},{rot.y},{rot.z}"
				# loc = bone.location * 12.5 (convert to MMD unit)
				# rot = bone.rotation.to_euler('XYZ') * 180 / math.pi (convert to degree)

				pbone = obj.pose.bones.get(bone.name)
				if pbone is None:
					print(f'Warning: Bone "{bone.name}" not found in "{obj.name}", skippping...')
					continue

				# use bone converter from mmd_tools to convert bone location and rotation to MMD unit
				converter = _get_converter(pbone) 
				loc = converter.convert_location( bone.location )
				rw, rx, ry, rz = bone.rotation
				rw, rx, ry, rz = converter.convert_rotation( [rx, ry, rz, rw] )
				rot = mmd.quaternion_to_degrees( Quaternion((rw, rx, ry, rz)) )
				bone_data = f'PmxBoneMorph,"{pose.name}",{index},"{bone.name}",{loc.x:.5g},{loc.y:.5g},{loc.z:.5g},{rot.x:.5g},{rot.y:.5g},{rot.z:.5g}\n'
				csvfile.write(bone_data)

		# Comment
		csvfile.write("\n;This file is generated by Sakura Poselib addon for Blender.\n")
	# end of with open()

	return


# Load PoseBook from a file (CSV)
def load_book_from_csv( book, filename ):
	poses = book.poses

	# Format:
	# line starts with ';' is comment. just discard.

	# Line starts with PMXMorh is a pose header
	#   PmxMorph,"{pose_name}","eng_name(discard)",category_index,4(BoneMorph) 

	# Line starts with PmxBoneMorph is a bone data
	#   PmxBoneMorph,"{pose_name(which is this bone transform is belongs to)}",index(within the pose, sequential),"{bone_name}",loc_x,loc_y,loc_z,rot_x,rot_y,rot_z

	# loc is in MMD unit (1/12.5 of Blender unit)
	# rot is in degree (not radian)

	with open(filename, 'r', newline='', encoding='utf-8') as csvfile:
		reader = csv.reader(csvfile, delimiter=',', quotechar='"')

		for row in reader:
			if len(row) < 1:
				continue

			#print(f"row: {row}")
			# if the line is comment, discard
			if row[0].startswith(';'):
				continue

			def _add_pose(name, cat_index):
				pose = poses.get(name)
				if not pose:
					pose = poses.add()
					pose.name = name
				else: # warn if the pose is already exists
					print(f'Pose "{name}" is already exists. Overwrite it.')

				pose.category = _POSE_CATEGORIES[cat_index] if cat_index < len(_POSE_CATEGORIES) and cat_index >= 0 else 'OTHER'
				if pose.category == 0:
					pose.category = guess_pose_category(pose.name)
				return pose

			# if the line is PMXMorph header, create a new pose
			if row[0].startswith('PmxMorph'):
				pose_name = row[1].strip('"')
				cat_index = int(row[3])
				pose = _add_pose(pose_name, cat_index)
				continue

			# if the line is PmxBoneMorph, add a bone data to the pose indicated by the pose name
			if row[0].startswith('PmxBoneMorph'):
				pose_name = row[1].strip('"')
				index = int(row[2]) # TODO: use this to sort bones within pose (currently, it is not used)
				pose = poses.get(pose_name)

				if not pose: # warn if the pose is not found
					pose = _add_pose(pose_name, -1)
					print(f'Pose "{pose_name}" is not found. Creating a new pose.')

				bone_name = row[3].strip('"')
				loc = Vector( (float(row[4]), float(row[5]), float(row[6])) ) / 12.5
				rot = (float(row[7]), float(row[8]), float(row[9]))

				# convert to quaternion
				rot = mmd.dgrees_to_quaternion( rot )
			
				# add a bone data
				bone = pose.bones.add()
				bone.name = bone_name
				bone.location = loc
				bone.rotation = rot
				bone.scale = Vector((1.0,1.0,1.0))

				continue

		book.name = os.path.basename(filename)

	return





# Apply Single Pose 
def apply_pose( pose_data, influence = 1.0, reset_others = False, additive = False ):
	if not pose_data:
		return

	arm:bpy.types.Object = pose_data.id_data

	zero_loc = Vector((0.0,0.0,0.0))
	zero_rot = Quaternion((1.0,0.0,0.0,0.0))
	zero_sca = Vector((1.0,1.0,1.0))

	# Reset other bones
	if reset_others:
		for bone in arm.pose.bones:
			bone.location = zero_loc
			bone.rotation_quaternion = zero_rot
			bone.scale = zero_sca


	for bone_data in pose_data.bones:
		bone = arm.pose.bones.get(bone_data.name)
		if not bone:
			continue

		# Convert into Blender's coordinate system
		loc_diff = Vector( bone_data.location ) * influence
		rot_diff = Quaternion( bone_data.rotation ) * influence
		sca_diff = ( Vector( bone_data.scale ) - Vector((1.0,1.0,1.0))) * influence

		# Apply pose
		if not additive: # Replace Transform
			bone.location = loc_diff
			bone.rotation_quaternion = rot_diff
			bone.scale = sca_diff + Vector((1.0,1.0,1.0))

		else: # Additive Transform
			bone.location = bone.location + loc_diff
			bone.rotation_quaternion = bone.rotation_quaternion.slerp( bone_data.rotation, influence )
			bone.scale = bone.scale + sca_diff

	return



# Update Combined Pose
def update_combined_pose( book ):
	if not book:
		return
	
	arm = book.id_data

	accum_dic = {} # {bone_name: (loc, rot, sca)}
	zero_vector = Vector((0,0,0))
	ident_quat = Quaternion((1,0,0,0))
	zero_euler = Euler((0,0,0))
	ident_scale = Vector((1,1,1))

	# accumulate all influences of poses
	for pose in book.poses:
		influence = pose.value
		for bone_data in pose.bones:
			if bone_data.name not in accum_dic:
				accum_dic[bone_data.name] = [zero_vector.copy(), zero_euler.copy(), ident_scale.copy()]

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
		pbone = arm.pose.bones.get(bone_name)
		if pbone:
			pbone.location = loc
			pbone.rotation_quaternion = rot.to_quaternion()
			pbone.scale = sca

	return
