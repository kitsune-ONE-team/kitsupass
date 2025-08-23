import os
import tempfile


class TMP:
    def __enter__(self):
        self.tmp = tempfile.NamedTemporaryFile(delete=False, delete_on_close=False)
        self.tmp.close()
        return self.tmp

    def __exit__(self, exc_type, exc_value, exc_traceback):
        os.remove(self.tmp.name)
