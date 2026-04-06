from django.urls import path
from .views import ProductoAPIView
from .views_auth import RegistroAPIView, LoginAPIView
from .views_perfil import PerfilImagenAPIView
from .solicitudes_views import SolicitudAPIView

urlpatterns = [
    # autenticación
    path('auth/registro/', RegistroAPIView.as_view(), name='api_registro'),
    path('auth/login/', LoginAPIView.as_view(), name='api_login'),

    # productos
    path('productos/', ProductoAPIView.as_view(), name='api_productos'),  # listar y crear
    path('productos/<str:producto_id>/', ProductoAPIView.as_view(), name='api_producto_detalle'),  # ver, actualizar o eliminar por id

    # perfil
    path('perfil/foto/', PerfilImagenAPIView.as_view(), name='api_perfil_foto'),
    path('solicitudes/', SolicitudAPIView.as_view(), name='solicitudes'),
]