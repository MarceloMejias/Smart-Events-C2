from typing import TYPE_CHECKING

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

if TYPE_CHECKING:
    from django.db.models.manager import Manager

# Evento
# Un usuario no autenticado puede ver los eventos, pero no puede crearlos, editarlos o eliminarlos.
# Un usuario autenticado puede regarse en eventos y ver los eventos en los que se ha regado. Tambien pueden anular su rego.
# Los adminadores pueden gestionar todos los eventos.


class Event(models.Model):
    """
    Modelo principal que representa un evento.

    Gestiona toda la información de eventos incluyendo fechas, capacidad,
    precio y estado. Incluye validaciones automáticas y métodos de utilidad.
    """

    if TYPE_CHECKING:
        objects: "Manager[Event]"

    class TipoEvento(models.TextChoices):
        CHARLA = "CHARLA", "Charla"
        TALLER = "TALLER", "Taller"
        FERIA = "FERIA", "Feria"
        CONCIERTO = "CONCIERTO", "Concierto"

    nombre = models.CharField(max_length=200, verbose_name="Nombre")
    descripcion = models.TextField(verbose_name="Descripción")
    tipo = models.CharField(
        max_length=20,
        choices=TipoEvento.choices,
        default=TipoEvento.CHARLA,
        verbose_name="Tipo de evento",
    )
    fecha_inicio = models.DateTimeField(db_index=True, verbose_name="Fecha de inicio")
    fecha_fin = models.DateTimeField(verbose_name="Fecha de fin")
    lugar = models.CharField(max_length=300, verbose_name="Lugar")
    creado_en = models.DateTimeField(auto_now_add=True, verbose_name="Creado en")
    actualizado_en = models.DateTimeField(auto_now=True, verbose_name="Actualizado en")
    imagen = models.ImageField(
        upload_to="event_images/", null=True, blank=True, verbose_name="Imagen"
    )
    activo = models.BooleanField(default=True, db_index=True, verbose_name="Activo")
    destacado = models.BooleanField(default=False, db_index=True, verbose_name="Destacado")
    capacidad = models.IntegerField(null=True, blank=True, verbose_name="Capacidad máxima")
    precio = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Precio"
    )

    class Meta:
        verbose_name = "Evento"
        verbose_name_plural = "Eventos"
        ordering = ["-fecha_inicio", "-destacado"]
        indexes = [
            models.Index(fields=["fecha_inicio", "activo"]),
            models.Index(fields=["destacado", "activo"]),
        ]

    def __str__(self) -> str:
        return self.nombre

    def clean(self):
        """Validaciones del modelo."""
        super().clean()

        # Validar que fecha_fin sea posterior a fecha_inicio
        if self.fecha_inicio and self.fecha_fin:
            if self.fecha_fin <= self.fecha_inicio:
                raise ValidationError(
                    {"fecha_fin": "La fecha de fin debe ser posterior a la fecha de inicio."}
                )

        # Validar capacidad positiva
        if self.capacidad is not None and self.capacidad < 1:
            raise ValidationError({"capacidad": "La capacidad debe ser mayor a 0."})

        # Validar precio positivo
        if self.precio is not None and self.precio < 0:
            raise ValidationError({"precio": "El precio no puede ser negativo."})

    def save(self, *args, **kwargs):
        """Override save para ejecutar validaciones."""
        self.clean()
        super().save(*args, **kwargs)

    def espacios_disponibles(self) -> int | None:
        """
        Retorna el número de espacios disponibles.

        Returns:
            int | None: Espacios disponibles, o None si no hay capacidad limitada.
        """
        if self.capacidad is None:
            return None

        registros_count = self.registrations.count()
        return max(0, self.capacidad - registros_count)

    def esta_lleno(self) -> bool:
        """
        Verifica si el evento está lleno.

        Returns:
            bool: True si está lleno, False si hay espacios o sin límite.
        """
        espacios = self.espacios_disponibles()
        return espacios is not None and espacios == 0

    def esta_activo(self) -> bool:
        """
        Verifica si el evento está activo y aún no ha finalizado.

        Returns:
            bool: True si está activo y no ha finalizado.
        """
        return self.activo and self.fecha_fin >= timezone.now()

    def puede_registrarse(self) -> bool:
        """
        Verifica si se pueden aceptar más registros.

        Returns:
            bool: True si el evento acepta registros.
        """
        return self.esta_activo() and not self.esta_lleno()

    def total_registrados(self) -> int:
        """
        Retorna el total de usuarios registrados.

        Returns:
            int: Número de registros activos.
        """
        return self.registrations.count()

    def porcentaje_ocupacion(self) -> float | None:
        """
        Calcula el porcentaje de ocupación del evento.

        Returns:
            float | None: Porcentaje (0-100), o None si no hay capacidad limitada.
        """
        if self.capacidad is None:
            return None

        if self.capacidad == 0:
            return 0.0

        return (self.total_registrados() / self.capacidad) * 100


# Categoria
class Category(models.Model):
    """
    Modelo que representa categorías para clasificar eventos.
    """

    if TYPE_CHECKING:
        objects: "Manager[Category]"

    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre")
    descripcion = models.TextField(null=True, blank=True, verbose_name="Descripción")

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ["nombre"]

    def __str__(self) -> str:
        return self.nombre

    def total_eventos(self) -> int:
        """
        Retorna el número total de eventos en esta categoría.

        Returns:
            int: Cantidad de eventos asociados.
        """
        return self.event_categories.count()

    def eventos_activos(self):
        """
        Retorna los eventos activos asociados a esta categoría.

        Returns:
            QuerySet: Eventos activos en esta categoría.
        """
        return Event.objects.filter(event_categories__categoria=self, activo=True).distinct()


# Relacion ManyToMany entre Evento y Categoria
class EventCategory(models.Model):
    """
    Modelo intermedio para la relación many-to-many entre eventos y categorías.
    """

    evento = models.ForeignKey(
        Event, on_delete=models.CASCADE, related_name="event_categories", verbose_name="Evento"
    )
    categoria = models.ForeignKey(
        Category,
        on_delete=models.CASCADE,
        related_name="event_categories",
        verbose_name="Categoría",
    )

    class Meta:
        unique_together = ("evento", "categoria")
        verbose_name = "Categoría del Evento"
        verbose_name_plural = "Categorías de Eventos"
        ordering = ["evento", "categoria"]

    def __str__(self) -> str:
        return f"{self.evento.nombre} - {self.categoria.nombre}"


# Registro de Usuario en Evento
class EventRegistration(models.Model):
    """
    Modelo que representa el registro de un usuario en un evento.

    Gestiona la inscripción de usuarios con validaciones de capacidad.
    """

    if TYPE_CHECKING:
        objects: "Manager[EventRegistration]"

    evento = models.ForeignKey(
        Event, on_delete=models.CASCADE, related_name="registrations", verbose_name="Evento"
    )
    usuario = models.ForeignKey(
        "auth.User",
        on_delete=models.CASCADE,
        related_name="event_registrations",
        verbose_name="Usuario",
    )
    registrado_en = models.DateTimeField(auto_now_add=True, verbose_name="Registrado en")

    class Meta:
        unique_together = ("evento", "usuario")
        verbose_name = "Registro de Evento"
        verbose_name_plural = "Registros de Eventos"
        ordering = ["-registrado_en"]
        indexes = [
            models.Index(fields=["evento", "usuario"]),
            models.Index(fields=["registrado_en"]),
        ]

    def __str__(self) -> str:
        return f"{self.usuario.username} registrado en {self.evento.nombre}"

    def clean(self):
        """Validaciones del modelo."""
        super().clean()

        # Validar que el evento acepta registros
        if not self.evento.puede_registrarse():
            if self.evento.esta_lleno():
                raise ValidationError("El evento está lleno.")
            elif not self.evento.esta_activo():
                raise ValidationError("El evento no está activo o ya finalizó.")

        # Validar que no esté ya registrado (solo en creación)
        if not self.pk:
            existe = EventRegistration.objects.filter(
                evento=self.evento, usuario=self.usuario
            ).exists()
            if existe:
                raise ValidationError("El usuario ya está registrado en este evento.")

    def save(self, *args, **kwargs):
        """Override save para ejecutar validaciones."""
        self.clean()
        super().save(*args, **kwargs)


# Comentario en Evento
class EventComment(models.Model):
    """
    Modelo que representa comentarios de usuarios en eventos.

    Permite a los usuarios dejar feedback y comentarios sobre eventos.
    """

    if TYPE_CHECKING:
        objects: "Manager[EventComment]"

    evento = models.ForeignKey(
        Event, on_delete=models.CASCADE, related_name="comments", verbose_name="Evento"
    )
    usuario = models.ForeignKey(
        "auth.User", on_delete=models.CASCADE, related_name="event_comments", verbose_name="Usuario"
    )
    comentario = models.TextField(verbose_name="Comentario")
    creado_en = models.DateTimeField(auto_now_add=True, verbose_name="Creado en")

    class Meta:
        verbose_name = "Comentario de Evento"
        verbose_name_plural = "Comentarios de Eventos"
        ordering = ["-creado_en"]
        indexes = [
            models.Index(fields=["evento", "-creado_en"]),
        ]

    def __str__(self) -> str:
        return f"Comentario de {self.usuario.username} en {self.evento.nombre}"

    def comentario_resumido(self, max_length: int = 50) -> str:
        """
        Retorna una versión resumida del comentario.

        Args:
            max_length: Longitud máxima del resumen.

        Returns:
            str: Comentario resumido con '...' si es necesario.
        """
        if len(self.comentario) <= max_length:
            return self.comentario
        return f"{self.comentario[:max_length]}..."
