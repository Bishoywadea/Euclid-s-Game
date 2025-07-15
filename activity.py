import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

import pygame
from sugar3.activity import activity
from sugar3.graphics.toolbarbox import ToolbarBox
from sugar3.activity.widgets import ActivityToolbarButton
from sugar3.activity.widgets import StopButton
from sugar3.graphics.toolbutton import ToolButton
from sugar3.graphics.palette import Palette
from gettext import gettext as _

import sugargame.canvas
from game import Game

class Euclids(activity.Activity):
    def __init__(self, handle):
        activity.Activity.__init__(self, handle)

        self._create_toolbar()

        # Game logic and visuals
        self.game = Game()

        # Sugar Pygame canvas
        self._pygamecanvas = sugargame.canvas.PygameCanvas(
            self, main=self.game.run, modules=[pygame.display, pygame.font]
        )
        self.game.set_canvas(self._pygamecanvas)

        self.set_canvas(self._pygamecanvas)
        self._pygamecanvas.grab_focus()

    def _create_toolbar(self):
        toolbar_box = ToolbarBox()
        self.set_toolbar_box(toolbar_box)

        activity_button = ActivityToolbarButton(self)
        toolbar_box.toolbar.insert(activity_button, -1)

        menu_button = ToolButton('go-home')
        menu_button.set_tooltip(_('Main Menu'))
        menu_button.connect("clicked", self._reset_game)
        toolbar_box.toolbar.insert(menu_button, -1)
        
        theme_button = ToolButton("camera")
        theme_button.set_tooltip("Toggle Theme")
        theme_button.connect("clicked", self._toggle_theme)
        toolbar_box.toolbar.insert(theme_button, -1)

        help_button = ToolButton("toolbar-help")
        help_button.set_tooltip("Help")
        help_button.connect("clicked", self._show_help)
        toolbar_box.toolbar.insert(help_button, -1)

        separator = Gtk.SeparatorToolItem()
        separator.props.draw = False
        separator.set_expand(True)
        toolbar_box.toolbar.insert(separator, -1)

        stop_button = StopButton(self)
        toolbar_box.toolbar.insert(stop_button, -1)

        toolbar_box.show_all()

    def _show_help(self, button):
        self.game.toggle_help()

    def _reset_game(self, button):
        self.game.handle_game_over_click()

    def _toggle_theme(self, button):
        self.game.toggle_theme()

    def read_file(self, file_path):
        self.game.read_file(file_path)

    def write_file(self, file_path):
        self.game.write_file(file_path)

    def close(self):
        self.game.quit()
