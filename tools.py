def new_frame(frames, curr_frame) -> 'new_frame':
	surf = frames[curr_frame]

	curr_frame += 1
	frames.insert(curr_frame, surf.copy())

	return curr_frame
