bl_info = {
	"name": "Sakura PoseLib",
	"author": "Kafuji Sato",
	"version": (1, 4, 3),
	"blender": (2, 93, 0),
	"location": "3D Viewport Side Panel -> Sakura -> Sakura PoseLib",
	"description": "Yet another pose library with handful of features",
	"warning": "",
	"doc_url": "",
	"category": "Animation",
}

# Modules (in order to load)
module_names = [
	"translation",
	"prefs",
	"spl",
	"ops",
	"panel",
	"menu",
	"hotkey",
	"handlers",
]


# Import and store modules in a list
modules = [__import__(__package__ + "." + name, fromlist=[name]) for name in module_names]

# Register & Unregister
def register():
	for module in modules:
		module.register()

def unregister():
	for module in reversed(modules):
		module.unregister()

if __name__ == "__main__":
	register()
