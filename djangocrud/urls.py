"""
URL configuration for djangocrud project.

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
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from tasks import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.signin, name='signin'),
    path('home/', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('classes/', views.reserve_class, name='classes'),
    path('myreservations/', views.myreservations, name='myreservations'),
    path('myresults/', views.my_results, name='my_results'),
    path('signup/', views.signup, name='signup'),
    path('signout/', views.signout, name='signout'),
    path('signin/', views.signin, name='signin'),
    path('planificacion/', views.ver_planificacion, name='ver_planificacion'),
    path('perfil/', views.editar_perfil, name='editar_perfil'),
    path('crearplanificacion/', views.crear_planificacion,
         name='crear_planificacion'),
    path('gestionarroles/', views.gestionar_roles, name='gestionar_roles'),
    path('cancelar-reserva/<int:reserva_id>/',
         views.cancelar_reserva, name='cancelar_reserva'),
    path('gestionarsuscripciones/', views.gestionar_suscripciones,
         name='gestionar_suscripciones'),
    path('registrarpago/', views.registrar_pago,
         name='registrar_pago'),
    path('historialpagos/', views.historial_pagos, name='historial_pagos'),
    path('resultados/detalle/', views.detalle_resultados,
         name='detalle_resultados'),
    path('resultados/eliminar/<int:id>/',
         views.eliminar_levantamiento, name='eliminar_levantamiento'),
    path('gestionar_invitaciones/', views.gestionar_invitaciones,
         name='gestionar_invitaciones'),
    path('invitaciones/eliminar/<int:invitacion_id>/',
         views.eliminar_invitacion, name='eliminar_invitacion'),
    path('usuarios/eliminar/<int:usuario_id>/',
         views.eliminar_usuario, name='eliminar_usuario'),
]
