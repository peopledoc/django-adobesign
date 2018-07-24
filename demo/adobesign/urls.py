"""demo URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path

from . import views

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('settings/update/<int:pk>/', views.SettingsUpdate.as_view(),
         name='update-settings'),
    path('settings/create', views.SettingsCreate.as_view(),
         name='create-settings'),
    path('token', views.TokenView.as_view(), name='token'),
    path('refresh_token', views.RefreshTokenView.as_view(),
         name='refresh_token'),
    path('signature', views.CreateSignatureView.as_view(), name='signature'),
    path('signer', views.CreateSigner.as_view(), name='signer'),
    path('sign/<int:pk>', views.Sign.as_view(), name='sign'),
]
