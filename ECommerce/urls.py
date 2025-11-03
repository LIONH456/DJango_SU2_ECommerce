"""
URL configuration for ECommerce project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns: path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('main.api_urls')),  # Main app API endpoints (removed v1)
    path('api/dashboard/', include('dashboard.api_urls')),  # Dashboard API endpoints (removed v1)
    path('', include('main.urls')),  # Main app views (for SSR)
    path('ecadmin/', include('dashboard.urls'))  # Dashboard views (for SSR)
]

# Add media files support during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # Django will automatically serve static files from STATICFILES_DIRS during development
