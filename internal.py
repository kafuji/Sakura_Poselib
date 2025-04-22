# Description: Internal functions for Sakura Poselib

import bpy
import math
import os

from mathutils import Vector, Quaternion, Euler, Matrix

from . import mmd, utils
from . import spl


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
			try:
				if not fc.data_path.startswith("pose.bones"):
					continue
			except UnicodeDecodeError: # in case of invalid datapath or something
				continue # just skip

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
def convert_from_poselib( book: spl.PoseBook, remove_poselib = False ):
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
def convert_to_poselib( book: spl.PoseBook ):
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
def load_poses_from_mmdtools( book: spl.PoseBook ):
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
		pose: spl.PoseData = book.poses.add()
		pose.name = morph.name
		for bone_name, rotation, location in morph.data:
			bd = pose.bones.add()
			bd.name = bone_name
			bd.location = location
			bd.rotation = rotation

	return


# Convert to MMD Tools' Bone Morph
def convert_poses_to_mmdtools( book: spl.PoseBook, use_alt_pose_names=False, clear_exsisting=False ):
	armature = book.id_data
	root = mmd.get_model_root( armature )
	if not root:
		return
	
	poses = book.poses
	bone_morphs = root.mmd_root.bone_morphs

	if clear_exsisting:
		bone_morphs.clear()

	for pose in poses:
		pose_name = pose.name_alt if use_alt_pose_names and pose.name_alt else pose.name

		# find by name
		morph = bone_morphs.get( pose_name )
		if not morph:
			morph = bone_morphs.add()
			morph.name = pose_name
			morph.category = pose.category if pose.category in ('EYEBROW', 'EYE', 'MOUTH') else 'OTHER'

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


# Helper: Guess pose category from pose name
EYEBROW = {'eyebrow', 'eyebrows', 'brow', 'brows', 'mayu'}
EYE = {'eye', 'eyes', 'eyelid', 'eyelids', 'iris', 'pupil', 'pupils', 'me' }
MOUTH = {'mouth', 'lips', 'lip', 'kuchibiru', 'kuchi'}

import re

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


# Json format
import json
# Save PoseBook into a file (JSON)
def save_book_to_json( book: spl.PoseBook, filepath, use_armature_space=False ):
	'''
		Parameters:
			book: PoseBook
			filepath: str
			use_armature_space: bool
				True: Save bone location and rotation in armature space (if possible)
				False: Save bone location and rotation in bone local space
	'''

	poses = book.poses

	# Convert to JSON
	data = []
	for pose in poses:
		pose_data = {
			'name' : pose.name,
			'name_alt' : pose.name_alt,
			'category' : pose.category,
			'space' : 'ARMATURE' if use_armature_space else 'LOCAL',
			'bones' : [],
		}
		for bone_data in pose.bones:
			name = bone_data.name
			loc = Vector(bone_data.location)
			rot = Quaternion(bone_data.rotation)
			sca = Vector(bone_data.scale)

			if use_armature_space:
				pbone = book.get_armature().pose.bones.get(name)
				loc, rot, sca = utils.to_armature_space( loc, rot, sca, pbone )

			bd = {
				'name' : name,
				'location' : loc[:],
				'rotation' : rot[:],
				'scale' : sca[:],
			}
			pose_data['bones'].append(bd)
		data.append(pose_data)
	
	# Save to file
	with open(filepath, 'w') as f:
		json.dump(data, f, indent=2)
	
	return


# Load PoseBook from a file (JSON)
def load_book_from_json( book: spl.PoseBook, filepath ):
	poses = book.poses
	poses.clear()

	arm = book.get_armature()

	# Load from file
	with open(filepath, 'r') as f:
		data = json.load(f)

	# Convert from JSON
	for pose_data in data:
		pose = poses.add()
		pose.name = pose_data.get('name')
		pose.name_alt = pose_data.get('name_alt')
		pose.category = pose_data.get('category', 'NONE')
		# if pose.category == 'NONE' and auto_set_category: # Guess
		# 	pose.category = guess_pose_category( pose.name )
		
		space = pose_data.get('space', 'LOCAL')

		for bone_data in pose_data.get('bones'):
			name = bone_data.get('name')
			loc = Vector( bone_data.get('location') )
			rot = Quaternion( bone_data.get('rotation') )
			sca = Vector( bone_data.get('scale', (1.0, 1.0, 1.0))  )

			if space == 'ARMATURE':
				pbone = arm.pose.bones.get(name)
				if pbone is None:
					print(f'Warning: Bone "{name}" not found in "{arm.name}", skipping...')
					continue

				loc, rot, sca = utils.to_armature_space( loc, rot, sca, pbone, invert=True )

			bd = pose.bones.add()
			bd.name = name
			bd.location = loc
			bd.rotation = rot
			bd.scale = sca

	# remove path and extension from filename
	book.name = os.path.splitext( os.path.basename(filepath) )[0]
	return


# CSV format
import csv

_POSE_CATEGORIES = [
	'NONE', 'EYEBROW', 'EYE', 'MOUTH', 'OTHER'
]


# Save PoseBook into a file (CSV)
def save_book_to_csv( book: spl.PoseBook, filename, scale=12.5, use_mmd_bone_names=True, use_alt_names=False ):
	poses = book.poses
	arm = book.get_armature()
	scale = scale * arm.scale[0] # consider armature scale

	converters = {b: mmd.BoneConverter(b, scale, invert=True) for b in arm.pose.bones}

	with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
		# write header
		header = ';PmxMorph,モーフ名,モーフ名(英),パネル(0:無効/1:眉(左下)/2:目(左上)/3:口(右上)/4:その他(右下)),モーフ種類(0:グループモーフ/1:頂点モーフ/2:ボーンモーフ/3:UV(Tex)モーフ/4:追加UV1モーフ/5:追加UV2モーフ/6:追加UV3モーフ/7:追加UV4モーフ/8:材質モーフ/9:フリップモーフ/10:インパルスモーフ)\n'
		csvfile.write(header)

		# write data
		for pose in poses:
			pose_name = pose.name_alt if use_alt_names and pose.name_alt else pose.name
			pose_name_alt = pose.name if use_alt_names and pose.name_alt else pose.name
			# Write a pose header
			# format: f"PmxMorph,{pose.name_j},{pose.name_e},{category_index},2(BoneMorph)"
			if pose.category not in _POSE_CATEGORIES:
				category_index = 4
			else:
				category_index = _POSE_CATEGORIES.index(pose.category)
			pose_header = f'PmxMorph,"{pose_name}","{pose_name_alt}",{category_index},2\n'
			csvfile.write(pose_header)

			# Write a bone list header
			# format: f";PmxBoneMorph,親モーフ名,オフセットIndex,ボーン名,移動量_x,移動量_y,移動量_z,回転量_x[deg],回転量_y[deg],回転量_z[deg]"
			bone_header = f';PmxBoneMorph,親モーフ名,オフセットIndex,ボーン名,移動量_x,移動量_y,移動量_z,回転量_x[deg],回転量_y[deg],回転量_z[deg]\n'
			csvfile.write(bone_header)

			# Write bone data
			for index, bone in enumerate(pose.bones):
				# Write a bone data
				# format: f"PmxBoneMorph,{pose.name},index,{bone.name},{loc.x},{loc.y},{loc.z},{rot.x},{rot.y},{rot.z}"

				pbone = arm.pose.bones.get(bone.name)
				if pbone is None:
					print(f'Warning: Bone "{bone.name}" in pose "{pose.name}" not found in "{arm.name}", skipping...')
					continue

				if use_mmd_bone_names:
					bone_name_j, _ = mmd.get_mmd_bone_name_j_e(pbone)
				else:
					bone_name_j = pbone.name

				# Convet using mmd_tools' BoneConverter
				converter = converters[pbone]
				loc = converter.convert_location(bone.location)
				rot = converter.convert_rotation(bone.rotation)
				rot.x, rot.y, rot.z = utils.quat_to_euler_mmd(rot, degrees=True)

				# # convert to armature space
				# loc, rot, _  = utils.to_armature_space( bone.location, bone.rotation, bone.scale, pbone )
				# loc = loc * scale * arm.scale[0] # convert to MMD unit considering armature scale
				# rot = utils.quaternion_to_degrees( rot )

				# # Swap YZ axis for MMD
				# loc = utils.swap_axis( loc, (0, 2, 1) )
				# rot = utils.swap_axis( rot, (0, 2, 1) )

				bone_data = f'PmxBoneMorph,"{pose_name}",{index},"{bone_name_j}",{loc.x:.5g},{loc.y:.5g},{loc.z:.5g},{rot.x:.5g},{rot.y:.5g},{rot.z:.5g}\n'
				csvfile.write(bone_data)

		# Comment
		csvfile.write("\n;This file is generated by Sakura Poselib addon for Blender.\n")
	# end of with open()

	return


# Load PoseBook from a file (CSV)
def load_book_from_csv( book: spl.PoseBook, filename, scale=0.08 ):
	poses = book.poses
	arm = book.get_armature()
	scale = scale / arm.scale[0] # consider armature scale
	converters = {b: mmd.BoneConverter(b, scale) for b in arm.pose.bones}

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
				# if pose.category == 0:
				# 	pose.category = guess_pose_category(pose.name)
				return pose

			# if the line is PMXMorph header, create a new pose
			if row[0].startswith('PmxMorph'):
				pose_name = row[1].strip('"')
				pose_name_e = row[2].strip('"')
				cat_index = int(row[3])
				pose = _add_pose(pose_name, cat_index)
				pose.name_alt = pose_name_e
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
				loc = Vector( (float(row[4]), float(row[5]), float(row[6])) ) 
				rot = Vector( (float(row[7]), float(row[8]), float(row[9])) )

				# convert to blender unit
				pbone = mmd.get_pose_bone_by_mmd_name(arm, bone_name)
				if pbone is None:
					print(f'Warning: Bone "{bone_name}" not found in "{arm.name}", skippping...')
					continue

				# # Convert using mmd_tools' BoneConverter
				converter = converters[pbone]
				loc = converter.convert_location(loc)
				rot = utils.euler_to_quat_mmd(rot, degrees=True) # convert to quaternion
				rot = converter.convert_rotation(rot)

				# Swap YZ axis for Blender
				# loc = utils.swap_axis( loc, (0, 2, 1) ) # still in MMD unit
				# rot = utils.swap_axis( rot, (0, 2, 1) )

				# # convert to Blender unit
				# loc = loc * scale / arm.scale[0] # convert to Blender unit (1/12.5 of MMD unit)
				# rot = utils.degrees_to_quaternion( rot )  # specify the order for conversion
				# # convert to bone local space
				# loc, rot, _ = utils.to_armature_space( loc, rot, Vector((1,1,1)), pbone, invert=True )

				bone = pose.bones.add()
				bone.name = pbone.name
				bone.location = loc
				bone.rotation = rot
				bone.scale = Vector((1.0,1.0,1.0)) # Not in MMD

				continue

		book.name = os.path.basename(filename)

	return


# Save a pose as VPD file
def export_pose_as_vpd( pose:spl.PoseData, filepath, scale=12.5 ):
	arm = pose.get_armature()

	vpd = mmd.VpdFile()

	for bone in pose.bones:
		bone: spl.BoneTransform

		pbone = arm.pose.bones.get(bone.name)
		if pbone is None:
			print(f'Warning: Bone "{bone.name}" not found in "{arm.name}", skipping...')
			continue

		converter = mmd.BoneConverter(pbone, scale, invert=True)
		loc = converter.convert_location(bone.location)
		rot = converter.convert_rotation(bone.rotation)
		rot = [rot.x, rot.y, rot.z, rot.w]

		bone_name = pbone.mmd_bone.name_j if pbone.mmd_bone.name_j else pbone.name
		vpd.bones.append( mmd.VpdBone( bone_name, loc, rot ) )
	
	vpd.osm_name = arm.name
	vpd.save(filepath=filepath)
	return

# Load a pose from VPD file
def import_pose_from_vpd( pose:spl.PoseData, filepath, scale=12.5 ):
	arm = pose.get_armature()

	vpd = mmd.VpdFile()
	try:
		vpd.load(filepath=filepath)
	except mmd.InvalidFileError as e:
		print(f'Error: Failed to load VPD file "{filepath}": {e}')
		return None

	pose.bones.clear()

	for vpdbone in vpd.bones:
		vpdbone: mmd.VpdBone

		pbone = mmd.get_pose_bone_by_mmd_name(arm, vpdbone.bone_name)
		if pbone is None:
			print(f'Warning: Bone "{vpdbone.bone_name}" not found in "{arm.name}", skipping...')
			continue

		converter = mmd.BoneConverter(pbone, scale)
		loc = Vector(vpdbone.location)
		loc = converter.convert_location(loc)

		rot = vpdbone.rotation
		rot = Quaternion((rot[3], rot[0], rot[1], rot[2]))
		rot = converter.convert_rotation(rot)

		bd = pose.bones.add()
		bd.name = pbone.name
		bd.location = loc
		bd.rotation = rot
		bd.scale = Vector((1.0,1.0,1.0)) # Not in MMD
	
	pose.name = os.path.basename(filepath)
	return pose






