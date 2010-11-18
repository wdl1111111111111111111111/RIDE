#  Copyright 2008-2009 Nokia Siemens Networks Oyj
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import wx

from robotide.pluginapi import Plugin, ActionInfoCollection
from robotide.robotapi import (ResourceFile, TestCaseFile, TestDataDirectory,
                               TestCase, UserKeyword, Variable)
from robotide.publish import (RideTreeSelection, RideNotebookTabChanging,
                              RideNotebookTabChanged, RideSaving)
from robotide.widgets import PopupCreator
from editors import (Editor, TestCaseEditor, UserKeywordEditor,
                     TestCaseFileEditor, ResourceFileEditor, InitFileEditor,
                     VariableEditorChooser)


_EDIT = """
[File]
&Save | Save current suite or resource | Ctrlcmd-S | ART_FILE_SAVE

[Edit]
&Undo | Undo last modification | Ctrlcmd-Z
&Redo | Redo modification | Ctrlcmd-Y
---
Cu&t | Cut | Ctrlcmd-X
&Copy | Copy | Ctrlcmd-C
&Paste | Paste | Ctrlcmd-V
&Delete | Delete  | Del
---
Comment | Comment selected rows | Ctrlcmd-3
Uncomment | Uncomment selected rows | Ctrlcmd-4

[Tools]
Content Assistance (Ctrl-Space or Ctrl-Alt-Space) | Show possible keyword and variable completions
"""


class EditorPlugin(Plugin):
    """The default editor plugin.

    This plugin implements editors for the various items of Robot Framework
    test data.
    """
    def __init__(self, application):
        Plugin.__init__(self, application)
        self._tab = None
        self._grid_popup_creator = PopupCreator()

    def enable(self):
        self.register_editor(TestDataDirectory, InitFileEditor)
        self.register_editor(ResourceFile, ResourceFileEditor)
        self.register_editor(TestCase, TestCaseEditor)
        self.register_editor(TestCaseFile, TestCaseFileEditor)
        self.register_editor(UserKeyword, UserKeywordEditor)
        self.register_editor(Variable, VariableEditorChooser)
        self._show_editor()
        self.register_actions(ActionInfoCollection(_EDIT, self._tab, self._tab))
        self.subscribe(self.OnTreeItemSelected, RideTreeSelection)
        self.subscribe(self.OnTabChanged, RideNotebookTabChanged)
        self.subscribe(self.OnTabChanging, RideNotebookTabChanging)
        self.subscribe(self.OnSaveToModel, RideSaving)

    def _show_editor(self):
        if not self._tab:
            self._tab = _EditorTab(self)
            self.add_tab(self._tab, 'Edit', allow_closing=False)
        if self.tab_is_visible(self._tab):
            self._tab.show_editor(self.tree)

    def disable(self):
        self.unregister_actions()
        self.unsubscribe_all()
        self.delete_tab(self._tab)
        self._tab = None

    def register_context_menu_hook_to_grid(self, callable):
        """ Used to register own items to grid's right click context menu

        callable is called with current selection (list of list containing
        values) and it is expected to return list of PopupMenuItem.
        If user selects one of the returned PopupMenuItem, related function
        is called with one argument, the wx event.
        """
        self._grid_popup_creator.add_hook(callable)

    def unregister_context_menu_hook_to_grid(self, callable):
        self._grid_popup_creator.remove_hook(callable)

    def OnTreeItemSelected(self, message=None):
        self._tab.create_editor(self.tree)
        self._show_editor()

    def OnOpenEditor(self, event):
        self._show_editor()

    def OnTabChanged(self, event):
        self._show_editor()

    def OnTabChanging(self, message):
        if 'Edit' in message.oldtab:
            self._tab.save()

    def OnSaveToModel(self, message):
        if self._tab:
            self._tab.save()


class _EditorTab(wx.Panel):

    def __init__(self, plugin):
        wx.Panel.__init__(self, plugin.notebook, style=wx.SUNKEN_BORDER)
        self.plugin = plugin
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.sizer)
        self.editor = None

    def show_editor(self, tree):
        if not self.editor:
            self.create_editor(tree)
        self.Show()

    def create_editor(self, tree):
        self.Show(False)
        if self.editor:
            self.editor.close()
            self.editor.Destroy()
            self.sizer.Clear()
        self.editor = Editor(self.plugin, self, tree)
        self.sizer.Add(self.editor, 1, wx.ALL | wx.EXPAND)
        self.Layout()

    def OnSave(self, event):
        self.plugin.save_selected_datafile()

    def OnUndo(self, event):
        self.editor.undo()

    def OnRedo(self, event):
        self.editor.redo()

    def OnCut(self, event):
        self.editor.cut()

    def OnCopy(self, event):
        self.editor.copy()

    def OnPaste(self, event):
        self.editor.paste()

    def OnDelete(self, event):
        self.editor.delete()

    def OnComment(self, event):
        self.editor.comment()

    def OnUncomment(self, event):
        self.editor.uncomment()

    def OnContentAssistance(self, event):
        self.editor.show_content_assist()

    def save(self, message=None):
        self.editor.save()
