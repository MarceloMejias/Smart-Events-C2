"""
URLs de la aplicación de eventos.

Define las rutas URL para las vistas de eventos:
- Página principal
- Listado de eventos
- Detalle de evento
- Registro en eventos
- Comentarios en eventos
"""

from django.urls import path

from .views import (
    EventDetailView,
    EventListView,
    EventRegisterView,
    HomeView,
    LoginView,
    LogoutView,
    MyEventsView,
    RegisterView,
)

urlpatterns = [
    # Página principal
    path("", HomeView.as_view(), name="home"),
    # Login y Registro de usuarios
    path("login/", LoginView.as_view(), name="login"),
    path("register/", RegisterView.as_view(), name="register"),
    path("logout/", LogoutView.as_view(), name="logout"),
    # Eventos
    path("events/", EventListView.as_view(), name="events"),
    path("events/<int:event_id>/", EventDetailView.as_view(), name="event_detail"),
    path("events/<int:event_id>/register/", EventRegisterView.as_view(), name="event_register"),
    path("my-events/", MyEventsView.as_view(), name="my_events"),
]
