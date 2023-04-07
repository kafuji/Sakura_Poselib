# Sakura Poselib

## Installation

To install Pose Library Plus, follow these steps:

1. Download the ZIP file for Pose Library Plus.
2. Open Blender, click "Edit" -> "Preferences" -> "Add-ons".
3. Click "Install" and select the downloaded ZIP file.
4. Click "Install Add-on" to install Pose Library Plus.

## GUI

After installing the addon, Sakura Poselib panel will be added on Armature Properites Panel.


## Features

### PoseBook

PoseBook is a collection of poses in Sakura Poselib. An armature can store multiple PoseBooks. This is similar to former pose library's 'action'.

Different from action, PoseBook is not a collection of keyframes. PoseBook stores poses as colleciton of { pose_name: bone_daga } structure.

### Pose

A Pose in Sakura Poselib is just a simple pair of { pose_name: bone_data }. The bone_data contains list of {bone_name: transform} data, and it can be edited in 'Bone Data' subpanel within Sakura Poselib panel.

### Adding a Pose

As same as former pose library, Shift+L shows Add/Replace menu  in pose mode. 
When adding a pose, bones that actually contributes current pose are automatically added to pose data. You don't need to select bones to add them. 
During this process, invisible bones are ignored, so you can prevent adding unnecessary bones to the pose data.

### Replacing a Pose

Same as adding pose, you can replace existing pose with current pose. Unnecessary bones will be remoded form pose data in this process.


### Preview Poses / Combined Pose

In the pose list of Sakura Poselib, there is a slider on each pose.
You can adjust each value to preview combined pose.
You can also create mixed pose by adding new pose while previewing.

Notice: This feature is not compatible with blender animation system. Designed for just preview purpose.

### Import/Export

#### From Pose Library (former)

Blender supports old type pose library up to 3.4. Sakura Poselib can use their data by importing from current pose library assigned on the armature.
If you need to retrieve several old pose library data, it is recommended to use Blender 3.12 or less due of pose library function removable in greater versions of Blender. 

Sakura Poselib can also export it's PoseBook to old pose library, but it is not recommended to use this feature because pose library is absolutely deplecated from Blender 3.5 (Replaced with Pose Assets type pose library).

#### From MMD_Tools

Sakura Poselib can use MMD models bone morph data as Pose Library by importing from a MMD model that is created by MMD_Tools.
You can also export your PoseBook to MMD model by using export feature in Sakura Poselib.


#### From File (Json and CSV)

You can export active PoseBook to a file.

 - Json: Only use for export/import between models witch uses Sakura Poselib.
 - CSV: Compatible PMX Editor (MMD model editor). You can export PoseBook to csv and use it in PMX Editor. Alternatively you can use CSV (Bone Morph) file exported from PMX Editor as Sakura Poselib's PoseBook.


### Utilities:

#### Pose Preview mode

In pose mode, Alt+L invokes Sakura Poselib's pose preview mode. You can cycle Pose and PoseBook by tapping keys (Instruction displayed on 3D Viewport).

#### Pose Data Cleaner

Within the Sakura Poselib panel, there are some handy operator buttons. 
Pose Data Cleaner button calls operator that removes unnecessary / invalid bone transforms from poses within active PoseBook.
If your pose data become invalid by renaming bones, be careful to use this (Transforms with invalid bone names will be removed!).

#### Bone Name Tracker

This is a background handler type feature.
This addon automatically track bone renames and maintain pose data healthy when renames detected.





