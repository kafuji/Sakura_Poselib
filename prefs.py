# Description: Addon preferences

import bpy
from bpy.props import *

# Addon Preferences
class SPL_Preferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    # dev_mode : bpy.props.BoolProperty(
    #     name = 'Developer Mode',
    #     description = 'Show developer UI items',
    #     default = DEV_MODE,
    # )

    show_alt_pose_names: BoolProperty(
		name="Show Alt Names",
		description="Show alternative pose names. Mainly intended for translation. Not used as idetifier in blender",
		default=True, 
		)

    show_apply_buttons: BoolProperty(
        name="Show Apply Buttons",
        description="Show apply buttons in the pose list",
        default=False,
    )

    show_select_bones_buttons: BoolProperty(
        name="Show Select Bones Buttons",
        description="Show select bones buttons in the pose list",
        default=False,
    )

    show_replace_buttons: BoolProperty(
        name="Show Replace Buttons",
        description="Show replace buttons in the pose list",
        default=True,
    )


    def draw(self,context: bpy.types.Context):
        layout:bpy.types.UILayout = self.layout

        # Pose List Display Settings
        box = layout.box()
        box.label(text="Pose List Display Settings")
        flow = box.grid_flow(row_major=True, columns=2, even_columns=True, even_rows=True, align=False)
        flow.prop(self, "show_alt_pose_names", icon='TEXT')
        flow.prop(self, "show_apply_buttons", icon='VIEWZOOM')
        flow.prop(self, "show_select_bones_buttons", icon='RESTRICT_SELECT_OFF' )
        flow.prop(self, "show_replace_buttons", icon='GREASEPENCIL')
        
        # box.prop(self, "show_alt_pose_names", icon='TEXT')
        # box.prop(self, "show_apply_buttons", icon='VIEWZOOM')
        # box.prop(self, "show_select_bones_buttons", icon='RESTRICT_SELECT_OFF' )
        # box.prop(self, "show_replace_buttons", icon='GREASEPENCIL')

        # Developer Settings
        # box = layout.box()
        # box.label(text="Developer Settings")
        # box.prop(self, "dev_mode")

        return

_classes = (
    SPL_Preferences,
)


# Register & Unregister
def register():
    for cls in _classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)

