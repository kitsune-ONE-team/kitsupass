import gi
import sys

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk


def getpass(title: str, subtitle: str | None = None) -> str | None:
    dialog = Gtk.MessageDialog(
        message_type=Gtk.MessageType.QUESTION,
        buttons=Gtk.ButtonsType.OK_CANCEL,
        text=title)
    if subtitle:
        dialog.format_secondary_text(subtitle)

    entry = Gtk.Entry()
    entry.set_visibility(False)
    entry.set_invisible_char('*')
    entry.set_size_request(360, 0)

    box = Gtk.Box()
    box.set_margin_start(16)
    box.set_margin_end(16)
    box.add(entry)

    dialog.get_content_area().pack_end(box, False, False, 0)
    dialog.show_all()

    response = dialog.run()
    password = entry.get_text()
    dialog.destroy()

    if response == Gtk.ResponseType.OK:
        return password


if __name__ == '__main__':
    title = sys.argv[1] if len(sys.argv) >= 2 else ''
    print(getpass(title))
