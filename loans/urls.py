from django.urls import path
from . import views

urlpatterns = [
    path("", views.home_view, name="home"),
    path("consulta_individual/", views.consulta_individual_view, name="consulta_individual"),
    path("simular-escenario/", views.simular_escenario, name="simular_escenario"),
    path("consulta_lotes/", views.consulta_lotes_view, name="consulta_lotes"),
    path("reportes/", views.reportes_view, name="reportes"),
    path("reporte-global/", views.reporte_global_view, name="reporte_global"),
    path("guardar_consulta_individual/", views.guardar_consulta_individual, name="guardar_consulta_individual"),
    path("comprobar_cliente/", views.comprobar_cliente, name="comprobar_cliente"),
    path("descargar_resultados/", views.descargar_resultados, name="descargar_resultados"),
    path("generar-reporte/", views.generar_reporte, name="generar_reporte"),
    path("generar-reporte-lote/", views.generar_reporte_lote, name="generar_reporte_lote"),
    path("limpiar_sesion/", views.limpiar_sesion, name="limpiar_sesion"),
    path("limpiar_filtros/", views.limpiar_filtros, name="limpiar_filtros"),
]
