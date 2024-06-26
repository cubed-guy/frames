# A beautiful thing in programming is that if you make it perfect, you never have to think about it ever again.

# paint and frames
# DONE: view
# DONE: scroll and zoom
# DONE: paint - pick colour, type hex
# DONE: frames
# DONE: select
# DONE: views
# DONE: lru_indirection
# DONE: multiclip support, new clip from selection
# DONE: new clip from clipboard
# TODO: text?
# TODO: multiarg tool support
# TODO: new blank clip (requires multiargs for dimensions)
# TODO: preview
# TODO: layouts

from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = 'hide'

from PIL import ImageGrab, Image
from PIL.PngImagePlugin import PngImageFile as PilPng
from PIL.BmpImagePlugin import DibImageFile as PilDib
from typing import Union
from os.path import expanduser
import numpy as np
from utils import DragMode, Mode, Region, RegionIdent, FrameIdent
from views import View, Clip, Session
import tools

import pygame
from pygame import (
	KEYDOWN, KEYUP, QUIT, VIDEORESIZE,
	MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION, MOUSEWHEEL,
	KMOD_LALT, KMOD_LCTRL, KMOD_LSHIFT, KMOD_RALT, KMOD_RCTRL, KMOD_RSHIFT,
	K_LCTRL, K_RCTRL, K_LSHIFT, K_RSHIFT,
	K_BACKSPACE, K_END, K_ESCAPE, K_TAB, K_F11, K_HOME, K_KP1, K_KP7, K_F4,
	K_LEFT, K_RETURN, K_RIGHT, K_SPACE, K_BACKSLASH, K_SLASH,
	K_b, K_c, K_d, K_e, K_f, K_g, K_k, K_n, K_s, K_v, K_x,
	RESIZABLE, FULLSCREEN,
)
pygame.font.init()
font_path = expanduser('~/Code/Product Sans Regular.ttf')
font  = pygame.font.Font(font_path, 16)
sfont = pygame.font.Font(font_path, 12)

c = type('c', (), {'__matmul__': lambda s, x: (*x.to_bytes(3, 'big'),), '__sub__': lambda s, x: (x&255,)*3})()
# c = type('c', (), {'__matmul__': lambda s, x: pygame.Color(x), '__sub__': lambda s, x: pygame.Color((x&255,)*3)})()
bg = c-34
fg = c@0xff9088
green = c@0xa0ffe0
yellow = c@0xffffe0
black = c-0
SH = 20

fps = 60

ZOOM_FAC = 0.8
MIN_ZOOM = 0.002

w, h = res = (1280, 720)

def updateStat(msg, update = True):
	# call this if you have a long loop that'll taking too long
	rect = (0, h-SH, w, 21)

	display.fill(c-0, rect)

	tsurf = sfont.render(f'{msg}', True, c--1)
	display.blit(tsurf, (5, h-SH))

	if update: pygame.display.update(rect)

display: Union[pygame.Surface, pygame.surface.Surface]  # A single annotation can't hurt
def resize(size):
	global w, h, res, display
	w, h = res = size
	display = pygame.display.set_mode(res, RESIZABLE)
	updateDisplay()

def updateDisplay():
	if session.show_selection: selection = session.selection
	else: selection = None
	view_surf = curr_view.render(w, h, selection, session.hover)

	display.blit(view_surf, (0, 0))  # TODO: Use layout

	updateStat(
		f'{view_idx} of {len(lru_stack)} -> {curr_view} '
		f'in {session.curr_mode} and {session.drag_mode}, '
		f'text: {session.text}',
		update = False,
	)
	pygame.display.flip()

def toggleFullscreen():
	global pres, res, w, h, display
	res, pres =  pres, res
	w, h = res
	if display.get_flags()&FULLSCREEN: resize(res)
	else: display = pygame.display.set_mode(res, FULLSCREEN); updateDisplay()

def start_selection(pos):
	# TODO: move this to Session

	x, y = curr_view.from_screen_space(pos)
	x, y = int(x), int(y)

	surf = curr_view.curr_surf()
	if not surf.get_rect().collidepoint((x, y)):
		# print('Rect start out of bounds')
		return

	session.drag_mode = DragMode.pixel_region_select
	session.show_selection = True

	region = Region((x, y), (x, y))
	session.selection = RegionIdent(curr_view.clip, curr_view.curr_frame, region)

	# print('Rectangle starting from', session.selection.region._start)

# TODO: Move to Window class
view_idx: int
def update_curr_view(lru_idx):
	global view_idx, curr_view
	view_idx = lru_stack[lru_idx]
	curr_view = session.views[view_idx]

# TODO: Move to Window class
def new_lru_view(new_view_idx):  # Adds a new view to the lru stack and changes the current view as well
	global lru_idx, lru_stack, view_idx, curr_view
	view_idx = new_view_idx
	curr_view = session.views[view_idx]

	lru_stack.append(new_view_idx)
	lru_idx = len(lru_stack)-1

# TODO: Move to Window class
def reset_lru():
	global lru_stack, lru_idx

	lru_stack.append(lru_stack.pop(lru_idx))
	lru_idx = len(lru_stack)-1
	# don't update_curr_view because view_idx is unchanged

valid_chars = {
	Mode.type_colour: set('0123456789abcdefABCDEF'),
}

# TODO: frame in view{frames} in session{views}
surf = pygame.image.load('berries.jpg')
# We don't do this here.
# We'll take the reference when we perform operations.
# frame = pygame.surfarray.pixels3d(surf)

# array of surfaces... would it be more efficient to store a single 3d/4d array?
# access the surface from array rather than the other way around...
# Apparently, that's not a thing. We'll do it like this only then.

clip = Clip('berries', surf)
curr_view = View(
	clip, frame_panel_h = 100,
)

session = Session(
	curr_view,
	paint_colour = c--1
)

# TODO: move this to Window
# The lru has to be specific to the window right
# The actual View list will be constant and part of the Session
lru_stack = session.generate_lru_stack()  # this will be in Window.__init__()
lru_idx = len(lru_stack)-1
update_curr_view(lru_idx)

resize(res)
pres = pygame.display.list_modes()[0]
pygame.key.set_repeat(500, 50)
clock = pygame.time.Clock()
running = True
while running:
	for event in pygame.event.get():
		if event.type == KEYDOWN:
			if event.key == K_F11: toggleFullscreen()

			elif session.curr_mode is Mode.type_colour:
				if event.mod & (KMOD_LCTRL|KMOD_RCTRL):
					if event.key == K_BACKSPACE:
						split = session.text.rsplit(maxsplit=1)
						if len(split) <= 1: session.text = ''
						else: session.text = split[0]
				elif event.key == K_BACKSPACE:
					session.text = session.text[:-1]
				elif event.key == K_RETURN:
					if session.curr_mode is Mode.type_colour:
						session.paint_colour = c@int(session.text[-6:], 16)
						session.text = f'{int.from_bytes(session.paint_colour, "big"):06x}'
					session.curr_mode = Mode.paint

				elif event.key == K_ESCAPE:
					if session.curr_mode is Mode.type_colour:
						session.text = f'{int.from_bytes(session.paint_colour, "big"):06x}'
					session.curr_mode = Mode.paint

				elif event.unicode and event.unicode in valid_chars[session.curr_mode]:
					session.text += event.unicode

			elif event.key == K_TAB:  # to change views
				if event.mod & (KMOD_LCTRL|KMOD_RCTRL):
					if event.mod & (KMOD_LSHIFT|KMOD_RSHIFT):
						lru_idx += 1
					else:
						lru_idx -= 1

					lru_idx %= len(lru_stack)
					update_curr_view(lru_idx)

			elif event.key == K_ESCAPE:
				if event.mod & (KMOD_LSHIFT|KMOD_RSHIFT):
					session.show_selection = False  # shift+s to show

				elif session.curr_mode is not Mode.paint:
					session.curr_mode = Mode.paint

				# else:
				# 	running = False

			elif event.key == K_c: # c for colour
				session.curr_mode = Mode.type_colour
				session.curr_tool = None
			elif event.key == K_s:
				if event.mod & (KMOD_LSHIFT|KMOD_RSHIFT):
					session.show_selection = True  # shift+esc to hide
				else:
					session.curr_mode = Mode.frame_select  # s for select
				session.curr_tool = None
			elif event.key == K_b:
				if event.mod & (KMOD_LSHIFT|KMOD_RSHIFT):
					session.show_selection = True  # shift+esc to hide
				else:
					session.curr_mode = Mode.pixel_region_select  # b for box
				session.curr_tool = None
			elif event.key == K_SPACE: curr_view.playing = not curr_view.playing

			elif event.key == K_LEFT:
				curr_view.set_frame(curr_view.curr_frame-1)
				curr_view.playing = False
			elif event.key == K_RIGHT:
				curr_view.set_frame(curr_view.curr_frame+1)
				curr_view.playing = False
			elif event.key in (K_HOME, K_KP7):
				curr_view.set_frame(0)
				curr_view.playing = False
			elif event.key in (K_END, K_KP1):
				curr_view.set_frame(-1)
				curr_view.playing = False

			# View manip (not really tools... yet)
			elif event.key == K_BACKSLASH:  # no ctrl, just direct.
				curr_view = curr_view.copy()
				session.views.append(curr_view)
				lru_stack.append(len(session.views)-1)  # new view_idx
				lru_idx = len(lru_stack) - 1
				update_curr_view(lru_idx)
				print(lru_stack)

			elif event.key == K_SLASH:
				# delete from lru_stack
				# the view is still maintained in the Session object
				# TODO: delete from session and update all lru_stacks

				if len(lru_stack) <= 1: continue  # ensure at least 1 view
				lru_stack.pop(lru_idx)
				print('detaching view', view_idx)
				print(lru_stack)
				curr_view.detach_from_clip()
				lru_idx %= len(lru_stack)
				update_curr_view(lru_idx)
			
			# TOOLS!

			# Instant tools (act directly on current state)
			elif event.key == K_n:  # Instant tools need not be too ergonomic
				if event.mod & (K_LSHIFT|K_RSHIFT):
					if (
						session.show_selection
						and isinstance(session.selection, RegionIdent)
					):
						clip = tools.new_clip(session)
						session.views.append(
							View(
								clip,
								zoom=curr_view.zoom,
								frame_panel_h=curr_view.frame_panel_h,
							)
						)
						new_lru_view(new_view_idx=len(session.views)-1)
					else:
						session.curr_mode = Mode.region_extract
						session.curr_tool = tools.new_clip
				else:
					curr_view.set_frame(tools.new_frame(curr_view.clip, curr_view.curr_frame))

			elif event.key == K_v:
				if event.mod & (KMOD_LCTRL|KMOD_RCTRL):  # paste
					cb_img = ImageGrab.grabclipboard()

					if not isinstance(cb_img, (PilPng, PilDib)): continue

					surf = pygame.image.fromstring(
						cb_img.tobytes(),  # type: ignore[arg-type]  # mypy wants a string here for some reason
						cb_img.size,
						cb_img.mode,       # type: ignore[arg-type]  # we have to trust it's the correct literal
					)

					clip = Clip(f'cb image {len(session.clips)}', surf)
					session.views.append(
							View(
								clip,
								zoom=curr_view.zoom,
								frame_panel_h=curr_view.frame_panel_h,
							)
						)
					new_lru_view(new_view_idx=len(session.views)-1)

			elif event.key == K_k:
				curr_view.set_frame(tools.delete_curr_frame(curr_view.clip, curr_view.curr_frame))

			# Direct/semi-modal tools (go to selection mode if no selection)
			elif event.key == K_x:
				# TODO: `handle_mode[mode].segment_i(...)` idk
				if session.selection is None or not session.show_selection:
					session.curr_tool = tools.delete_frame
					session.curr_mode = Mode.attached[session.curr_tool]
				else:
					if isinstance(session.selection, RegionIdent):
						frame = session.selection.frame_ident.frame
					else:
						frame = session.selection.frame

					curr_view.set_frame(
						tools.delete_frame(curr_view.clip, frame, curr_view.curr_frame)
					)

			# Modal tools (go to custom mode for more selections)
			elif event.key == K_g:
				session.curr_tool = tools.move_frame
				session.curr_mode = Mode.attached[session.curr_tool]
				session.drag_mode = DragMode.none

			elif event.key == K_d:
				if event.mod & (KMOD_LSHIFT|KMOD_RSHIFT):
					session.curr_tool = tools.copy_frame
				else:
					session.curr_tool = tools.copy_region
				session.curr_mode = Mode.attached[session.curr_tool]
				session.drag_mode = DragMode.none

			# TODO: move to semi-modal section
			elif event.key == K_f: # region direct tool
				if session.selection is None or not session.show_selection:
					session.curr_tool = tools.fill
					session.curr_mode = Mode.attached[session.curr_tool]
					session.drag_mode = DragMode.none
				else:
					tools.fill(
						curr_view.curr_surf(), session.paint_colour, session.selection.region  # type: ignore[union-attr]
					)

			# TODO: move to semi-modal section
			elif event.key == K_e: # region direct tool
				if session.selection is None or not session.show_selection:
					session.curr_tool = tools.ellipse
					session.curr_mode = Mode.attached[session.curr_tool]
					session.drag_mode = DragMode.none
				else:
					tools.ellipse(
						curr_view.curr_surf(), session.paint_colour, session.selection.region  # type: ignore[union-attr]
					)

		elif event.type == KEYUP:
			if event.key in (K_LCTRL, K_RCTRL) and (lru_idx+1)%len(lru_stack):
				# curr_view stays the same
				reset_lru()
				print(lru_stack)

		elif event.type == VIDEORESIZE:
			if not display.get_flags()&FULLSCREEN: resize(event.size)
		elif event.type == QUIT: running = False
		elif event.type == MOUSEWHEEL:
			mods = pygame.key.get_mods()
			mouse_pos = pygame.mouse.get_pos()

			if mouse_pos[1] > h-SH - curr_view.frame_panel_h:  # mousewheel event to frame panel
				if mods & (KMOD_LSHIFT|KMOD_RSHIFT):
					dx, _dy = -event.y, event.x
				else:
					dx, _dy = event.x, -event.y

				curr_view.frame_scroll -= dx * 7

			elif mods & (KMOD_LCTRL|KMOD_RCTRL):
				old_obj_space_mouse = curr_view.from_screen_space(mouse_pos)
				# the diff that we had here
				curr_view.zoom *= ZOOM_FAC ** event.y
				curr_view.zoom = max(MIN_ZOOM, curr_view.zoom)

				# center at mouse
				new_obj_space_mouse = curr_view.from_screen_space(mouse_pos)
				curr_view.scroll[0] += new_obj_space_mouse[0] - old_obj_space_mouse[0]
				curr_view.scroll[1] += new_obj_space_mouse[1] - old_obj_space_mouse[1]

			else:
				curr_view.scroll[0] -= event.x * curr_view.zoom * 12
				curr_view.scroll[1] += event.y * curr_view.zoom * 12

		elif event.type == MOUSEBUTTONDOWN:
			if event.button == 3:
				session.drag_mode = DragMode.scrolling

			elif event.button == 1:
				# intentional double space. don't touch.
				print('MOUSEDOWN  FRAME', session.hover, session.curr_mode, session.drag_mode)

				x, y = curr_view.from_screen_space(event.pos)
				x, y = int(x), int(y)

				mods = pygame.key.get_mods()
				if mods & (KMOD_LALT|KMOD_RALT):
					if session.hover is not None: continue  # mouse on panel
					session.paint_colour = surf.get_at((x, y))
					session.text = f'{int.from_bytes(session.paint_colour, "big"):06x}'

				elif session.curr_mode == Mode.paint:
					if session.hover in curr_view.clip:  # wrap-around would be weird
						curr_view.set_frame(session.hover.frame)  # type: ignore[union-attr]
						session.drag_mode = DragMode.scrub
						continue

					if session.hover is not None: continue  # mouse on panel

					surf = curr_view.curr_surf()
					if not surf.get_rect().collidepoint((x, y)): continue

					session.drag_mode = DragMode.default

					surf.set_at((x, y), session.paint_colour)

				elif session.curr_mode in (
					Mode.frame_select, Mode.frame_direct
				):
					if session.hover in curr_view.clip:
						session.show_selection = True
						session.selection = FrameIdent(
							session.hover.clip, session.hover.frame  # type: ignore[union-attr]
						)
						# don't start scrub because we need selection not view

				elif session.curr_mode == Mode.frame_dest:
					if session.hover not in curr_view.clip: continue

					if not session.show_selection or session.selection is None:
						session.show_selection = True

						# simulates click-drag
						# NOTE: beware of mutability
						session.selection = session.hover

					curr_view.set_frame(session.hover.frame)  # type: ignore[union-attr]
					session.drag_mode = DragMode.scrub

				elif session.curr_mode in (
					Mode.pixel_region_select, Mode.region_direct,
					Mode.fill, Mode.region_extract,
				):
					if session.hover is not None:
						if session.hover in curr_view.clip:
							session.drag_mode = DragMode.scrub
							curr_view.set_frame(session.hover.frame)

					else:
						start_selection(event.pos)

				elif session.curr_mode == Mode.pixel_dest:
					if session.hover is not None:
						if session.hover in curr_view.clip:
							session.drag_mode = DragMode.scrub
							curr_view.set_frame(session.hover.frame)

					elif not session.show_selection or session.selection is None:
						start_selection(event.pos)

					else:
						session.drag_mode = DragMode.default  # apply on mouse up

				else:  # type_colour
					updateStat(f'Unsupported mode {session.curr_mode} for mouse down')
					print(f'Unsupported mode {session.curr_mode} for mouse down')

		elif event.type == MOUSEBUTTONUP:
			if event.button == 3:
				if session.drag_mode is DragMode.scrolling:
					session.drag_mode = DragMode.none

			elif event.button == 1:
				print('MOUSEUP ON FRAME', session.hover, session.curr_mode, session.drag_mode)

				# No tool

				if session.curr_tool is None:
					# paint, type_colour, frame_select, pixel_region_select
					# drag_mode can be scrub in pixel_region_select mode
					if session.drag_mode is not DragMode.scrub: session.curr_mode = Mode.paint
					session.drag_mode = DragMode.none
					continue

				# Direct tools (already applied, or applied on mouse up)

				elif session.curr_mode is Mode.frame_direct:
					# mouseup on frame_direct must have a selection
					# ... unless we get a sole mouseup event, ignore for now
					frame_ident = session.selection.frame_ident  # type: ignore[union-attr]

					# Also handles multiclip
					if session.hover not in frame_ident.clip: continue

					curr_view.set_frame(
						session.curr_tool(
							frame_ident.clip,
							frame_ident.frame,
							session.hover.frame,  # type: ignore[union-attr]
						)
					)

				elif session.curr_mode is Mode.region_direct:
					# mouseup on region_direct must have a selection
					# ... unless we get a sole mouseup event, ignore for now
					session.curr_tool(
						curr_view.curr_surf(), session.selection.region  # type: ignore[union-attr]
					)

				elif session.curr_mode is Mode.fill:
					# mouseup on fill must have a selection
					# ... unless we get a sole mouseup event, ignore for now
					session.curr_tool(
						curr_view.curr_surf(),
						session.selection.region,  # type: ignore[union-attr]
						session.paint_colour
					)

				elif session.curr_mode is Mode.region_extract:
					print('MOUSEUP FOR REGION EXTRACT')
					# mouseup on region_extract must have a selection
					# ... unless we get a sole mouseup event, ignore for now
					clip = session.curr_tool(session)
					session.views.append(
						View(
							clip,
							zoom=curr_view.zoom,
							frame_panel_h=curr_view.frame_panel_h,
						)
					)
					new_lru_view(new_view_idx=len(session.views)-1)

				# Fully modal tools. Apply the tool on mouse up. TODO: preview

				elif session.curr_mode is Mode.frame_dest:
					if session.drag_mode is not DragMode.scrub: continue

					print(session.curr_tool, session.hover, session.selection)
					session.curr_tool(session.hover, session.selection.frame_ident)  # type: ignore[union-attr]

				elif session.curr_mode is Mode.pixel_dest:
					if session.drag_mode in (
						DragMode.pixel_region_select, DragMode.scrub
					):
						session.drag_mode = DragMode.none
						continue  # keep selection

					print('Pixel dest')

					x, y = curr_view.from_screen_space(event.pos)
					pixel = int(x), int(y)
					# # copy_region() can handle out of bounds dest
					# if not frames[curr_frame].get_rect().collidepoint(pixel):
					# 	continue

					# session.selection should be a RegionIdent here
					# because drag_mode not in (region_select, scrub)
					session.curr_tool(
						curr_view.curr_frame_ident(), pixel,
						session.selection.frame_ident,  # type: ignore[union-attr]
						session.selection.region,       # type: ignore[union-attr]
					)

				else:  # paint, type_colour, frame_select, pixel_region_select
					updateStat('Unknown mode')

				session.curr_tool = None
				session.curr_mode = Mode.paint
				session.show_selection = False
				session.drag_mode = DragMode.none

		elif event.type == MOUSEMOTION:
			if session.drag_mode is DragMode.none:
				session.hover = None

				# TODO: use curr_view position
				if event.pos[1] >= h-SH - curr_view.frame_panel_h:
					hovered_frame = curr_view.frame_from_screen_space(event.pos[0])
					session.hover = FrameIdent(curr_view.clip, int(hovered_frame))

			elif session.drag_mode is DragMode.scrub:
				# TODO: offset event.pos with layout

				# TODO: use curr_view position
				hovered_frame = curr_view.frame_from_screen_space(event.pos[0])
				session.hover = FrameIdent(curr_view.clip, int(hovered_frame))

				if session.hover in curr_view.clip:
					curr_view.set_frame(session.hover.frame)

			elif session.drag_mode is DragMode.pixel_region_select:
				x, y = curr_view.from_screen_space(event.pos)
				x, y = int(x), int(y)

				surf = curr_view.curr_surf()
				if not surf.get_rect().collidepoint((x, y)): continue

				session.selection.region.set_end((x, y))  # type: ignore[union-attr]

			elif session.drag_mode is DragMode.scrolling:
				curr_view.scroll[0] += event.rel[0] * curr_view.zoom
				curr_view.scroll[1] += event.rel[1] * curr_view.zoom

			elif session.curr_mode is Mode.paint:
				x, y = curr_view.from_screen_space(event.pos)
				x, y = int(x), int(y)

				surf = curr_view.curr_surf()
				if not surf.get_rect().collidepoint((x, y)): continue

				surf.set_at((x, y), session.paint_colour)

	updateDisplay()
	frame_time = clock.tick(fps)

	for view in session.views:
		if curr_view.playing:
			curr_view.set_tick(curr_view.tick + frame_time)
