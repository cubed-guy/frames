from pygame import Surface
from utils import Mode

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

@Mode.frame_dest.attach
def move_frame(frames: list[Surface], dst, src):
	frames.insert(dst, frames.pop(src))

@Mode.frame_dest.attach
def copy_frame(frames: list[Surface], dst, src):
	frames.insert(dst, frames[src].copy())
