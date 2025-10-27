"""
Vistas de la aplicación de eventos.

Este módulo contiene las vistas basadas en clases para gestionar:
- Página principal con eventos destacados y recientes
- Listado de eventos
- Detalle de eventos con comentarios
- Registro de usuarios en eventos
- Creación de comentarios en eventos
"""

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views import View

from .models import Event, EventComment, EventRegistration


class HomeView(View):
    """
    Vista principal de la aplicación.

    Muestra los eventos destacados y más recientes en la página de inicio.
    """

    def get(self, request):
        destacados = Event.objects.filter(destacado=True, activo=True).order_by("-fecha_inicio")[:5]
        recientes = Event.objects.filter(activo=True).order_by("-creado_en")[:5]
        context = {
            "destacados": destacados,
            "recientes": recientes,
        }
        return render(request, "home.html", context)


class EventListView(View):
    """
    Vista de listado de eventos.

    Muestra todos los eventos activos con filtros por tipo de evento,
    eventos destacados, próximos eventos y eventos populares.
    """

    def get(self, request):
        # Obtener filtro de tipo de evento
        tipo_evento = request.GET.get("tipo", "")

        # Query base de eventos activos
        eventos_query = Event.objects.filter(activo=True)

        # Filtrar por tipo si se especifica
        if tipo_evento:
            eventos_query = eventos_query.filter(tipo=tipo_evento)

        # Eventos destacados (máximo 4)
        destacados = eventos_query.filter(destacado=True).order_by("-fecha_inicio")[:4]

        # Próximos eventos (ordenados por fecha, máximo 6)
        ahora = timezone.now()
        upcoming = eventos_query.filter(fecha_inicio__gte=ahora).order_by("fecha_inicio")[:6]

        # Eventos populares (ordenados por número de registros, máximo 5)
        populares = (
            Event.objects.filter(activo=True)
            .annotate(num_registros=Count("registrations"))
            .order_by("-num_registros")[:5]
        )

        # Tipos de eventos disponibles con conteo
        tipos_eventos = []
        for tipo_choice in Event.TipoEvento.choices:
            tipo_code = tipo_choice[0]
            tipo_label = tipo_choice[1]
            count = Event.objects.filter(activo=True, tipo=tipo_code).count()
            tipos_eventos.append(
                {
                    "code": tipo_code,
                    "label": tipo_label,
                    "count": count,
                }
            )

        # Total de eventos
        total_eventos = Event.objects.filter(activo=True).count()

        context = {
            "destacados": destacados,
            "upcoming": upcoming,
            "populares": populares,
            "tipos_eventos": tipos_eventos,
            "total_eventos": total_eventos,
            "selected_tipo": tipo_evento,
        }

        return render(request, "events.html", context)


class EventDetailView(View):
    """
    Vista de detalle de un evento específico.

    Muestra toda la información del evento y sus comentarios.
    Retorna 404 si el evento no existe o no está activo.
    """

    def get(self, request, event_id):
        evento = get_object_or_404(Event, id=event_id, activo=True)

        # Verificar si el usuario ya está registrado
        ya_registrado = False
        if request.user.is_authenticated:
            ya_registrado = EventRegistration.objects.filter(
                evento=evento, usuario=request.user
            ).exists()

        context = {
            "evento": evento,
            "ya_registrado": ya_registrado,
        }
        return render(request, "event_detail.html", context)


class EventRegisterView(View):
    """
    Vista para registrar usuarios en eventos.

    Maneja el registro de usuarios autenticados en eventos.
    Valida:
    - Autenticación del usuario
    - Disponibilidad de espacios
    - Estado activo del evento
    - Registros duplicados
    """

    def post(self, request, event_id):
        # Requiere autenticación
        if not request.user.is_authenticated:
            messages.error(request, "Debes iniciar sesión para registrarte en un evento.")
            return redirect("login")

        evento = get_object_or_404(Event, id=event_id, activo=True)

        # Si el formulario solicita cancelación, eliminar el registro si existe
        if request.POST.get("cancel"):
            registro = EventRegistration.objects.filter(evento=evento, usuario=request.user).first()
            if registro:
                registro.delete()
                messages.success(request, f"Se canceló tu registro en {evento.nombre}.")
            else:
                messages.info(request, "No encontré un registro tuyo para cancelar.")
            return redirect("event_detail", event_id=event_id)

        # Si ya está registrado, informar
        if EventRegistration.objects.filter(evento=evento, usuario=request.user).exists():
            messages.info(request, f"Ya estás registrado en {evento.nombre}.")
            return redirect("event_detail", event_id=event_id)

        # Verificar si puede registrarse (capacidad, evento activo, etc.)
        if not evento.puede_registrarse():
            if evento.esta_lleno():
                messages.error(request, f"El evento {evento.nombre} está lleno.")
            else:
                messages.error(request, f"El evento {evento.nombre} no acepta registros.")
            return redirect("event_detail", event_id=event_id)

        # Crear el registro
        try:
            EventRegistration.objects.create(evento=evento, usuario=request.user)
            messages.success(request, f"Te has registrado exitosamente en {evento.nombre}.")
        except Exception:
            # Si por alguna razón la creación falla (race condition), informar al usuario
            messages.error(request, "No fue posible completar el registro. Intenta nuevamente.")

        return redirect("event_detail", event_id=event_id)


class EventCommentView(View):
    """
    Vista para agregar comentarios a eventos.

    Permite a usuarios autenticados comentar en eventos activos.
    Valida:
    - Autenticación del usuario
    - Existencia y estado del evento
    - Contenido no vacío del comentario
    """

    def post(self, request, event_id):
        if not request.user.is_authenticated:
            messages.error(request, "Debes iniciar sesión para comentar en un evento.")
            return redirect("login")

        evento = get_object_or_404(Event, id=event_id, activo=True)
        comentario_texto = request.POST.get("comentario", "").strip()

        if comentario_texto:
            EventComment.objects.create(
                evento=evento, usuario=request.user, comentario=comentario_texto
            )
            messages.success(request, "Tu comentario ha sido agregado.")
        else:
            messages.error(request, "El comentario no puede estar vacío.")

        return redirect("event_detail", event_id=event_id)


class LoginView(View):
    """
    Vista para el inicio de sesión de usuarios.
    """

    def get(self, request):
        # Si ya está autenticado, redirigir al home
        if request.user.is_authenticated:
            return redirect("home")
        return render(request, "login.html")

    def post(self, request):
        username = request.POST.get("username")
        password = request.POST.get("password")

        # Autenticar usuario
        user = authenticate(request, username=username, password=password)

        if user is not None:
            # Login exitoso
            login(request, user)
            messages.success(request, f"¡Bienvenido de nuevo, {user.username}!")
            return redirect("home")
        else:
            # Login fallido
            messages.error(request, "Usuario o contraseña incorrectos.")
            return render(request, "login.html", {"error": "Credenciales inválidas"})


class RegisterView(View):
    """
    Vista para el registro de nuevos usuarios.
    """

    def get(self, request):
        return render(request, "register.html")

    def post(self, request):
        # Lógica de registro aquí
        pass
        return redirect("home")


class LogoutView(View):
    """
    Vista para cerrar sesión de usuarios.
    """

    def get(self, request):
        logout(request)
        messages.success(request, "Has cerrado sesión exitosamente.")
        return redirect("home")


class MyEventsView(View):
    """
    Vista para mostrar los eventos en los que el usuario está registrado.
    """

    def get(self, request):
        # Verificar que el usuario esté autenticado
        if not request.user.is_authenticated:
            messages.warning(request, "Debes iniciar sesión para ver tus eventos.")
            return redirect("login")

        # Obtener filtro de tipo de evento
        tipo_evento = request.GET.get("tipo", "")

        # Obtener todos los registros del usuario
        mis_registros = (
            EventRegistration.objects.filter(usuario=request.user)
            .select_related("evento")
            .order_by("-registrado_en")
        )

        # Filtrar por tipo si se especifica
        if tipo_evento:
            mis_registros = mis_registros.filter(evento__tipo=tipo_evento)

        # Obtener tipos de eventos con conteos
        tipos_eventos = []
        for tipo_code, tipo_label in Event.TipoEvento.choices:
            count = EventRegistration.objects.filter(
                usuario=request.user, evento__tipo=tipo_code
            ).count()
            if count > 0:
                tipos_eventos.append({"code": tipo_code, "label": tipo_label, "count": count})

        # Calcular estadísticas
        total_eventos = mis_registros.count()
        # Eventos que ya pasaron (asumimos que fueron asistidos)
        eventos_asistidos = mis_registros.filter(evento__fecha_fin__lt=timezone.now()).count()
        eventos_proximos = mis_registros.filter(evento__fecha_inicio__gte=timezone.now()).count()

        context = {
            "mis_eventos": mis_registros,
            "tipos_eventos": tipos_eventos,
            "total_eventos": total_eventos,
            "eventos_asistidos": eventos_asistidos,
            "eventos_proximos": eventos_proximos,
            "selected_tipo": tipo_evento,
            "now": timezone.now(),
        }

        return render(request, "my_events.html", context)
