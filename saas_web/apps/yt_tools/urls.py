from django.urls import path

from . import views

app_name = 'yt_tools'

urlpatterns = [
    path('', views.ClipGenerateView.as_view(), name='generate'),
    path('<int:pk>/', views.ClipResultsView.as_view(), name='results'),
    path('<int:pk>/regenerate/', views.ClipRegenerateView.as_view(), name='regenerate'),
]
