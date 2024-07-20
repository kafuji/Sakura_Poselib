# Sakura Poselib

![keyart](img/keyart.png)

***Yet another pose library with a lot of handy features.***

## Overview

- Adds simple and handy pose libraries to armatures.
- Quickly add/update/preview poses form context menu.
- Blend multiple poses with sliders.
- Supports Blender's animation system. Keyframe your poses to make character animations!
- Compatible with mmd_tools, PMX Editor via import/export functions.

## Online Document

- [English](https://kafuji.github.io/Sakura-Creative-Suite/en/addons/Sakura_PoseLib/)
- [日本語](https://kafuji.github.io/Sakura-Creative-Suite/ja/addons/Sakura_PoseLib/)

## Change Log

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

[MIT License](https://opensource.org/license/mit)

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

© 2021 Kafuji Sato, All rights reserved.
