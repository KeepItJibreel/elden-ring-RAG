from django.contrib import admin
from .models import Chunk

@admin.register(Chunk)
class ChunkAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "source")
    list_filter = ("category",)
    search_fields = ("name", "text")
    exclude = ("embedding",)