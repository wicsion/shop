from django.core.files.storage import FileSystemStorage
from django.utils.deconstruct import deconstructible

@deconstructible
class CustomFileStorage(FileSystemStorage):
    def __init__(self, *args, **kwargs):
        self.version = kwargs.pop('version', None)
        super().__init__(*args, **kwargs)

    def url(self, name):
        url = super().url(name)
        # Добавляем версию к URL для сброса кэша при изменении
        if self.version is not None:
            return f"{url}?v={self.version}"
        return url