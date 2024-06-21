# A beautiful thing in programming is that if you make it perfect, you never have to think about it ever again.

# paint and frames
# DONE: view
# DONE: scroll and zoom
# DONE: paint - pick colour, type hex
# DONE: frames
# DONE: select
# TODO: views
# TODO: text?
# TODO: multiarg tool support

from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = 'hide'

from os.path import expanduser
import numpy as np
import tools
from utils import Mode, Region

from enum import Enum, auto
import pygame
from pygame.locals import *
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
play_fps = 24

DEBUG_PAD = 0
ZOOM_FAC = 0.8
MIN_ZOOM = 0.002
FRAME_WIDTH = 16

w, h = res = (1280, 720)

PAINT_STAT  = c@0x800080
COLOUR_STAT = c-0
SELECT_STAT = c--1
FRAME_STAT = c@0x800000
UNKNOWN_STAT = c@0xff00ff

def updateStat(msg, update = True):
	# call this if you have a long loop that'll taking too long
	rect = (0, h-SH, w, 21)

	# if   curr_mode is Mode.paint: col = PAINT_STAT
	# elif curr_mode is Mode.type_colour: col = COLOUR_STAT
	# elif curr_mode is Mode.frame_select: col = SELECT_STAT
	# elif curr_mode is Mode.frame_dest: col = FRAME_STAT
	# else: col = UNKNOWN_STAT

	display.fill(c-0, rect)

	tsurf = sfont.render(f'{msg}', True, c--1)
	display.blit(tsurf, (5, h-SH))

	if update: pygame.display.update(rect)

def resize(size):
	global w, h, res, display
	w, h = res = size
	display = pygame.display.set_mode(res, RESIZABLE)
	updateDisplay()

def updateDisplay():
	display.fill(bg)

	# display.fill(green, (DEBUG_PAD, DEBUG_PAD, w-DEBUG_PAD*2, h-SH-DEBUG_PAD*2))

	# scale, first subsurf

	# represents the subsection of the frame to show
	# doesn't need to be precise, only for profromance
	# this is how big the screen is wrt obj space
	obj_space_w = (w - DEBUG_PAD*2) * zoom + 2
	obj_space_h = (h - SH - DEBUG_PAD*2) * zoom + 2

	surf = frames[curr_frame]

	# still in obj space
	crop_rect = pygame.Rect(
		(-scroll[0], -scroll[1]), (obj_space_w, obj_space_h)
	).clip(surf.get_rect())
	if crop_rect:
		# TODO: show selection region rect (yellow inside, black outside)

		cropped_surf = surf.subsurface(crop_rect)

		view_w = crop_rect.width  / zoom
		view_h = crop_rect.height / zoom
		scaled_surf = pygame.transform.scale(cropped_surf, (view_w, view_h))

		# so in obj space, the cropped_surf is at crop_rect.topleft
		# transform that to screen space
		x, y = to_screen_space(*crop_rect.topleft)
		display.blit(scaled_surf, (x + DEBUG_PAD, y + DEBUG_PAD))

		if show_selection and selected_region:
			region = selected_region.reorganised()

			# crop the region
			x1, y1 = to_screen_space(*region._start)

			x2, y2 = region._end
			x2, y2 = to_screen_space(x2+1, y2+1)

			sel_w, sel_h = x2-x1, y2-y1

			rect = pygame.Rect(x1, y1, sel_w, sel_h).clip(display.get_rect())
			pygame.draw.rect(display, black, rect.inflate(2, 2), width=1)
			pygame.draw.rect(display, yellow, rect.inflate(4, 4), width=1)
	
	frame_panel_surf = render_frame_panel()
	display.blit(frame_panel_surf, (0, h - SH - frame_panel_h))

	updateStat(f'{curr_mode}, {drag_mode}, #{text[-6:]}', update = False)
	pygame.display.flip()

def toggleFullscreen():
	global pres, res, w, h, display
	res, pres =  pres, res
	w, h = res
	if display.get_flags()&FULLSCREEN: resize(res)
	else: display = pygame.display.set_mode(res, FULLSCREEN); updateDisplay()

def from_screen_space(pos):
	x = pos[0] * zoom - scroll[0]
	y = pos[1] * zoom - scroll[1]
	return x, y

def to_screen_space(x, y):
	return (x + scroll[0]) / zoom, (y + scroll[1]) / zoom

def frame_from_screen_space(x):
	global frame_scroll

	return (x - frame_scroll) / FRAME_WIDTH

def frame_to_screen_space(x):
	global frame_scroll

	return x * FRAME_WIDTH + frame_scroll

class DragMode(Enum):
	none = auto()
	scrolling = auto()
	default = auto()  # default drag mode for either frame panel or viewport
	scrub = auto()  # used to select current frame
	pixel_region_select = auto()  # while making a selection
	# frame_region_select = auto()

def render_frame_panel():
	global frame_panel_h, curr_frame, frame_scroll, hovered_frame, selected_frame

	out = pygame.Surface((w, frame_panel_h), SRCALPHA)

	if playing:
		col = green
	else:
		col = c-192

	out.fill((*c-0, 230))

	valid_frames_rect = pygame.Rect(frame_to_screen_space(0), 0, len(frames) * FRAME_WIDTH, frame_panel_h)
	out.fill((*c-27, 230), valid_frames_rect.clip(out.get_rect()))

	if hovered_frame in range(len(frames)):  # NOTE: Also acts as a None-check
		# NOTE: Redundant, we should just calculate this directly
		# But then, we don't get the perfect x coord. Therefore, this is actually kinda ok.
		x = frame_to_screen_space(hovered_frame)
		out.fill(c-50, (x, 0, FRAME_WIDTH, frame_panel_h))

	if show_selection and selected_frame in range(len(frames)):  # NOTE: Also acts as a None-check
		# NOTE: Redundant, we should just calculate this directly
		# But then, we don't get the perfect x coord. Therefore, this is actually kinda ok.
		x = frame_to_screen_space(selected_frame)
		out.fill(c-192, (x, 0, FRAME_WIDTH, frame_panel_h))

	x = frame_to_screen_space(curr_frame)

	out.fill(col, (x, 0, 1, frame_panel_h))

	frame_n_surface = font.render(f'{curr_frame}', True, col)
	out.blit(frame_n_surface, (x, 0))

	return out

def set_frame(frame):
	global ticks, curr_frame

	curr_frame = frame % len(frames)
	ticks = curr_frame * 1000 // play_fps

def start_selection(pos):
	global selected_region, drag_mode, selected_frame, show_selection

	x, y = from_screen_space(pos)
	x, y = int(x), int(y)

	surf = frames[curr_frame]
	if not surf.get_rect().collidepoint((x, y)):
		# print('Rect start out of bounds')
		return

	drag_mode = DragMode.pixel_region_select
	show_selection = True
	selected_frame = curr_frame

	selected_region = Region((x, y), (x, y))
	# print('Rectangle starting from', selected_region._start)


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

frame_panel_h = 100

scroll = [0, 0]  # object space
zoom = 1
curr_mode = Mode.paint
curr_tool = None
paint_colour = c-0
frame_scroll = 0
playing = False
drag_mode = DragMode.none
ticks = 0

frames: list[pygame.Surface] = [surf.copy() for i in range(16)]
curr_frame = 0
hovered_frame  = None  # For highlight
selected_frame = None  # TODO: frame range
selected_region = None
show_selection = False
text = f'{int.from_bytes(paint_colour, "big"):06x}'

resize(res)
pres = pygame.display.list_modes()[0]
pygame.key.set_repeat(500, 50)
clock = pygame.time.Clock()
running = True
while running:
	for event in pygame.event.get():
		if event.type == KEYDOWN:
			if event.key == K_F11: toggleFullscreen()

			elif curr_mode is Mode.type_colour:
				if event.mod & (KMOD_LCTRL|KMOD_RCTRL):
					if event.key == K_BACKSPACE:
						split = text.rsplit(maxsplit=1)
						if len(split) <= 1: text = ''
						else: text = split[0]
				elif event.key == K_BACKSPACE:
					text = text[:-1]
				elif event.key == K_RETURN:
					if curr_mode is Mode.type_colour:
						paint_colour = c@int(text[-6:], 16)
						text = f'{int.from_bytes(paint_colour, "big"):06x}'
					curr_mode = Mode.paint

				elif event.key == K_ESCAPE:
					if curr_mode is Mode.type_colour:
						text = f'{int.from_bytes(paint_colour, "big"):06x}'
					curr_mode = Mode.paint

				elif event.unicode and event.unicode in valid_chars[curr_mode]:
					text += event.unicode

			elif event.key == K_ESCAPE:
				# TODO: Separate keybinds for paint mode and deselection
				if event.mod & (KMOD_LSHIFT|KMOD_RSHIFT):
					show_selection = False  # shift+s to show

				elif curr_mode is not Mode.paint:
					curr_mode = Mode.paint

				else:
					running = False
			elif event.key == K_c: # c for colour
				curr_mode = Mode.type_colour
				curr_tool = None
			elif event.key == K_s:
				if event.mod & (KMOD_LSHIFT|KMOD_RSHIFT):
					show_selection = True  # shift+esc to hide
				else:
					curr_mode = Mode.frame_select  # s for select
				curr_tool = None
			elif event.key == K_b:
				if event.mod & (KMOD_LSHIFT|KMOD_RSHIFT):
					show_selection = True  # shift+esc to hide
				else:
					curr_mode = Mode.pixel_region_select  # b for box
				curr_tool = None
			elif event.key == K_SPACE: playing = not playing

			elif event.key == K_LEFT:  set_frame(curr_frame-1); playing = False
			elif event.key == K_RIGHT: set_frame(curr_frame+1); playing = False
			elif event.key in (K_HOME, K_KP7): set_frame(0); playing = False
			elif event.key in (K_END, K_KP1): set_frame(-1); playing = False

			
			# TOOLS!

			# Instant tools (act directly on current state)
			elif event.key == K_n:  # Instant tools need not be too ergonomic
				set_frame(tools.new_frame(frames, curr_frame))
			elif event.key == K_k:
				set_frame(tools.delete_curr_frame(frames, curr_frame))

			# Direct/semi-modal tools (go to selection mode if no selection)
			elif event.key == K_x:
				# TODO: `handle_mode[mode].segment_i(...)` idk
				if selected_frame is None or not show_selection:
					curr_tool = tools.delete_frame
					curr_mode = Mode.attached[curr_tool]
				else:
					set_frame(
						tools.delete_frame(frames, selected_frame, curr_frame)
					)

			# Modal tools (go to custom mode for more selections)
			elif event.key == K_g:
				curr_tool = tools.move_frame
				curr_mode = Mode.attached[curr_tool]

			elif event.key == K_d:
				if event.mod & (KMOD_LSHIFT|KMOD_RSHIFT):
					curr_tool = tools.copy_frame
					curr_mode = Mode.attached[curr_tool]
				else:
					curr_tool = tools.copy_region
					curr_mode = Mode.attached[curr_tool]
					if selected_region is None or not show_selection:
						drag_mode = DragMode.pixel_region_select

			elif event.key == K_f: # region direct tool
				if selected_region is None or not show_selection:
					curr_tool = tools.fill
					curr_mode = Mode.attached[curr_tool]
					drag_mode = DragMode.pixel_region_select
				else:
					tools.fill(
						frames[curr_frame], paint_colour, selected_region
					)

		elif event.type == VIDEORESIZE:
			if not display.get_flags()&FULLSCREEN: resize(event.size)
		elif event.type == QUIT: running = False
		elif event.type == MOUSEWHEEL:
			mods = pygame.key.get_mods()
			mouse_pos = pygame.mouse.get_pos()

			if mouse_pos[1] > h-SH - frame_panel_h:  # mousewheel event to frame panel
				if mods & (KMOD_LSHIFT|KMOD_RSHIFT):
					dx, _dy = -event.y, event.x
				else:
					dx, _dy = event.x, -event.y

				frame_scroll -= dx * 7

			elif mods & (KMOD_LCTRL|KMOD_RCTRL):
				old_obj_space_mouse = from_screen_space(mouse_pos)
				# the diff that we had here
				zoom *= ZOOM_FAC ** event.y
				zoom = max(MIN_ZOOM, zoom)

				# center at mouse
				new_obj_space_mouse = from_screen_space(mouse_pos)
				scroll[0] += new_obj_space_mouse[0] - old_obj_space_mouse[0]
				scroll[1] += new_obj_space_mouse[1] - old_obj_space_mouse[1]

			else:
				scroll[0] -= event.x * zoom * 12
				scroll[1] += event.y * zoom * 12

		elif event.type == MOUSEBUTTONDOWN:
			if event.button == 3:
				drag_mode = DragMode.scrolling

			elif event.button == 1:
				print('MOUSEDOWN  FRAME', hovered_frame, curr_mode, drag_mode)

				mods = pygame.key.get_mods()
				if mods & (KMOD_LALT|KMOD_RALT):
					if hovered_frame is not None: continue  # mouse on panel
					paint_colour = surf.get_at((x, y))
					text = f'{int.from_bytes(paint_colour, "big"):06x}'

				elif curr_mode == Mode.paint:
					if hovered_frame in range(len(frames)):  # wrap-around would be weird
						set_frame(hovered_frame)
						drag_mode = DragMode.scrub
						continue

					if hovered_frame is not None: continue  # mouse on panel

					x, y = from_screen_space(event.pos)
					x, y = int(x), int(y)

					surf = frames[curr_frame]
					if not surf.get_rect().collidepoint((x, y)): continue

					drag_mode = DragMode.default

					surf.set_at((x, y), paint_colour)

				elif curr_mode == Mode.frame_select:
					if hovered_frame in range(len(frames)):
						show_selection = True
						selected_frame = hovered_frame
						# don't start scrub because we need selection not view

				elif curr_mode == Mode.frame_dest:
					if hovered_frame not in range(len(frames)): continue

					if not show_selection or selected_frame is None:
						show_selection = True
						selected_frame = hovered_frame  # simulates click-drag

					set_frame(hovered_frame)
					drag_mode = DragMode.scrub

				elif curr_mode == Mode.pixel_region_select:
					if hovered_frame is not None:
						if hovered_frame in range(len(frames)):
							drag_mode = DragMode.scrub
							set_frame(hovered_frame)

					else:
						show_selection = True
						selected_frame = curr_frame
						start_selection(event.pos)

				elif curr_mode == Mode.pixel_dest:
					if hovered_frame is not None:
						if hovered_frame in range(len(frames)):
							drag_mode = DragMode.scrub
							set_frame(hovered_frame)

					elif not show_selection or selected_frame is None:
						show_selection = True
						selected_frame = curr_frame
						start_selection(event.pos)

					else:
						drag_mode = DragMode.default  # apply on mouse up

				else:
					updateStat(f'Unsupported mode {curr_mode} for mouse down')

		elif event.type == MOUSEBUTTONUP:
			if event.button == 3:
				if drag_mode is DragMode.scrolling:
					drag_mode = DragMode.none

			elif event.button == 1:
				print('MOUSEUP ON FRAME', hovered_frame, curr_mode, drag_mode)

				# No tool

				if curr_tool is None:
					# paint, type_colour, frame_select, pixel_region_select
					# drag_mode can be scrub in pixel_region_select mode
					if drag_mode is not DragMode.scrub: curr_mode = Mode.paint
					drag_mode = DragMode.none
					continue

				# Direct tools (already applied, or applied on mouse up)

				elif curr_mode is Mode.frame_direct:
					set_frame(curr_tool(frames, selected_frame, curr_frame))

				elif curr_mode is Mode.region_direct:
					curr_tool(surf, selected_region)

				elif curr_mode is Mode.fill:
					curr_tool(
						frames[curr_frame], paint_colour, selected_region
					)

				# Fully modal tools. Apply the tool on mouse up. TODO: preview

				elif curr_mode is Mode.frame_dest:
					if drag_mode is not DragMode.scrub: continue

					print(curr_tool, hovered_frame, selected_frame)
					curr_tool(frames, hovered_frame, selected_frame)

				elif curr_mode is Mode.pixel_dest:
					if drag_mode in (
						DragMode.pixel_region_select, DragMode.scrub
					):
						drag_mode = DragMode.none
						continue  # keep selection

					print('Pixel dest')

					pixel = from_screen_space(event.pos)
					# # copy_region() can handle out of bounds dest
					# if not frames[curr_frame].get_rect().collidepoint(pixel):
					# 	continue

					# Region should contain frame?
					curr_tool(
						frames,
						curr_frame,
						pixel,
						selected_frame,
						selected_region.as_rect(),
					)

				else:
					updateStat('Unknown mode')

				curr_tool = None
				curr_mode = Mode.paint
				show_selection = False
				drag_mode = DragMode.none

		elif event.type == MOUSEMOTION:
			if drag_mode is DragMode.none:
				hovered_frame = None

				if event.pos[1] >= h-SH - frame_panel_h:
					hovered_frame = int(frame_from_screen_space(event.pos[0]))

			elif drag_mode is DragMode.scrub:
				hovered_frame = int(frame_from_screen_space(event.pos[0]))
				if hovered_frame in range(len(frames)): set_frame(hovered_frame)

			elif drag_mode is DragMode.pixel_region_select:
				x, y = from_screen_space(event.pos)
				x, y = int(x), int(y)

				surf = frames[curr_frame]
				if not surf.get_rect().collidepoint((x, y)): continue

				selected_region.set_end((x, y))

			elif drag_mode is DragMode.scrolling:
				scroll[0] += event.rel[0] * zoom
				scroll[1] += event.rel[1] * zoom

			elif curr_mode is Mode.paint:
				x, y = from_screen_space(event.pos)
				x, y = int(x), int(y)

				surf = frames[curr_frame]
				if not surf.get_rect().collidepoint((x, y)): continue

				surf.set_at((x, y), paint_colour)

	updateDisplay()
	frame_time = clock.tick(fps)

	if playing:

		ticks += frame_time
		ticks %= len(frames) * 1000 // play_fps

		# prev_frame = curr_frame
		curr_frame = ticks * play_fps // 1000
