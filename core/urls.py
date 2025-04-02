from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from tour.views import *

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('tour.urls')),
]

# Static dosyalar için gerekli yapılandırma
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.DEBUG:
    urlpatterns += [
        path('__debug__/', include('debug_toolbar.urls')),
    ]
