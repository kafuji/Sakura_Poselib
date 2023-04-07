# Description: Addon preferences

import bpy

DEV_MODE = True

# Addon Preferences
class SPL_Preferences(bpy.types.AddonPreferences):
    bl_idname = __package__

    dev_mode : bpy.props.BoolProperty(
        name = 'Developer Mode',
        description = 'Show developer UI items',
        default = DEV_MODE,
    )

    def draw(self,context):
        layout = self.layout
        row = layout.row()
        row.prop(self, 'dev_mode')
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

