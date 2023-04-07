# track bone renames
# path: handlers.py

import bpy
from bpy.app.handlers import persistent
from .props import get_poselib

# Msgbus handlers
def on_bone_rename( *args ):
    print( 'on_bone_rename', args )

    # find renamed bones and update bone name backup
    for arm in [o for o in bpy.data.objects if o.pose]:
        plp = get_poselib(arm)
        if plp is None:
            continue

        for bone in arm.data.bones:
            old_name = bone.get('spl_bone_name_backup', None)
            if old_name is None: # may be a new bone
                bone['spl_bone_name_backup'] = bone.name
                continue

            if bone.name != old_name:
                # update bone name in all poses
                for book in plp.books:
                    for pose in book.poses:
                        for bone_data in pose.bones:
                            if bone_data.name == old_name:
                                bone_data.name = bone.name
                                break
                # update bone name backup
                bone['spl_bone_name_backup'] = bone.name

    return


# Msgbus
msg_handlers = [
    ( (bpy.types.Bone, 'name'), on_bone_rename ), # track bone renames
    ( (bpy.types.PoseBone, 'name'), on_bone_rename ), # track bone renames
]

owner=object()
def register_msgbus():
    for datapath, func in msg_handlers:
        bpy.msgbus.subscribe_rna( owner=owner, key=datapath, args=(), notify=func )
    return

def unregister_msgbus():
    bpy.msgbus.clear_by_owner(owner)

# Timer handler
def timed_handler_every_second():
    #print('timed_handler_every_second')
    return 1.0



# On Load handler
@persistent
def on_load(dummy):
    # create bone name backup
    for arm in bpy.data.armatures:
        for bone in arm.bones:
            bone['spl_bone_name_backup'] = bone.name

    # re-register handlers
    if not bpy.app.timers.is_registered(timed_handler_every_second):
        bpy.app.timers.register(timed_handler_every_second)
    
    # if depsgraph_update_post_handler not in bpy.app.handlers.depsgraph_update_post:
    #     bpy.app.handlers.depsgraph_update_post.append(depsgraph_update_post_handler)
    #     return

    unregister_msgbus()
    register_msgbus()

    return


# Register addon
def register():
    bpy.app.timers.register(timed_handler_every_second)
    bpy.app.handlers.load_post.append(on_load)
    register_msgbus()


# Unregister addon
def unregister():
    if bpy.app.timers.is_registered(timed_handler_every_second):
        bpy.app.timers.unregister(timed_handler_every_second)
    bpy.app.handlers.load_post.remove(on_load)
    unregister_msgbus()

