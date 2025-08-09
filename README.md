# Sakura Poselib

***Yet another pose library with a lot of handy features.***

Sakura Poselib was created to replace the old pose library, which was gradually phased out in the Blender 3 series.

With this addon, you can easily create, manage, apply poses, and use them directly in your animations.

You can also export them for other applications (currently PMX Editor is supported).

[Get it from Blender Extension Repository](https://extensions.blender.org/add-ons/sakura-poselib/)

## Overview

- Quickly create pose data from current armature pose.
- Importing poses from the old pose library, mmd_tools, PMX Editor, etc.
- Managing them by categorizing, batch renaming, etc.
- Naturally combine poses by sliders, which work the same way as Shape Keys influence values.
- Use them in Animation timeline by just keying pose values.
- Save pose data to a file and reuse it with other models.
- Use them in MMD models by exporting to mmd_tools or saving as CSV files or VPD files.
- And many other handy features are included.
- Multi language: English and Japanese are supported.

## Where to find

- Sakura tab at 3D Viewport side panel.

## Online Documents

- [English](https://kafuji.github.io/Sakura-Creative-Suite/en/addons/Sakura_PoseLib/)
- [日本語](https://kafuji.github.io/Sakura-Creative-Suite/ja/addons/Sakura_PoseLib/)

## Change Log

- 2025/08/09: v1.4.3
  - Fixed an issue where the pose data was not being saved correctly when the armature had a parent with scale.

- 2025/07/30: v1.4.2
  - Changed display style of Bone names in the Bone list for better visibility.
  - Update README and init.py (bl_info) to describe GUI changes.

- 2025/07/30: v1.4.1
  - Load PoseBook from JSON:
    - Added warning message when matching bone is missing in the Armature.
  - Replace Pose:
    - Added confirmation dialog when replacing a pose.
      - This is optional. Set "Confirm on Replace Pose" option in the addon preferences to enable it.
  - GUI:
    - Removed Sakura Poselib panel from the Armature data tab in the Properties editor.
      - It is now only available in the 3D Viewport side panel.
      - Bone List panel was moved to the 3D Viewport side panel.
      - Bone names in the Bone List panel are now editable.
  - Minor bug fixes and improvements.

- 2025/04/22: v1.4.0
  - Added "Sort Poses" operator on Pose List menu.
    - Sorts poses by name or category.
  - Added "Load Pose from VPD" and "Save Pose to VPD" operators.
    - Load/Save pose data from/to VPD file format.
    - VPD files can be used in MMD applications.
  - Save to CSV and Load from CSV:
    - Enhanced internal data handling for better results.
    - It still struggles with some poses, which have complex bone rotations. Please use "Export to mmd_tools" or "Save Pose to VPD" for complex poses.
  - Many minior bug fixes and improvements.

- 2025/03/15: v1.3.2
  - Fixed issues where the pose book list was not being displayed on the "Merge PoseBooks" and the "Move Pose to PoseBook" operator UI.

- 2025/03/01: v1.3.1
  - PoseBook Menu:
    - Removed Save/Load submenu and merged them to the Import/Export submenu.
    - Added "Scale Pose Data" Operator.
      - Scales translation(bone movement) of pose data in the active/all pose books.
      - Can be used to adjust pose data to fit the model size.

- 2025/02/20: v1.3.0
  - Added "Duplicate PoseBook" Operator.
    - Can be found in the PoseBook menu.

- 2025/02/10: v1.2.9
  - Add Pose and Replace Pose:
    - Fixed an issue where hidden bones are not ignored when adding or replacing poses with the "Ignore Hidden Bones" option enabled on Blender 4.2 or later.
    - Operator option "Ignore Hidden Bones" is now enabled by default.

- 2025/01/02: v1.2.8
  - Added "Activate Poses on Book Change" option in addon preferences (default is False).
    - When enabled, the poses on the active book will be activated when the active book is changed (previous versions default behavior).

- 2024/11/18: v.1.2.7
  - Some minor fixes according to review from Blender Extension team.

- 2024/11/14: v.1.2.5
  - Added blender_manifest.toml for Blender 4.2.
    - This add-on is now work as well as an extension (for Blender 4.2 or later).
  - Licence changed to GPL v3.

- 2024/11/07: v.1.2.4
  - Save to JSON: Added the "Use Armature Space" option to save poses in armature space (default is True).
    - When enabled, bone transforms are saved in armature space, which is useful for sharing poses across different armatures with varying bone rolls.
    - When disabled, bone transforms are saved in bone local space, matching previous versions (Blender’s default behavior).
  - Load from JSON/CSV: Removed the automatic category-setting behavior for loading poses.
  - PoseBook menu: Tweaked for more usability.

- 2024/08/03: v1.2.3
  - Fixed: Creating new posebook no longer reset current pose.
  - Optimized internal pose data handling.

- 2024/07/22: v1.2.2
- Add/Replace/Duplicate Pose:
  - Fixed errors when adding / replacing pose on a armature without animation_data.
  - Automatically makes new/target pose applied after operator is executed.
- General:
  - Automatically update current pose to match pose values when changing active pose book in Poselib.
  - In Pose list, `Move Pose` operator is now disabled when there's no active pose.
  - Tweaked Pose Preview overlay text position to better visibility.
  - Better language translation for Add/Replace pose context menu.

- 2024/07/19: v1.2.1
  - Sakura Poselib panel was shown on object data tab other than Armature data (eg. Mesh data tab). It is now only on Armature data tab.
- Added 'bl_ext.blender_org.mmd_tools' to check mmd_tools, to work in Blender 4.2.

- 2024/07/18: v1.2.0
  - Added Animation Mode to support using Poselib with Blender's animation system.
    - To use it, press 'Enable Animation' button in the Book list panel.
  - Added support for Linked Library Armature object.
    - Now you can use Poselib with linked library armature object.
  - Minor bugfixes and feature improvements.

- 2024/07/16: v1.1.1
  - Pose List:
    - Added 'Duplicate Pose' function.
    - 'Add Pose' operator now inserts new pose next to the active pose.
      - This behaviour can be changed in the operator options (Insert/Append/Prepend).
  - General:
    - All features are now disalbed on Linked/Overrided Library armature objects to prevent causing errors.
      - Library armature will be supported in the future update.

- 2024/06/03 v1.1.0
  - Pose List:
    - Added 'Batch Rename Poses' function.
    - Added Display Settings. Buttons for Apply, Replace, Select Bones are now switchable.
    - Auto Set Pose Category operator now handles 'eyelid', 'eyelids' as EYE category.
    - Minor UI improvements.
  - Add Pose Operator:
    - Fixed bug where pose category was not set when creating new pose.
    - Category is now auttomatically set by using the category_filter of active pose book.
  - Preferences:
    - Added Pose List Display Settings.

- 2024/04/08 v1.0.1
  - Fixed an issue that caused error on the add-on load in MacOS/Linux. (Fixed how to handle file path)

## Disclaimer

The author is not responsible for any results from using this add-on. Please use it at your own risk.

## License

[GPL 3.0](https://www.gnu.org/licenses/gpl-3.0.html)

---

## Author

- **Kafuji Sato** - VR Character Workshop
  - [Twitter](https://twitter.com/kafuji)
  - [GitHub](https://kafuji.github.io)
  - [Fantia](https://fantia.jp/fanclubs/3967)
  - [Fanbox](https://kafuji.fanbox.cc/)
  - [Gumroad](https://kafuji.gumroad.com)
  - [Blender Market](https://blendermarket.com/creators/kafuji)

## Copyright

© 2021-2024 Kafuji Sato
