# Description: Panel for Sakura Poselib

import bpy
from bpy.types import Panel
from bpy.types import UIList

from .spl import get_poselib, get_poselib_from_context, get_armature_from_id
from .poll_requirements import *

# UIList for displaying the poses categories in Sakura Poselib
class SPL_UL_PoseCategoryList(UIList):
	def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
		l:bpy.types.UILayout = layout
		# Draw each item in the list as a label with the pose name
		row = l.row()
		row.prop( item, 'name', text='', emboss=False )


# UIList for displaying the poses in Sakura Poselib
class SPL_UL_PoseBook(UIList):
	def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
		l:bpy.types.UILayout = layout

		prefs = bpy.context.preferences.addons[__package__].preferences

		row = l.row(align=True)
		sp = row.split(factor=0.2, align=True)
		sp.prop( item, 'category', text='', emboss=False)
		sp.prop( item, 'name', text='', emboss=False )
		if prefs.show_alt_pose_names:
			sp.prop( item, 'name_alt', text='', emboss=True )

		spl = get_poselib_from_context(context)
		if spl.enable_animation:
			arm = get_armature_from_id(item)
			con_name = item.get('constraint_name', None)
			if con_name and con_name in arm.keys():
				sp.prop( arm, '["' + con_name + '"]', slider=True, text='' )
			else:
				sp.label(text="", icon='ERROR')
		else:
			sp.prop( item, 'value', slider=True, text='' )

		#col = l.column(align=True)
		#row = l.row(align=True)

		if prefs.show_apply_buttons or prefs.show_replace_buttons or prefs.show_select_bones_buttons:
			row.separator()

		if prefs.show_apply_buttons:
			row.operator( 'spl.apply_pose', text='', icon='VIEWZOOM').pose_index = index
		if prefs.show_replace_buttons:
			row.operator( 'spl.replace_pose', text='', icon='GREASEPENCIL').pose_index = index
		if prefs.show_select_bones_buttons:
			row.operator( 'spl.select_bones_in_pose', text='', icon='RESTRICT_SELECT_OFF').pose_index = index
		

		# row.operator( 'spl.apply_pose', text='', icon='VIEWZOOM').pose_index = index # apply single pose
		# row.operator( 'spl.replace_pose', text='', icon='GREASEPENCIL').pose_index = index # replace pose data with current pose
		# col.operator( 'spl.select_bones_in_pose', text='', icon='RESTRICT_SELECT_OFF').pose_index = index

	def filter_items(self, context: bpy.types.Context, data: bpy.types.AnyType, property: str):
		# filter items by category
		# print(data, property)
		category_filter = data.category_filter

		items = getattr(data, property)

		# Filter
		filtered = [self.bitflag_filter_item] * len(items)

		# by category
		if category_filter != 'ALL':
			for i, item in enumerate(items):
				if item.category != category_filter:
					filtered[i] = ~self.bitflag_filter_item

		# by search string
		if self.use_filter_invert:
			for i, item in enumerate(items):
				if self.filter_name in item.name:
					filtered[i] = ~self.bitflag_filter_item
		else:
			for i, item in enumerate(items):
				if self.filter_name not in item.name:
					filtered[i] = ~self.bitflag_filter_item

		# Sort
		ordered = []
		if self.use_filter_sort_alpha:
			ordered = bpy.types.UI_UL_list.sort_items_by_name(items)

		return filtered, ordered



# UIList for displaying the Bones in Pose in Sakura Poselib
class SPL_UL_BoneList(UIList):
	def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
		l:bpy.types.UILayout = layout
		# Draw each item in the list as a label with the pose name
		arm = get_armature_from_id(item)
		pbone = arm.pose.bones.get(item.name)

		row = l.row(align=True)
		row.alert = pbone is None
		row.label( text=item.name, icon='BONE_DATA')
		row.operator( 'spl.remove_bone_from_pose', text='', icon='REMOVE').bone_index = index


# Submenu for PoseBook operations
class SPL_MT_PoseBookMenu(bpy.types.Menu):
	bl_label = "PoseBook Operations"
	bl_idname = "SPL_MT_PoseBookMenu"

	def draw(self, context):
		l:bpy.types.UILayout = self.layout
		l.operator( 'spl.duplicate_posebook', icon='DUPLICATE')
		l.operator( 'spl.merge_posebook', icon='OUTLINER_OB_GROUP_INSTANCE')

		l.separator()
		l.operator( 'spl.scale_pose_data', icon='EMPTY_ARROWS')

		l.separator()
		l.menu( 'SPL_MT_ImportMenu', icon='IMPORT')
		l.menu( 'SPL_MT_ExportMenu', icon='EXPORT')


# Submenu for export acitons
class SPL_MT_ConvertMenu(bpy.types.Menu):
	bl_label = "Convert"
	bl_idname = "SPL_MT_ConvertMenu"

	def draw(self, context):
		l:bpy.types.UILayout = self.layout
		l.label(text="Import / Export", icon='IMPORT')
		l.operator('spl.load_from_poselibrary', icon='IMPORT')
		l.operator('spl.convert_to_poselibrary', icon='EXPORT')
		l.separator()
		l.operator('spl.load_from_mmdtools', icon='IMPORT')
		l.operator('spl.send_to_mmdtools', icon='EXPORT')
	
		l.separator()
		l.label(text="Save / Load", icon='FILE')
		l.operator('spl.load_from_json', icon='FILE_FOLDER')
		l.operator('spl.save_to_json', icon='CURRENT_FILE')
		l.separator()
		l.operator('spl.load_from_csv', icon='FILE_FOLDER')
		l.operator('spl.save_to_csv', icon='CURRENT_FILE')

# Submenu for Import actions
class SPL_MT_ImportMenu(bpy.types.Menu):
	bl_label = "Import"
	bl_idname = "SPL_MT_ImportMenu"

	def draw(self, context):
		l:bpy.types.UILayout = self.layout
		l.operator('spl.load_from_poselibrary', icon='IMPORT')
		l.operator('spl.load_from_mmdtools', icon='IMPORT')
		l.separator()
		l.operator('spl.load_from_json', icon='FILE_FOLDER')
		l.operator('spl.load_from_csv', icon='FILE_FOLDER')


# Submenu for Export actions
class SPL_MT_ExportMenu(bpy.types.Menu):
	bl_label = "Export"
	bl_idname = "SPL_MT_ExportMenu"

	def draw(self, context):
		l:bpy.types.UILayout = self.layout
		l.operator('spl.convert_to_poselibrary', icon='EXPORT')
		l.operator('spl.send_to_mmdtools', icon='EXPORT')

		l.separator()
		l.operator('spl.save_to_json', icon='CURRENT_FILE')
		l.operator('spl.save_to_csv', icon='CURRENT_FILE')


# Submenu for Pose List
class SPL_MT_PoseListMenu(bpy.types.Menu):
	bl_label = "Pose Operations"
	bl_idname = "SPL_MT_PoseListMenu"

	def draw(self, context):
		l:bpy.types.UILayout = self.layout
		l.operator('spl.move_pose_to_posebook', icon='FILE_PARENT')
		l.separator()
		l.operator( 'spl.auto_set_pose_category', icon='LINENUMBERS_ON')
		l.operator( 'spl.batch_rename_poses', icon='SYNTAX_OFF')
		l.operator( 'spl.batch_rename_bones', icon='SYNTAX_OFF')
		l.operator( 'spl.sort_poses', icon='SORTALPHA')
		l.operator( 'spl.clean_poses', icon='BRUSH_DATA')
		l.separator()
		l.operator( 'spl.save_pose_to_vpd', icon='EXPORT')
		l.operator( 'spl.load_pose_from_vpd', icon='IMPORT')

# Submenu for Pose List Display Settings
class SPL_MT_PoseListDisplayMenu(bpy.types.Menu):
	bl_label = "Pose List Display Settings"
	bl_idname = "SPL_MT_PoseListDisplayMenu"

	def draw(self, context):
		l:bpy.types.UILayout = self.layout
		prefs = bpy.context.preferences.addons[__package__].preferences

		box = l.box()
		box.label(text="Pose List Display Settings")
		flow = box.grid_flow(row_major=True, columns=2, even_columns=True, even_rows=True, align=False)
		flow.prop(prefs, "show_alt_pose_names", icon='TEXT')
		flow.prop(prefs, "show_apply_buttons", icon='VIEWZOOM')
		flow.prop(prefs, "show_select_bones_buttons", icon='RESTRICT_SELECT_OFF' )
		flow.prop(prefs, "show_replace_buttons", icon='GREASEPENCIL')

		return

# Panel drawer for Property Panel and 3D View Side Panel
def draw_main_panel(self, context: bpy.types.Context):
	l:bpy.types.UILayout = self.layout

	obj = context.object
	if obj.pose:
		arm = obj
	else:
		arm = obj.find_armature()
	
	if not arm:
		l.label(text="No model selected.", icon='INFO')
		return

	spl = get_poselib(arm)
	book = spl.get_active_book()

	# Draw the PoseBook list as a UIList, and add buttons for PoseBook operations
	row = l.row(align=True)
	row.alignment = 'LEFT'
	row.label(text="PoseBooks:", icon='ASSET_MANAGER')
	col = row.column(align=True)
	if arm.library or arm.override_library:
		col.alert = True
	col.label(text=arm.name, icon='OUTLINER_OB_ARMATURE', translate=False )

	row = l.row( align=False )
	row.template_list("SPL_UL_PoseCategoryList", "", spl, "books", spl, "active_book_index", rows=5)
	#row.prop_search(spl, "active_list_name", spl, "books", text="")
	row = row.column(align=True)
	row.operator( 'spl.add_book', text='', icon='ADD')
	row.operator( 'spl.remove_book', text='', icon='REMOVE')
	row.separator()
	row.operator( 'spl.move_book', text='', icon='TRIA_UP').direction = 'UP'
	row.operator( 'spl.move_book', text='', icon='TRIA_DOWN').direction = 'DOWN'
	row.separator()
	# PoseBook submenu
	row.menu( 'SPL_MT_PoseBookMenu', text='', icon='DOWNARROW_HLT')


	# Draw add pose button when no active PoseBook
	if not book:
		l.label(text="No active PoseBook.", icon='INFO')
		l.operator( 'spl.add_book', icon='ADD')
		return

	# Draw the pose list as a UIList, and add buttons for pose operations
	col = l.column(align=True)
	l.enabled = book.poses is not None
	col.prop(spl, 'enable_animation', expand=True, toggle=True, icon='ANIM')

	row = l.row(align=True)
	sp = l.split(factor=0.6, align=True)
	row = sp.row(align=True)
	row.alignment = 'LEFT'
	row.label(text="Poses:", icon='POSE_HLT')
	row.label(text=book.name, translate=False)

	prefs = bpy.context.preferences.addons[__package__].preferences
	col = sp.column(align=True)
	col.alignment = 'RIGHT'
	row = col.row(align=True)
	row.alignment = 'RIGHT'
	row.label(text="Display Settings:")
	row.prop(prefs, 'show_alt_pose_names', toggle=True, icon='TEXT', text='')
	row.prop(prefs, 'show_apply_buttons', toggle=True, icon='VIEWZOOM', text='')
	row.prop(prefs, 'show_select_bones_buttons', toggle=True, icon='RESTRICT_SELECT_OFF', text='')
	row.prop(prefs, 'show_replace_buttons', toggle=True, icon='GREASEPENCIL', text='')


	#col.prop(book, 'show_alt_pose_names', toggle=True, icon='TEXT')

	row = l.row()
	row.prop(book, 'category_filter', expand=True)
	
	row = l.row()
	row.template_list("SPL_UL_PoseBook", "", book, "poses", book, "active_pose_index", rows=9)

	col = row.column(align=True)
	col.operator('spl.add_pose', text="", icon='ADD')
	col.operator('spl.remove_pose', text="", icon='REMOVE')

	col.separator()

	# Up/Down buttons for moving poses in the list
	col.operator('spl.move_pose', text="", icon='TRIA_UP').direction = 'UP'
	col.operator('spl.move_pose', text="", icon='TRIA_DOWN').direction = 'DOWN'

	# Top and Bottom buttons for moving poses to the top or bottom of the list
	col.separator()
	col.operator('spl.move_pose', text="", icon='TRIA_UP_BAR').direction = 'TOP'
	col.operator('spl.move_pose', text="", icon='TRIA_DOWN_BAR').direction = 'BOTTOM'

	# Duplicate pose button
	col.separator()
	col.operator('spl.duplicate_pose', text="", icon='DUPLICATE')

	col.separator()
	col.operator('spl.reset_book_values', text="", icon='X')
	col.separator()
	col.menu( 'SPL_MT_PoseListMenu', text='', icon='DOWNARROW_HLT')

	# Rest poses in the book button
	col = l.column(align=True)
	row = col.row(align=False)
	row.operator( 'spl.apply_pose', icon='VIEWZOOM').pose_index = -1 # apply single pose
	row.operator( 'spl.replace_pose', icon='GREASEPENCIL').pose_index = -1 # replace pose data with current pose

	return



# Panel to display Sakura Poselib functionality in the properties panel
class SPL_PT_PoseLibPropPanel(Panel):
	bl_label = "Sakura Poselib"
	bl_idname = "SPL_PT_PoseLibPropPanel"
	bl_space_type = 'PROPERTIES'
	bl_region_type = 'WINDOW'
	bl_context = "data"
	bl_options = {'DEFAULT_CLOSED'}

	# Only show the panel when an armature object is selected
	@classmethod
	def poll(cls, context):
		return context.object and context.object.pose

	def draw(self, context):
		draw_main_panel(self, context)


# Panel to display Sakura Poselib in the 3D View Side Panel
class SPL_PT_PoseLibrarySidePanel(Panel):
	bl_label = "Sakura Poselib"
	bl_idname = "SPL_PT_PoseLibSidePanel"
	bl_space_type = 'VIEW_3D'
	bl_region_type = 'UI'
	bl_category = "Sakura"

	# Only show the panel when an armature object is selected
	@classmethod
	def poll(cls, context):
		return context.object

	def draw(self, context):
		draw_main_panel(self, context)


# Panel to display Sakura Poselib functionality in the properties panel
class SPL_PT_PoseBoneData(Panel):
	bl_label = "Pose Bone Data"
	bl_idname = "SPL_PT_PoseBoneData"
	bl_parent_id = "SPL_PT_PoseLibPropPanel"
	bl_space_type = 'PROPERTIES'
	bl_region_type = 'WINDOW'
	bl_context = "data"
	bl_options = {'DEFAULT_CLOSED'}

	@classmethod
	@requires_poses
	def poll(cls, context):
		return True

	def draw(self, context):
		l = self.layout
		spl = get_poselib_from_context(context)
		book = spl.get_active_book()
		poses = book.poses
		pose_index = book.active_pose_index

		# Show Bone List and Transforms for selected pose
		pose = poses[pose_index] if len(poses) > pose_index else None
		if not pose:
			l.label(text="No active pose.", icon='INFO')
		else:
			row = l.row()
			row.prop(book, 'name', icon='OUTLINER_OB_ARMATURE')
			row.prop(pose, 'name', icon='ARMATURE_DATA')
			col = l.column()
			# Bone List from active pose
			col.label(text='Bones:', icon='BONE_DATA')
			row = col.row()
			row.template_list("SPL_UL_BoneList", "", pose, 'bones', pose, 'active_bone_index' )
			col = row.column()
			col.operator( 'spl.add_selected_bone_to_pose', text='', icon='ADD' )
			col.separator()
			col.operator( 'spl.select_bones_in_pose', text='', icon='RESTRICT_SELECT_OFF').pose_index = pose_index # select bones in pose

			# show transforms for selected bone
			bone = pose.bones[pose.active_bone_index] if len(pose.bones) > pose.active_bone_index else None
			if bone:
				col = l.column()
				col.label(text=f'Transforms: {bone.name}')
				col.row().prop(bone, 'location')
				col.row().prop(bone, 'rotation')
				col.row().prop(bone, 'scale')

# Pose Library converter Panel
class SPL_PT_PoseBookConverter(Panel):
	bl_label = "Converter"
	bl_idname = "SPL_PT_PoseBookConverter"
	bl_parent_id = "SPL_PT_PoseLibPropPanel"
	bl_space_type = 'PROPERTIES'
	bl_region_type = 'WINDOW'
	bl_context = "data"
	bl_options = {'DEFAULT_CLOSED'}

	def draw(self, context):
		l = self.layout

		l.label(text="Import/Export", icon='IMPORT')
		row = l.row()
		row.operator("spl.load_from_poselibrary", icon='IMPORT')
		row.operator("spl.convert_to_poselibrary", icon='EXPORT')
		row = l.row()
		row.operator("spl.load_from_mmdtools", icon='IMPORT')
		row.operator("spl.send_to_mmdtools", icon='EXPORT')

		l.separator()
		row = l.row()
		row.operator("spl.load_from_json", icon='FILE_FOLDER')
		row.operator("spl.save_to_json", icon='CURRENT_FILE')
		row = l.row()
		row.operator("spl.load_from_csv", icon='FILE_FOLDER')
		row.operator("spl.save_to_csv", icon='CURRENT_FILE')

		l.separator()
		return


# Register all classes
_classes = [ 
	SPL_UL_PoseCategoryList,
	SPL_UL_PoseBook,
	SPL_MT_PoseBookMenu,
	SPL_MT_ConvertMenu,
	SPL_MT_ImportMenu,
	SPL_MT_ExportMenu,

	SPL_MT_PoseListMenu,
	SPL_MT_PoseListDisplayMenu,
	SPL_UL_BoneList,
	SPL_PT_PoseLibPropPanel,
	SPL_PT_PoseLibrarySidePanel,
	SPL_PT_PoseBoneData,
	# SPL_PT_PoseBookConverter,
]

# Register & Unregister
def register():
	for cls in _classes:
		bpy.utils.register_class(cls)

def unregister():
	for cls in reversed(_classes):
		bpy.utils.unregister_class(cls)

