from pygame import Surface
from views import Clip
from utils import Mode, Region, FrameIdent, RegionIdent
import pygame.draw

NewCurrFrame = int

# No attachment because it doesn't invoke a separate mode.
# But maybe we should, just to enforce the signature.
def new_frame(clip: Clip, curr_frame: int) -> NewCurrFrame:
	surf = clip[curr_frame]

	curr_frame += 1
	clip.frames.insert(curr_frame, surf.copy())

	return curr_frame

def delete_curr_frame(clip: Clip, curr_frame: int) -> NewCurrFrame:
	'''
	The behaviour of this is intentionally dependent on delete_frame().
	This is to guarantee consistent behaviour between the tools.
	'''
	return delete_frame(clip, curr_frame, curr_frame)

@Mode.frame_direct.attach
def delete_frame(clip: Clip, frame: int, curr_frame: int) -> NewCurrFrame:
	if len(clip) == 1: return curr_frame  # don't crash on exceptional case, maintain len(frame) >= 1

	clip.frames.pop(frame)
	return min(len(clip)-1, curr_frame)

@Mode.frame_dest.attach
def move_frame(dst: FrameIdent, src: FrameIdent):
	# if dst.clip is not src.clip: return  # check for multiclips
	clip = dst.clip

	clip.frames.insert(dst.frame, clip.frames.pop(src.frame))

@Mode.frame_dest.attach
def copy_frame(dst: FrameIdent, src: FrameIdent):
	clip = dst.clip
	clip.frames.insert(dst.frame, src.frame_surf().copy())

@Mode.pixel_dest.attach
def copy_region(dst_frame: FrameIdent, dst_pixel: tuple[int, int], src: RegionIdent):
	print(dst_frame.frame_surf(), 'subsurf', src.region.as_rect())
	# subsurf = frames[src_frame].subsurface(rect)

	dst_surf = dst_frame.frame_surf()
	# print(f'{dst_surf.get_locked() = } {subsurf.get_locked() = }')
	dst_surf.blit(src.frame_ident.frame_surf(), dst_pixel, area=src.region.as_rect())

@Mode.fill.attach
def fill(surf: Surface, region: Region, colour):
	surf.fill(colour, region.as_rect())

@Mode.fill.attach
def ellipse(surf: Surface, region: Region, colour):
	pygame.draw.ellipse(surf, colour, region.as_rect())
