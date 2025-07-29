# This file is part of the Euclid's game.
# Copyright (C) 2025 Bishoy Wadea
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
import time
from gi.repository import GLib
from sugar3.activity import activity
from sugar3.graphics.toolbarbox import ToolbarBox
from sugar3.activity.widgets import ActivityToolbarButton
from sugar3.activity.widgets import StopButton
from sugar3.graphics.toolbutton import ToolButton
from gettext import gettext as _
import os
import json
from collabwrapper import CollabWrapper

from game import Game, GameMode
from game import Game

class Euclids(activity.Activity):
    def __init__(self, handle):
        activity.Activity.__init__(self, handle)
        
        self._loaded_from_journal = False
        self._read_file_called = False
        
        self._create_toolbar()
        
        self.game = Game()
        
        self._collab = CollabWrapper(self)
        self._collab.connect('joined', self.__joined_cb)
        self._collab.connect('buddy_joined', self.__buddy_joined_cb)
        self._collab.connect('buddy_left', self.__buddy_left_cb)
        self._collab.connect('message', self.__message_cb)
        
        self.game.set_collab_wrapper(self._collab)
        
        game_content = self.game.main_box
        if game_content.get_parent():
            game_content.get_parent().remove(game_content)
        
        self.set_canvas(game_content)
        
        self.game.hide()
        
        GLib.timeout_add(500, self._setup_collab)
        
        GLib.timeout_add(100, self._check_and_show_menu)
    
    def _setup_collab(self):
        """Setup collaboration after everything is initialized"""
        print("DEBUG: Setting up collaboration")
        self._collab.setup()
        return False
    
    def _check_and_show_menu(self):
        """Show menu only if we haven't loaded from journal"""
        if not self._read_file_called:
            print("DEBUG: No journal file to load, showing menu")
            self.game.show_menu()
        else:
            print("DEBUG: Journal file is being loaded, not showing menu")
        return False 
    
    def _create_toolbar(self):
        toolbar_box = ToolbarBox()
        self.set_toolbar_box(toolbar_box)
        
        activity_button = ActivityToolbarButton(self)
        toolbar_box.toolbar.insert(activity_button, -1)
        
        menu_button = ToolButton('go-home')
        menu_button.set_tooltip(_('Main Menu'))
        menu_button.connect("clicked", self._show_menu)
        toolbar_box.toolbar.insert(menu_button, -1)
        
        help_button = ToolButton("toolbar-help")
        help_button.set_tooltip(_("Help"))
        help_button.connect("clicked", self._show_help)
        toolbar_box.toolbar.insert(help_button, -1)
        
        separator = Gtk.SeparatorToolItem()
        separator.props.draw = False
        separator.set_expand(True)
        toolbar_box.toolbar.insert(separator, -1)
        
        stop_button = StopButton(self)
        toolbar_box.toolbar.insert(stop_button, -1)
        
        toolbar_box.show_all()
    
    def _show_menu(self, button):
        self.game.show_menu()
    
    def _show_help(self, button):
        dialog = Gtk.MessageDialog(
            parent=self,
            flags=0,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=_("How to Play Euclid's Game")
        )
        dialog.format_secondary_text(_(
            "1. Select two numbers from the board\n"
            "2. Their difference will be added if it's not already there\n"
            "3. The player who cannot make a valid move loses\n"
            "4. Try to force your opponent into a position with no moves!"
        ))
        dialog.run()
        dialog.destroy()
    
    def read_file(self, file_path):
        """Load game state from Journal"""
        print(f"DEBUG: read_file called with path: {file_path}")
        
        self._read_file_called = True
        
        if not os.path.exists(file_path):
            print(f"ERROR: File does not exist: {file_path}")
            self.game.show_menu()
            return
        
        try:
            file_stats = os.stat(file_path)
            print(f"DEBUG: File size: {file_stats.st_size} bytes")
            print(f"DEBUG: File modified: {time.ctime(file_stats.st_mtime)}")
            
            with open(file_path, 'r') as f:
                content = f.read()
                print(f"DEBUG: Read {len(content)} characters from file")
                
                try:
                    data = json.loads(content)
                    print(f"DEBUG: Successfully parsed JSON")
                    print(f"DEBUG: Top-level keys: {list(data.keys())}")
                except json.JSONDecodeError as e:
                    print(f"ERROR: JSON parsing failed: {e}")
                    print(f"DEBUG: First 200 chars of content: {content[:200]}")
                    self.game.show_menu()
                    return
            
            loaded_metadata = data.get('metadata', {})
            print(f"DEBUG: Metadata: {loaded_metadata}")
            
            game_state = data.get('game_state', {})
            if game_state:
                print(f"DEBUG: Game state found with keys: {list(game_state.keys())}")
                
                if hasattr(self.game, 'load_state'):
                    print("DEBUG: Loading game state immediately")
                    if self.game.load_state(game_state):
                        self._loaded_from_journal = True
                        print("DEBUG: Game state loaded successfully")
                    else:
                        print("ERROR: game.load_state() returned False")
                        self.game.show_menu()
                else:
                    print("ERROR: game object doesn't have load_state method")
                    self.game.show_menu()
            else:
                print("WARNING: No game_state in loaded data")
                self.game.show_menu()
                
        except IOError as e:
            print(f"ERROR: IO error reading file: {e}")
            self.game.show_menu()
        except Exception as e:
            print(f"ERROR: Unexpected error reading file: {e}")
            import traceback
            traceback.print_exc()
            self.game.show_menu()

    def write_file(self, file_path):
        """Save game state to Journal"""
        print(f"DEBUG: write_file called with path: {file_path}")
        
        try:
            data = {
                'metadata': {
                    'activity': 'org.sugarlabs.Euclids',
                    'activity_version': 1,
                    'mime_type': 'application/x-euclids-game',
                    'timestamp': time.time()
                },
                'game_state': {}
            }
            
            if hasattr(self.game, 'save_state'):
                print("DEBUG: Calling game.save_state()")
                game_state = self.game.save_state()
                print(f"DEBUG: Got game state with keys: {list(game_state.keys()) if game_state else 'None'}")
                data['game_state'] = game_state
            else:
                print("ERROR: game object doesn't have save_state method")
            
            try:
                print("DEBUG: Serializing data to JSON")
                json_string = json.dumps(data, indent=2)
                print(f"DEBUG: Data keys: {json_string}")
                print(f"DEBUG: JSON serialization successful, length: {len(json_string)}")
            except Exception as e:
                print(f"ERROR: JSON serialization failed: {e}")
                return
            
            with open(file_path, 'w') as f:
                f.write(json_string)
                f.flush()
                os.fsync(f.fileno())
                
            print(f"DEBUG: File written successfully")
            
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                print(f"DEBUG: Verified file exists, size = {file_size} bytes")
                
                with open(file_path, 'r') as f:
                    verify_content = f.read()
                    print(f"DEBUG: Verified content length = {len(verify_content)}")
            else:
                print("ERROR: File doesn't exist after writing!")
                
        except Exception as e:
            print(f"ERROR: Writing file failed: {e}")
            import traceback
            traceback.print_exc()

    def can_close(self):
        """Called when the activity is about to close"""
        return True

    def close(self):
        """Clean shutdown"""
        if hasattr(self.game, 'quit'):
            self.game.quit()
        super(Euclids, self).close()
    
    def __joined_cb(self, collab):
        """Called when we join a shared activity"""
        print("DEBUG: Joined shared activity")
        if self.game:
            self.game.on_collaboration_joined()

    def __buddy_joined_cb(self, collab, buddy):
        """Called when another user joins"""
        print(f"DEBUG: Buddy joined: {buddy.props.nick}")
        if self.game:
            self.game.on_buddy_joined(buddy)

    def __buddy_left_cb(self, collab, buddy):
        """Called when another user leaves"""
        print(f"DEBUG: Buddy left: {buddy.props.nick}")
        if self.game:
            self.game.on_buddy_left(buddy)

    def __message_cb(self, collab, buddy, message):
        """Called when we receive a message"""
        print(f"DEBUG: __message_cb called")
        print(f"DEBUG: From buddy: {buddy.props.nick}")
        print(f"DEBUG: Message content: {message}")
        print(f"DEBUG: Message type: {type(message)}")
        
        if self.game:
            self.game.on_message_received(buddy, message)
        else:
            print("ERROR: No game object to handle message")
    
    def get_data(self):
        """Called by CollabWrapper when someone joins to get current state"""
        print("DEBUG: get_data called")
        if hasattr(self.game, 'get_game_state_for_sync'):
            data = self.game.get_game_state_for_sync()
            print(f"DEBUG: Returning game state: {data}")
            return data
        return {}

    def set_data(self, data):
        """Called by CollabWrapper when joining to receive current state"""
        print(f"DEBUG: set_data called with: {data}")
        if data and hasattr(self.game, 'set_game_state_from_sync'):
            self.game.set_game_state_from_sync(data)
            