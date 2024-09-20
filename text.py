from typing import Optional, Union
from pygame.font import Font
import pygame

Surface = Union[pygame.Surface, pygame.surface.Surface]

class TextSurface:
	def __init__(self, font_path: str, size: int, colour, text='', tracking=0, *, create_font=True):
		self.font_path = font_path
		self.size = size
		self.colour = colour
		self.text = text
		self.tracking = 0
		if create_font: self.update_font()

	def update_font(self) -> None:
		self.font = Font(self.font_path, self.size)
		self._surf_cache: Optional[Surface] = None

	def surf(self) -> Surface:
		'''
		Use only for reading.
		DO NOT MODIFY THE RETURNED SURFACE
		pygame does not have any way of enforcing that so we have to do it manually.
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
