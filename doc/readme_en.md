# Pose Library Plus

Pose Library Plus is an add-on for Blender 2.8 and later. It was created to replace the pose library, which will be gradually phased out in the Blender 3 series. With this add-on, you can easily save, manage, and apply poses.

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

- Compatibility:
  - Old pose library: Import and use the old format.
  - mmd_tools: Import existing bone morphs or convert the pose list to bone morphs.
  - json: Save and load pose lists as json files.

## Installation

To install Pose Library Plus, follow these steps:

1. Download the ZIP file for Pose Library Plus.
2. Open Blender, click "Edit" -> "Preferences" -> "Add-ons".
3. Click "Install" and select the downloaded ZIP file.
4. Click "Install Add-on" to install Pose Library Plus.

## Version History

- 2023/04/01
  - v1.0: Initial release

## Usage

Upon installing this add-on, a Sakura Poselib item will appear in the properties panel of the armature in pose mode. Poses are saved in the list within this item. The panel buttons allow for similar operations as the old pose library.

In pose mode, you can use the following hotkeys:

- Shift+L: Opens the pose editing menu. Save the current pose as a new entry or overwrite an existing pose.
- Alt+L: Pose preview. Quickly select the next pose with key or wheel operations.

## Support

The author is not responsible for any results from using this add-on. Please use it at your own risk.

## Author

Sakura Poselib (c) by Kafuji Sato, All rights reserved.
