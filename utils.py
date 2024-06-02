from enum import Enum, auto

class AttachedEnum(Enum):
	'''
	Contains a dict with mapping of decorated functions
	to their corresponding enum variants.
	'''

	def __init_subclass__(cls):
		cls.attached = {}

	def attach(self, fn):  # decorator names are usually adjectives
		self.attached[fn] = self
		return fn

class Mode(AttachedEnum):
	paint = auto()
	type_colour = auto()
	frame_select = auto()

	# tool modes
	# attach these to functions to annotate required function signature
	frame_dest = auto()  # (&mut frames, dst_frame, src_frame) -> None
