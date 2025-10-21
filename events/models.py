from django.db import models

# Evento
# Un usuario no autenticado puede ver los eventos, pero no puede crearlos, editarlos o eliminarlos.
# Un usuario autenticado puede regarse en eventos y ver los eventos en los que se ha regado. Tambien pueden anular su rego.
# Los adminadores pueden gestionar todos los eventos.

class Event(models.Model):
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField()
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField()
    lugar = models.CharField(max_length=300)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)
    imagen = models.ImageField(upload_to='event_images/', null=True, blank=True)
    activo = models.BooleanField(default=True)
    destacado = models.BooleanField(default=False)
    capacidad = models.IntegerField(null=True, blank=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self) -> str:
        return self.nombre

# Categoria
class Category(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(null=True, blank=True)

    def __str__(self) -> str:
        return self.nombre

# Relacion ManyToMany entre Evento y Categoria
class EventCategory(models.Model):
    evento = models.ForeignKey(Event, on_delete=models.CASCADE)
    categoria = models.ForeignKey(Category, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('evento', 'categoria')

    def __str__(self) -> str:
        return f"{self.evento.nombre} - {self.categoria.nombre}"

# Registro de Usuario en Evento
class EventRegistration(models.Model):
    evento = models.ForeignKey(Event, on_delete=models.CASCADE)
    usuario = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    registrado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('evento', 'usuario')

    def __str__(self) -> str:
        return f"{self.usuario.username} registrado en {self.evento.nombre}"

# Comentario en Evento
class EventComment(models.Model):
    evento = models.ForeignKey(Event, on_delete=models.CASCADE)
    usuario = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    comentario = models.TextField()
    creado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Comentario de {self.usuario.username} en {self.evento.nombre}"

