# mmd_tools related functions

import bpy

# get mmd root object
def get_mmd_root(obj: bpy.types.Object) -> bpy.types.Object:
	if not obj:
		return None
	if obj.mmd_type == 'ROOT':
		return obj
	return get_mmd_root(obj.parent)


# Check if mmd_tools is installed
def is_mmd_tools_installed():
	return bpy.context.preferences.addons.get("mmd_tools")


