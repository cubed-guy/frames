from pygame import Surface
from utils import Mode, Region
import pygame.draw

# No attachment because it doesn't invoke a separate mode.
# But maybe we should, just to enforce the signature.
def new_frame(frames, curr_frame) -> 'new_frame':
	surf = frames[curr_frame]

	curr_frame += 1
	frames.insert(curr_frame, surf.copy())

	return curr_frame

def delete_curr_frame(frames, curr_frame) -> 'new_frame':
	'''
	The behaviour of this is intentionally dependent on delete_frame().
	This is to guarantee consistent behaviour between the tools.
	'''
	return delete_frame(frames, curr_frame, curr_frame)

@Mode.frame_direct.attach
def delete_frame(frames, frame, curr_frame) -> 'new_frame':
	if len(frames) == 1: return curr_frame  # don't crash on exceptional case, maintain len(frame) >= 1

	frames.pop(frame)
	return min(len(frames)-1, curr_frame)

@Mode.frame_dest.attach
def move_frame(frames: list[Surface], dst, src):
	frames.insert(dst, frames.pop(src))

@Mode.frame_dest.attach
def copy_frame(frames: list[Surface], dst, src):
	frames.insert(dst, frames[src].copy())

@Mode.pixel_dest.attach
def copy_region(frames, dst_frame, dst_pixel, src_frame, rect):
	print(frames[src_frame], 'subsurf', rect)
	# subsurf = frames[src_frame].subsurface(rect)

	dst_surf = frames[dst_frame]
	# print(f'{dst_surf.get_locked() = } {subsurf.get_locked() = }')
	dst_surf.blit(frames[src_frame], dst_pixel, area=rect)

@Mode.fill.attach
def fill(surf, colour, region: Region):
	surf.fill(colour, region.as_rect())
