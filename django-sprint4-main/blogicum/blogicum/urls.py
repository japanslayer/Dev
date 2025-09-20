from django.contrib import admin
from django.urls import path, include
from pages import views as pages_views
from django.views.generic import TemplateView

urlpatterns = [
    path('pages/', include('pages.urls', namespace='pages')),
    path('auth/', include('django.contrib.auth.urls')),
    path('auth/registration/', pages_views.RegisterView.as_view(), name='registration'),
    path('admin/', admin.site.urls),
    path('', include('blog.urls', namespace='blog')),
]

handler404 = 'pages.views.page_not_found'
handler500 = 'pages.views.server_error'
