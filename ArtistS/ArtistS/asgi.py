import os
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack
import ArtistappS.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ArtistS.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            ArtistappS.routing.websocket_urlpatterns
        )
    ),
})
