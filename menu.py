# Description: Main Menu and Submenu for Sakura Poselib

import bpy
from bpy.types import Menu

# Main Menu in Pose Mode
class SPL_MT_PoseMenu(Menu):
	bl_label = "Sakura Poselib"
	bl_idname = "SPL_MT_PoseMenu"

	def draw(self, context):
		layout = self.layout
		layout.operator("spl.add_pose", text="New")

		spl = get_active_poselib(context)
		book = get_active_book(spl)
		if not book:
			return
		
		pose = get_active_pose(book)
		if pose:
			layout.operator("spl.replace_pose", text=f"Replace (Current)").pose_index = -1
		if len(book.poses):
			layout.menu("SPL_MT_ReplacePoseMenu", text="Replace...")


from .props import get_active_poselib, get_active_book, get_active_pose

# Submenu: Replace Pose
class SPL_MT_ReplacePoseMenu(Menu):
	bl_label = "Replace Pose"
	bl_idname = "SPL_MT_ReplacePoseMenu"

	def draw(self, context):
		layout = self.layout

		spl = get_active_poselib(context)
		book = get_active_book(spl)
		if not book:
			return

		for i, pose in enumerate(book.poses):
			op = layout.operator("spl.replace_pose", text=pose.name)
			op.pose_index = i


# Register
_classes = (
	SPL_MT_PoseMenu,
	SPL_MT_ReplacePoseMenu,
)

def register():
    for cls in _classes:
        bpy.utils.register_class(cls)

# Unregister
def unregister():
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)

