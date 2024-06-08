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
	pixel_select = auto()

	# tool modes
	# attach these to functions to annotate required function signature
	frame_dest = auto()  # (&mut frames, dst_frame, src_frame) -> None
	frame_direct = auto()  # (&mut frames, target_frame, curr_frame) -> new_frame  # applies directly if there is already a selection
	pixel_dest = auto()  # (&mut frames, target_frame, dst_pixel, src_frame, src_rect) -> None

	# separate mode just for fill
	fill = auto()  # (&mut surf, rect, colour) -> None  # applies directly if there is already a selection

class Region:
	def __init__(self, start: tuple[int, int], end: tuple[int, int]):
		self._start = start
		self._end = end
		print('end set to', end)

		self._reorganised = None

	def __bool__(self):
		return self._start != None != self._end

	def __repr__(self):
		return f'Region({self._start} to {self._end})'

	def set_end(self, end):
		self._end = end
		print('end updated to', end)
		self._reorganised = None

	def set_start(self, start):
		self._start = start
		self._reorganised = None

	def reorganised(self):
		if self._reorganised is not None: return self._reorganised

		x1, y1 = self._start
		print('trying to unpack', self._end)
		x2, y2 = self._end

		if x2 < x1: x1, x2 = x2, x1
		if y2 < y1: y1, y2 = y2, y1

		self._reorganised = self.__class__((x1, y1), (x2, y2))
		return self._reorganised

	def as_rect(self):
		region = self.reorganised()
		x1, y1 = region._start
		x2, y2 = region._end

		return x1, y1, x2-x1, y2-y1
