# Description: Hotkey registration for Pose Library Plus

import bpy

# Keymap for Addon hotkeys
addon_keymaps = []

def register_keymaps():
	wm = bpy.context.window_manager

	# Pose Menu
	km = wm.keyconfigs.addon.keymaps.new(name='Pose', space_type='EMPTY')
	kmi = km.keymap_items.new('wm.call_menu', 'L', 'PRESS', shift=True)
	kmi.properties.name = "SPL_MT_PoseMenu"
	addon_keymaps.append((km, kmi))

	# Preview Pose
	km = wm.keyconfigs.addon.keymaps.new(name='Pose', space_type='EMPTY')
	kmi = km.keymap_items.new('spl.pose_preview', 'L', 'PRESS', alt=True)
	addon_keymaps.append((km, kmi))

def unregister_keymaps():
	for km, kmi in addon_keymaps:
		km.keymap_items.remove(kmi)
	addon_keymaps.clear()


# Register
def register():
    register_keymaps()

# Unregister
def unregister():
    unregister_keymaps()

