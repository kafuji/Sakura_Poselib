import bpy
from .spl import get_poselib_from_context

# Wrappers for operator poll
from functools import wraps
def requires_active_armature(func):
    """Check if the active object is an armature"""
    @wraps(func)
    def wrapper(cls, context):
        spl = get_poselib_from_context(context)
        if not spl:
            return False

        return func(cls, context)
    return wrapper

def requires_animation_disabled(func):
    """Check if the active object is not in animation mode"""
    @wraps(func)
    def wrapper(cls, context):
        spl = get_poselib_from_context(context)
        if spl.enable_animation:
            return False

        return func(cls, context)
    return wrapper

def requires_active_posebook(func):
    """Check if the active posebook exists"""
    @wraps(func)
    def wrapper(cls, context):
        spl = get_poselib_from_context(context)
        if not spl:
            return False
        if not spl.get_active_book():
            return False

        return func(cls, context)
    return wrapper

def requires_active_pose(func):
    """Check if the active posebook has active pose"""
    @wraps(func)
    def wrapper(cls, context):
        spl = get_poselib_from_context(context)
        if not spl:
            return False
        book = spl.get_active_book()
        if not book:
            return False
        
        pose = book.get_active_pose()
        if not pose:
            return False

        return func(cls, context)
    return wrapper

def requires_poses(func):
    """Check if the active posebook has any poses"""
    @wraps(func)
    def wrapper(cls, context):
        spl = get_poselib_from_context(context)
        if not spl:
            return False
        book = spl.get_active_book()
        if not book:
            return False
        
        if len(book.poses) == 0:
            return False

        return func(cls, context)
    return wrapper

def requires_blender_pose_library(func):
    """Check if the Blender version has pose_library attribute"""
    @wraps(func)
    def wrapper(cls, context):
        if not 'pose_library' in bpy.types.Object.bl_rna.properties:
            return False
        return func(cls, context)
    return wrapper
