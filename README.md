# Sakura Poselib

Sakura Poselib is an add-on for Blender. It was created to replace the pose library, which will be gradually phased out in the Blender 3 series. With this add-on, you can easily save, manage, and apply poses.

# Supported Version

Blender 2.8 or later (Export/Import from old pose library is supported up to 3.4)

## Features

- Replicates the old pose library:
  - Save named pose states and recall them using buttons on the panel or hotkeys (Alt+L).
  - Display the add and replace pose menu with Shift+L for quick editing.

- Unique features:
  - Poses are stored in a simple format internally by the add-on, rather than as actions.
  - Pose lists are stored as collections called "Pose Books". You can create multiple pose books.
  - Easy and reliable pose editing. Bones contributing to the transformation are automatically saved in the pose entry. There is no need to select bones.
  - Individual bone editing. The bone list of the selected pose is displayed in the panel, where you can edit bone names and transforms.
  - Pose mixing. Adjust the degree of pose application with sliders for each pose, and check the combined state of multiple poses.
    - Note: This is not suitable for animation purposes, such as setting keyframes.
    - Animation compatible pose features will be supported in feature releases.
  - Track bone name changes. When you rename bones in the armature, bone names in pose data will be also changed. 
  - Free from bone rotation modes. Pose data is stored as quaternion rotation and will be automatically converted into current bone's rotation mode when applying pose to armature.

- Compatibility:
  - Old pose library: Import from old pose library / Export to old pose library (Supports up to Blender 3.4),
  - mmd_tools: Import existing bone morphs or convert the pose list to bone morphs.
  - json: Save and load pose lists as json files.

## Version History

- 2023/04/15: Version 1.0.0
  - Initial release

## Usage

Upon installing this add-on, a Sakura Poselib item will appear in the properties panel of the armature. Poses are saved in the list within this item. The panel buttons allow for similar operations as the old pose library.

In pose mode, you can use the following hotkeys:

- Shift+L: Opens the pose editing menu. Save the current pose as a new entry or overwrite an existing pose.
- Alt+L: Pose preview. Quickly select the next pose with key or wheel operations.

## Support

The author is not responsible for any results from using this add-on. Please use it at your own risk.

# License

MIT License.

## Author

Kafuji Sato / VR Character Workshop
