from typing import Optional, Union
from pygame.font import Font
import pygame

Surface = Union[pygame.Surface, pygame.surface.Surface]

class TextFrame:
	def __init__(self,
		font_path: str, size: int, colour, text='', tracking=0,
		*, create_font=True
	):
		self.font_path = font_path
		self.size = size
		self.colour = colour
		self.text = text
		self.tracking = 0  # Unused for now.
		if create_font: self.update_font()
		self.reset_surf_cache()

	def update_font(self) -> None:
		self.font = Font(self.font_path, self.size)

	def reset_surf_cache(self) -> None:
		self._surf_cache: Optional[Surface] = None

	def update_params(self, *,
		font_path=None, size=None, colour=None, tracking=None, text=None,
	) -> None:

		update_font = False

		if font_path is not None: self.font_path = font_path; update_font = True
		if size is not None: self.size = size; update_font = True
		if colour is not None: self.colour = colour
		if text is not None: self.text = text
		if tracking is not None: self.tracking = tracking

		if update_font: self.update_font()
		self.reset_surf_cache()

	def surf(self) -> Surface:
		'''
		Use only for reading.
		DO NOT MODIFY THE RETURNED SURFACE
		pygame does not have any way of enforcing it so we have to do it manually.
		'''
		if self._surf_cache is None:
			self._surf_cache = self.font.render(self.text, True, self.colour)
			print(f'Text has been rendered: {self._surf_cache} (text = {self.text!r})')

		return self._surf_cache

	def copy(self):
		out = self.__class__(self.font_path, self.size, self.colour, self.text, self.tracking, create_font=False)
		out.font = self.font
		out._surf_cache = self._surf_cache  # read-only, so no problem
		return out
