from typing import Optional, Callable, Union
from utils import Mode, DragMode, FrameIdent, RegionIdent
import pygame
from pygame import SRCALPHA

Surface = Union[pygame.Surface, pygame.surface.Surface]

# TODO: Put these in a common file
from os.path import expanduser
pygame.font.init()
font_path = expanduser('~/Code/Product Sans Regular.ttf')
font  = pygame.font.Font(font_path, 16)
c = type('c', (), {'__matmul__': lambda s, x: (*x.to_bytes(3, 'big'),), '__sub__': lambda s, x: (x&255,)*3})()
FRAME_WIDTH = 16
DEBUG_PAD = 0
green = c@0xa0ffe0
yellow = c@0xffffe0
black = c-0
bg = c-34

class Session:
	def __init__(self, view: 'View', paint_colour):
		self.paint_colour = paint_colour
		self.curr_tool: Optional[Callable] = None
		self.curr_mode = Mode.paint
		self.drag_mode = DragMode.none

		self.selection: Optional[Union[RegionIdent, FrameIdent]] = None
		self.hover: Optional[FrameIdent]  = None  # For highlight

		self.show_selection = False
		self.text = f'{int.from_bytes(paint_colour, "big"):06x}'

		self.clips = [view.clip]
		self.views = [view]

	def generate_lru_stack(self) -> list[int]:
		return [*range(len(self.views))]

	# def update_lru_stack(self): ...  # call when we delete a view

class Clip:  # contains frames
	def __init__(self, name: str, surf: Surface):  # TODO: accept frame list
		self.name = name
		self.frames = [surf]  # always len(frames) >= 1
		self.views: list['View'] = []

	def __getitem__(self, index):
		return self.frames[index]

	def __len__(self):
		return self.frames.__len__()

	def __contains__(self, frame_ident: Optional[FrameIdent]):
		if frame_ident is None: return False

		return (
			frame_ident.clip is self
			and frame_ident.frame in range(len(self)) # NOTE: Also acts as a None-check
		)

	def __repr__(self):
		return f'Clip {self.name!r}'

class View:  # contains a clip and how it will be rendered
	def __init__(
		self, clip, *,
		frame_panel_h,
		zoom = 1, scroll = None, frame_scroll = 0,
		tick=0, playing = False, play_fps = 24,
	):
		self.clip: Clip = clip

		self.frame_panel_h: int = frame_panel_h
		self.play_fps: int = play_fps

		self.zoom: float = zoom
		self.frame_scroll: float = frame_scroll
		self.playing: bool = playing

		if scroll is None: scroll = [0, 0]
		self.scroll: list[float] = scroll

		self.set_tick(tick)

		self.clip.views.append(self)

	def __repr__(self):
		return (
			f'View<{self.clip} @ {self.zoom:.2f}x '
			f'({self.scroll[0]:.2f}, {self.scroll[1]:.2f})>'
		)

	def set_tick(self, tick):
		self.tick: int = tick % (len(self.clip) * 1000 // self.play_fps)
		self.curr_frame: int = self.tick * self.play_fps // 1000
		print('tick', self.curr_frame, 'of', len(self.clip))

	def set_frame(self, frame: int):
		self.curr_frame = frame % len(self.clip)
		self.tick = self.curr_frame * 1000 // self.play_fps

	def from_screen_space(self, pos) -> tuple[float, float]:
		x = pos[0] * self.zoom - self.scroll[0]
		y = pos[1] * self.zoom - self.scroll[1]
		return x, y

	def to_screen_space(self, x: int, y: int):
		return (
			(x + self.scroll[0]) / self.zoom,
			(y + self.scroll[1]) / self.zoom,
		)

	def frame_from_screen_space(self, x: int) -> float:
		return (x - self.frame_scroll) / FRAME_WIDTH

	def frame_to_screen_space(self, x: int):
		return x * FRAME_WIDTH + self.frame_scroll

	def get_name(self):  # window.get_name() -> window.view.clip.name
		return self.clip.name

	def curr_surf(self):
		return self.clip[self.curr_frame]

	def curr_frame_ident(self):
		return FrameIdent(self.clip, self.curr_frame)

	def detach_from_clip(self):
		self.clip.views.remove(self)

	def copy(self):
		return self.__class__(
			self.clip,  # Don't copy this. That's the whole point.
			tick = self.tick,
			frame_panel_h = self.frame_panel_h,
			zoom = self.zoom,
			scroll = self.scroll.copy(),
			frame_scroll = self.frame_scroll,
			# playing = False,
			play_fps = self.play_fps,
		)

	def render(
		self, w, h,
		selection: Optional[Union[RegionIdent, FrameIdent]],
		hover: Optional[FrameIdent],
	):

		out = pygame.Surface((w, h))
		out.fill(bg)

		# out.fill(green, (DEBUG_PAD, DEBUG_PAD, w-DEBUG_PAD*2, h-SH-DEBUG_PAD*2))

		# represents the subsection of the frame to show
		# doesn't need to be precise, only for profromance
		# this is how big the screen is wrt obj space
		obj_space_w = (w - DEBUG_PAD*2) * self.zoom + 2
		obj_space_h = (h - DEBUG_PAD*2) * self.zoom + 2

		surf = self.curr_surf()

		# still in obj space
		crop_rect = pygame.Rect(
			(-self.scroll[0], -self.scroll[1]), (obj_space_w, obj_space_h)
		).clip(surf.get_rect())
		if crop_rect:
			# TODO: show selection region rect (yellow inside, black outside)

			cropped_surf = surf.subsurface(crop_rect)

			view_w = crop_rect.width  / self.zoom
			view_h = crop_rect.height / self.zoom
			scaled_surf = pygame.transform.scale(cropped_surf, (view_w, view_h))

			# so in obj space, the cropped_surf is at crop_rect.topleft
			# transform that to screen space
			x, y = self.to_screen_space(*crop_rect.topleft)
			out.blit(scaled_surf, (x + DEBUG_PAD, y + DEBUG_PAD))

			if (
				isinstance(selection, RegionIdent)
				and selection.frame_ident.clip is self.clip
			):
				region = selection.region.reorganised()  # type: ignore[union-attr]

				# crop the region
				x1, y1 = self.to_screen_space(*region._start)

				x2, y2 = region._end
				x2, y2 = self.to_screen_space(x2+1, y2+1)

				sel_w, sel_h = x2-x1, y2-y1

				rect = pygame.Rect(x1, y1, sel_w, sel_h).clip(out.get_rect())
				pygame.draw.rect(out, black, rect.inflate(2, 2), width=1)
				pygame.draw.rect(out, yellow, rect.inflate(4, 4), width=1)

		# selected_frame = selection and selection.frame_ident
		if selection is None: selected_frame = None
		elif isinstance(selection, FrameIdent): selected_frame = selection
		else: selected_frame = selection.frame_ident

		frame_panel_surf = self.render_frame_panel(w, selected_frame, hover)
		out.blit(frame_panel_surf, (0, h - self.frame_panel_h))

		return out

	def render_frame_panel(self, w, selection: Optional[FrameIdent], hover):

		out = pygame.Surface((w, self.frame_panel_h), SRCALPHA)

		if self.playing:
			col = green
		else:
			col = c-192

		out.fill((*c-0, 230))

		valid_frames_rect = pygame.Rect(self.frame_to_screen_space(0), 0, len(self.clip) * FRAME_WIDTH, self.frame_panel_h)
		out.fill((*c-27, 230), valid_frames_rect.clip(out.get_rect()))

		if hover in self.clip:  # NOTE: Also acts as a None-check
			# NOTE: Redundant, we should just calculate this directly
			# But then, we won't get the perfect x coord. Therefore, this is actually kinda ok.
			x = self.frame_to_screen_space(hover.frame)
			out.fill(c-50, (x, 0, FRAME_WIDTH, self.frame_panel_h))

		if selection in self.clip:
			# NOTE: Redundant, we should just calculate this directly
			# But then, we won't get the perfect x coord. Therefore, this is actually kinda ok.
			x = self.frame_to_screen_space(selection.frame)  # type: ignore[union-attr]
			out.fill(c-192, (x, 0, FRAME_WIDTH, self.frame_panel_h))

		x = self.frame_to_screen_space(self.curr_frame)

		out.fill(col, (x, 0, 1, self.frame_panel_h))

		frame_n_surface = font.render(f'{self.curr_frame}', True, col)
		out.blit(frame_n_surface, (x, 0))

		return out
