from django.contrib import admin
from .models import Calon, Pemilih, Vote


@admin.register(Calon)
class CalonAdmin(admin.ModelAdmin):
    list_display = ('nama_calon', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('nama_calon',)


@admin.register(Pemilih)
class PemilihAdmin(admin.ModelAdmin):
    list_display = ('nim', 'nama', 'sudah_memilih')
    list_filter = ('sudah_memilih',)
    search_fields = ('nim', 'nama')


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ('pemilih', 'pilihan', 'calon', 'voted_at')
    list_filter = ('pilihan', 'calon', 'voted_at')
    search_fields = ('pemilih__nim', 'pemilih__nama')
    autocomplete_fields = ('pemilih', 'calon')
    list_select_related = ('pemilih', 'calon')
