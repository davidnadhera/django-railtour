from django.urls import path

from . import views

app_name = 'railtour'
urlpatterns = [
    path('', views.index, name='index'),
    path('import/stanice', views.import_stanice, name='import_stanice'),
    path('import/checkpoint', views.import_checkpoint, name='import_checkpoint'),
    path('import/presuny', views.import_presuny, name='import_presuny'),
    path('import/hrany', views.import_hrany, name='import_hrany'),
    path('import/spoj', views.import_spoj, name='import_spoj'),
    path('stanice', views.stanice, name='stanice'),
    path('stanice/graph', views.stanice_graph, name='stanice_graph'),
    path('stanice/schema', views.stanice_schema, name='stanice_schema'),
    path('spojeni', views.spojeni, name='spojeni'),
    path('odjezdy', views.odjezdy, name='odjezdy'),
    path('trasy', views.trasy, name='trasy'),
    path('detail/<int:start>/<int:cil>/<int:id>', views.detail, name='detail'),
    path('detail_trasy/<int:id>', views.detail_trasy, name='detail_trasy'),
    path('ajax/change_doba1', views.change_doba1, name='change_doba1'),
    path('ajax/change_doba2', views.change_doba2, name='change_doba2'),
    path('ajax/change_active', views.change_active, name='change_active'),
    path('ajax/iterace', views.iterace, name='iterace'),
    path('ajax/pocet_tras', views.pocet_tras, name='pocet_tras'),
    path('ajax/fetch_trasy', views.fetch_trasy, name='fetch_trasy'),
    path('ajax/zastavit', views.zastavit, name='zastavit'),
    path('ajax/vypocet_tras', views.vypocet_tras, name='vypocet_tras')
]