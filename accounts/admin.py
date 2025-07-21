from django.contrib import admin
from .models import SupportTicket

@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = ('id', 'company', 'user', 'ticket_type', 'status', 'created_at')
    list_filter = ('ticket_type', 'status', 'company')
    search_fields = ('company__legal_name', 'user__email', 'message')
    readonly_fields = ('company', 'user', 'created_at')
    fieldsets = (
        (None, {
            'fields': ('company', 'user', 'ticket_type', 'status')
        }),
        ('Контактная информация', {
            'fields': ('contact_email', 'contact_phone')
        }),
        ('Сообщение', {
            'fields': ('message',)
        }),
        ('Администрирование', {
            'fields': ('admin_notes',),
            'classes': ('collapse',)
        }),
    )