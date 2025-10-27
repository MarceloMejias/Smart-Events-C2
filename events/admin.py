"""Configuración del panel de administración de Django para eventos."""

from django.contrib import admin
from django.utils.html import format_html

from .models import Category, Event, EventCategory, EventComment, EventRegistration


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    """Administración simple de eventos con soporte para imágenes."""

    list_display = (
        "nombre",
        "imagen_preview",
        "tipo",
        "fecha_inicio",
        "lugar",
        "ocupacion_display",
        "activo",
        "destacado",
    )
    list_filter = ("activo", "destacado", "tipo", "fecha_inicio")
    search_fields = ("nombre", "descripcion", "lugar")
    date_hierarchy = "fecha_inicio"
    ordering = ("-fecha_inicio",)
    readonly_fields = ("imagen_preview",)

    fields = (
        "nombre",
        "descripcion",
        "tipo",
        "imagen",
        "imagen_preview",
        "fecha_inicio",
        "fecha_fin",
        "lugar",
        "capacidad",
        "precio",
        "activo",
        "destacado",
    )

    @admin.display(description="Vista Previa")
    def imagen_preview(self, obj):
        """Muestra una vista previa de la imagen del evento."""
        if obj.imagen:
            return format_html(
                '<img src="{}" style="max-width: 200px; max-height: 200px; '
                'border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);" />',
                obj.imagen.url,
            )
        return format_html('<span style="color: #6c757d;">Sin imagen</span>')

    @admin.display(description="Ocupación")
    def ocupacion_display(self, obj):
        """Muestra una barra de progreso visual de la ocupación del evento."""
        if obj.capacidad is None:
            return format_html(
                '<span style="color: #6c757d; font-style: italic;">Sin límite</span>'
            )

        porcentaje = obj.porcentaje_ocupacion()
        total = obj.total_registrados()
        espacios = obj.espacios_disponibles()

        # Determinar color según ocupación
        if porcentaje >= 100:
            color = "#dc3545"  # Rojo
        elif porcentaje >= 80:
            color = "#ffc107"  # Amarillo
        else:
            color = "#28a745"  # Verde

        # Barra de progreso HTML
        return format_html(
            '<div style="width: 200px;">'
            '<div style="background-color: #e9ecef; border-radius: 4px; overflow: hidden;">'
            '<div style="background-color: {}; width: {}%; height: 20px; '
            "display: flex; align-items: center; justify-content: center; "
            'color: white; font-size: 11px; font-weight: bold;">'
            "{}%"
            "</div>"
            "</div>"
            '<div style="font-size: 11px; color: #6c757d; margin-top: 2px;">'
            "{}/{} registrados ({} disponibles)"
            "</div>"
            "</div>",
            color,
            min(porcentaje, 100),
            int(porcentaje),
            total,
            obj.capacidad,
            espacios,
        )


# Registro simple de los demás modelos
admin.site.register(Category)
admin.site.register(EventCategory)
admin.site.register(EventRegistration)
admin.site.register(EventComment)
# Fin de events/admin.py
