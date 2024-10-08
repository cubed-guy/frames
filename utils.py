from enum import Enum, auto
from typing import Optional, Callable, TYPE_CHECKING, TypeVar, Union
import pygame
if TYPE_CHECKING:
	from views import Clip

Surface = Union[pygame.Surface, pygame.surface.Surface]
F = TypeVar('F')

class AttachedEnum(Enum):
	'''
	Contains a dict with mapping of decorated functions
	to their corresponding enum variants.
	'''

	attached: dict

	def __init_subclass__(cls):
		cls.attached = {}

	def attach(self, fn: F) -> F:  # decorator names are usually adjectives
		self.attached[fn] = self
		return fn

class Mode(AttachedEnum):
	__getitem__: Callable[..., 'Mode']  # Just an annotation can't hurt.

	type_colour = auto()
	type_text = auto()
	type_number = auto()

	paint = auto()
	frame_select = auto()  # click to set only selected, not playhead
	pixel_region_select = auto()

	# tool modes
	# attach these to functions to annotate required function signature
	frame_dest = auto()
	frame_direct = auto()  # applies directly if selection exists
	pixel_dest = auto()
	region_direct = auto()  # applies directly if selection is a region
	region_extract = auto()  # applies directly if selection is a region
	fill = auto()  # applies directly if selection is a region

class DragMode(Enum):
	none = auto()
	scrolling = auto()
	default = auto()  # default drag mode for either frame panel or viewport
	scrub = auto()  # used to select current frame
	pixel_region_select = auto()  # while making a selection
	# frame_region_select = auto()

class FrameIdent:
	def __init__(self, clip: 'Clip', frame: int):
		self.clip = clip
		self.frame = frame

	def frame_surf(self) -> Surface:
		return self.clip.surf_at(self.frame)

class RegionIdent:
	def __init__(self, clip: 'Clip', frame: int, region: 'Region'):
		self.frame_ident = FrameIdent(clip, frame)
		self.region = region

	def __bool__(self):
		return not not self.region

	def __repr__(self):
		return f'RegionIdent({self.frame_ident.clip}, {self.frame_ident.frame}, {self.region})'

class Region:
	def __init__(self, start: tuple[int, int], end: tuple[int, int]):
		self._start = start
		self._end = end
		print('end set to', end)

		self._reorganised: Optional[Region] = None

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

	def reorganised(self) -> 'Region':
		if self._reorganised is not None: return self._reorganised

		x1, y1 = self._start
		print('trying to unpack', self._end)
		x2, y2 = self._end

		if x2 < x1: x1, x2 = x2, x1
		if y2 < y1: y1, y2 = y2, y1

		self._reorganised = self.__class__((x1, y1), (x2, y2))
		return self._reorganised

	def as_rect(self) -> tuple[int, int, int, int]:
		region = self.reorganised()
		x1, y1 = region._start
		x2, y2 = region._end

		return x1, y1, x2-x1, y2-y1
