"""
ui/dialogs/import_dialog.py
Simple dialog to choose import mode: Replace or Merge.
"""

import tkinter as tk


def ask_import_mode(parent) -> str | None:
    """
    Show a dialog with two buttons: Replace and Merge.
    Returns "replace" or "merge", or None if cancelled.
    """
    dialog = tk.Toplevel(parent)
    dialog.title("Import Mode")
    dialog.transient(parent)
    dialog.grab_set()
    dialog.geometry("300x120")
    dialog.resizable(False, False)

    tk.Label(dialog, text="How would you like to import the data?", pady=10).pack()

    frame = tk.Frame(dialog)
    frame.pack(pady=5)

    result = [None]

    def set_result(mode):
        result[0] = mode
        dialog.destroy()

    tk.Button(frame, text="Replace (overwrite all)", command=lambda: set_result("replace"), width=15).pack(side=tk.LEFT, padx=5)
    tk.Button(frame, text="Merge (add unique items)", command=lambda: set_result("merge"), width=15).pack(side=tk.LEFT, padx=5)

    dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)
    parent.wait_window(dialog)
    return result[0]
    