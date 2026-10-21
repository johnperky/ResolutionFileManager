"""Exercise actual translated action buttons and their copy/move/cancel values."""
import unittest
import tkinter as tk
from tkinter import ttk
from types import SimpleNamespace
from pathlib import Path
from localization import Translator,SUPPORTED_LANGUAGES,RTL_LANGUAGES
from transfer_ui import UpgradePaneMixin


class DropDialogTests(unittest.TestCase):
    def test_all_languages_have_explicit_buttons_and_correct_actions(self):
        root=tk.Tk();root.geometry('500x200')
        class Pane(UpgradePaneMixin,ttk.Frame): pass
        pane=Pane(root);pane.pack();root.update()
        try:
            for code in SUPPORTED_LANGUAGES:
                translator=Translator(Path(__file__).parent/'locales',code)
                pane.app=SimpleNamespace(tr=translator.text,is_rtl=code in RTL_LANGUAGES)
                for index,expected in ((0,True),(1,False),(2,None),(3,None)):
                    errors=[]
                    def act():
                        try:
                            window=next(w for w in pane.winfo_children() if isinstance(w,tk.Toplevel))
                            frame=next(w for w in window.winfo_children() if isinstance(w,ttk.Frame))
                            buttons=[w for w in frame.winfo_children() if isinstance(w,ttk.Button)]
                            self.assertEqual([b.cget('text') for b in buttons],[translator.text(k) for k in ('choice.copy','choice.move','common.cancel')])
                            self.assertEqual(len(buttons),3)
                            if index==3: window.destroy()
                            else: buttons[index].invoke()
                        except Exception as exc:
                            errors.append(exc)
                            for w in pane.winfo_children():
                                if isinstance(w,tk.Toplevel):w.destroy()
                    root.after(20,act)
                    with self.subTest(language=code,action=index):
                        actual=pane.ask_drop_action()
                        if errors: raise errors[0]
                        self.assertIs(actual,expected)
        finally:root.destroy()

if __name__=='__main__':unittest.main()
