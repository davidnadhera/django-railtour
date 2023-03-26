from django.shortcuts import render, redirect, reverse
from django.http import HttpResponse, HttpResponseRedirect
import csv
from .models import Stanice, Checkpoint, Kraj, Presun, Hrana, Spoj, DSpoj, Zadani
from datetime import timedelta, datetime, time, date
import json
from .utils import handle_timedelta, add_time, time_diff
import pickle
from .rtschema import build_schema
from .consts import STARTTIME, CILTIME, PRAHA, ROWS_PER_PAGE, SPANEK
from .Railtour import Railtour


def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")

def import_stanice(request):
    with open('railtour/data/data-stanice.csv', newline='', encoding="utf8") as csvfile:
        reader = csv.DictReader(csvfile)
        stanice=''
        for row in reader:
            stanice+=row['idstanice']+' '+row['nazev']+'\n'
            Stanice.objects.create(id=int(row['idstanice']),nazev=row['nazev'])
    return HttpResponse(stanice)

def import_checkpoint(request):
    with open('railtour/data/data-checkpointy.csv', newline='', encoding="utf8") as csvfile:
        reader = csv.DictReader(csvfile)
        stanice=''
        for row in reader:
            stanice+=row['idstanice']+' '+row['nazev']+'\n'
            Checkpoint.objects.create(id=int(row['idstanice']),
                                      nazev=row['nazev'],
                                      doba_premie1=timedelta(hours=int(row['dobapremie1'])),
                                      doba_premie2=timedelta(hours=int(row['dobapremie2'])),
                                      body=row['body'],
                                      assocText='',
                                      do_cile=CILTIME,
                                      kraj=row['kraj'])
    return HttpResponse(stanice)

def import_presuny(request):
    with open('railtour/data/data-presuny.csv', newline='', encoding="utf8") as csvfile:
        reader = csv.DictReader(csvfile)
        stanice=''
        for row in reader:
            stanice+=row['od']+' '+row['do']+'\n'
            t = datetime.strptime(row['cas'].strip(' "'), "%H:%M:%S")
            od = Checkpoint.objects.get(id=int(row['od']))
            do = Checkpoint.objects.get(id=int(row['do']))
            Presun.objects.create(od=od,do=do,km=float(row['km'].strip(' "')),
                                  doba=timedelta(hours=t.hour, minutes=t.minute, seconds=t.second))
    return HttpResponse(stanice)

def import_hrany(request):
    for i in list(range(3000,3297))+[3333]:
        with open(f'railtour/data/json_data/hrany{i}.json', 'r') as handle:
            seznam = json.load(handle)
            for cil in seznam:
                for trasa in seznam[cil]:
                    spoje = trasa['trasa']
                    hrana = Hrana.objects.create(od_id=i,
                                         do_id=cil,
                                         km=trasa['km'],
                                         odjezd=time.fromisoformat(trasa['odjezd'].strip(' "')),
                                         doba=handle_timedelta(trasa['doba']),
                                         presun_do=handle_timedelta(trasa['presundo']))
                    for spoj in spoje:
                        vlak = spoj['vlak']
                        strvlak = 'pěšky' if vlak == 0 else str(spoj['vlak'])
                        Spoj.objects.create(od_id=spoj['od'], do_id=spoj['do'], vlak=strvlak,
                                            odjezd=time.fromisoformat(spoj['odjezd']),
                                            prijezd=time.fromisoformat(spoj['prijezd']),
                                            hrana=hrana)
    return HttpResponse('OK')

def import_spoj(request):
    stanice_id = Stanice.objects.values_list('id',flat=True)
    spoj_list = {}
    idhrany = 1
    for id in stanice_id:
        spoj_list[id] = {}
    for i in list(range(3000,3297))+[3333]:
        with open(f'railtour/data/json_data/hrany{i}.json', 'r') as handle:
            seznam = json.load(handle)
        hrany = {}
        for cil in seznam:
            hrany[int(cil)] = []
            for trasa in seznam[cil]:
                spoje = trasa['trasa']
                hrana = Hrana(id=idhrany,
                             od_id=i,
                             do_id=int(cil),
                             km=float(trasa['km']),
                             odjezd=time.fromisoformat(trasa['odjezd'].strip(' "')),
                             doba=handle_timedelta(trasa['doba']),
                             presun_do=handle_timedelta(trasa['presundo']))
                idhrany += 1
                hrana.trasa = []
                # hrana = DHrana(i, cil, trasa['km'], time.fromisoformat(trasa['odjezd'].strip(' "')),
                #                handle_timedelta(trasa['doba']), handle_timedelta(trasa['presundo']))
                for spoj in spoje:
                    cls_spoj = DSpoj(int(spoj['od']),
                                     int(spoj['vlak']),
                                     time.fromisoformat(spoj['odjezd']),
                                     time.fromisoformat(spoj['prijezd']))
                    if cls_spoj.to_string() not in spoj_list[int(spoj['od'])]:
                        spoj_list[int(spoj['od'])][cls_spoj.to_string()] = cls_spoj
                    else:
                        cls_spoj = spoj_list[int(spoj['od'])][cls_spoj.to_string()]
                    hrana.trasa.append(cls_spoj)
                hrany[int(cil)].append(hrana)

        with open(f'railtour/data/hrany/hrany{i}.pickle', 'wb+') as handle:
            pickle.dump(hrany, handle, protocol=pickle.HIGHEST_PROTOCOL)
    return HttpResponse('OK')

def spojeni(request):
    stanice_list = Checkpoint.objects.filter(is_active=True).order_by('id')
    od = int(request.GET.get('od',0))
    do = int(request.GET.get('do',0))
    hrany = []
    if od and do:
        with open(f'railtour/data/graf.pickle', 'rb') as handle:
            graf = pickle.load(handle)
        hrany = graf.get(od,[]).get(do,[])
        for hrana in hrany:
            hrana.prijezd = add_time(hrana.odjezd, hrana.doba)
            hrana.vykon1 = round(hrana.do.body / hrana.doba.total_seconds() * 3600, 2)
            hrana.vykon2 = round(hrana.do.body - hrana.doba.total_seconds() / 3600, 2)
            hrana.doba = str(hrana.doba)[:-3]
    return render(request, 'railtour/spojeni.html', {'chps': stanice_list, 'od': od, 'do': do, 'hrany': hrany})

def odjezdy(request):
    stanice_list = Checkpoint.objects.filter(is_active=True).order_by('id')
    od = int(request.POST.get('od',0))
    cas = time.fromisoformat(request.POST.get('cas', '00:00'))
    odjezd = int(request.POST.get('odjezd', 1))
    razeni = int(request.POST.get('razeni', 1))
    hrany = []
    if request.method == "POST":
        with open(f'railtour/data/graf.pickle', 'rb') as handle:
            graf = pickle.load(handle)
        if odjezd == 1:
            odjezdy = graf.get(od,dict())
            for cil in odjezdy:
                if cil_hrany := odjezdy[cil]:
                    for hrana in cil_hrany:
                        if hrana.odjezd >= cas:
                            hrana.druhydeno = 0
                            hrany.append(hrana)
                            break
                    else:
                        hrana = cil_hrany[0]
                        hrana.druhydeno = 1
                        hrany.append(hrana)
        else:
            for start in graf:
                odjezdy = graf[start]
                if od in odjezdy:
                    if cil_hrany := odjezdy[od]:
                        for hrana in sorted(cil_hrany, key=lambda x: (add_time(x.odjezd,x.doba),-x.doba.total_seconds()), reverse=True):
                            if add_time(hrana.odjezd,hrana.doba) <= cas:
                                hrana.druhydenp = 0
                                hrany.append(hrana)
                                break
                        else:
                            hrana = cil_hrany[-1]
                            hrana.druhydenp = -1
                            hrany.append(hrana)
        for hrana in hrany:
            hrana.prijezd = add_time(hrana.odjezd, hrana.doba)
            if hrana.prijezd < hrana.odjezd:
                if odjezd == 1:
                    hrana.druhydenp = hrana.druhydeno + 1
                else:
                    hrana.druhydeno = hrana.druhydenp - 1
            else:
                if odjezd == 1:
                    hrana.druhydenp = hrana.druhydeno
                else:
                    hrana.druhydeno = hrana.druhydenp
            if odjezd == 1:
                hrana.doba = hrana.doba + time_diff(hrana.odjezd,cas)
            else:
                hrana.doba = time_diff(cas, hrana.odjezd)
            hrana.vykon1 = round(hrana.do.body / hrana.doba.total_seconds() * 3600, 2)
            hrana.vykon2 = round(hrana.do.body - hrana.doba.total_seconds() / 3600, 2)
            hrana.doba = str(hrana.doba)[:-3]
        match razeni:
            case 1:
                hrany.sort(key=lambda x: (x.druhydenp, x.prijezd))
            case 2:
                hrany.sort(key=lambda x: (x.druhydeno, x.odjezd))
            case 3:
                hrany.sort(key=lambda x: (x.druhydenp, x.prijezd), reverse=True)
            case 4:
                hrany.sort(key=lambda x: (x.druhydeno, x.odjezd), reverse=True)
            case 5:
                hrany.sort(key=lambda x: -x.vykon1)
            case 6:
                hrany.sort(key=lambda x: -x.vykon2)
        request.method = 'GET'
    return render(request, 'railtour/odjezdy.html', {'chps': stanice_list, 'od': od, 'cas': cas,
                                                     'odjezd': odjezd, 'razeni': razeni, 'hrany': hrany})

def detail(request, start, cil, id):
    with open(f'railtour/data/hrany/hrany{start}.pickle', 'rb') as handle:
        seznam = pickle.load(handle)
    hrany = seznam[cil]
    spoje = []
    for hrana in hrany:
        if hrana.id == id:
            spoje = hrana.trasa
            break
    modif_spoje = []
    for spoj in spoje:
        strvlak = 'pěšky' if spoj.vlak == 0 else str(spoj.vlak)
        stanice = Stanice.objects.get(id=spoj.id)
        modif_spoje.append({'odjezd': spoj.odjezd,
                            'stanice': stanice.nazev,
                            'vlak': strvlak,
                            'prijezd': spoj.prijezd})
    cil_stanice = Stanice.objects.get(id=cil)
    return render(request, 'railtour/detail.html', {'spoje': modif_spoje, 'cil': cil_stanice.nazev})

def detail_trasy(request, id):
    with open(f'railtour/data/vysledky.pickle', 'rb') as handle:
        vysledky = pickle.load(handle)
    zadani = Zadani.objects.last()
    cas = zadani.cas
    for vysledek in vysledky:
        if vysledek.id == id:
            hrany = vysledek.hrany
            break
    else:
        return HttpResponse('')
    modif_hrany = []
    for idstanice,hrana in hrany.items():
        if hrana[0].odjezd >= cas.time():
            cas = datetime.combine(cas.date(), hrana[0].odjezd)
        else:
            cas = datetime.combine(cas.date(), hrana[0].odjezd)+timedelta(days=1)
        modif_hrany.append({'nazev_od': hrana[0].od.nazev,
                            'nazev_do': hrana[0].do.nazev,
                            'odjezd': cas,
                            'prijezd': cas+hrana[0].doba,
                            'od_id': hrana[0].od_id,
                            'do_id': hrana[0].do_id,
                            'id': hrana[0].id,
                            'body': hrana[1],
                            'km': hrana[0].km,
                            'body_premie': hrana[2],
                            'body_kraje': hrana[3],
                            'body_inday': hrana[4],
                            'body_postupka': hrana[5]})
    return render(request, 'railtour/detail_trasy.html', {'hrany': modif_hrany, 'id': id})

def stanice(request):
    stanice_list = {}
    kraje = Kraj.choices
    for i,_ in kraje:
        stanice_list[i] = Checkpoint.objects.filter(kraj=i).order_by('-is_active','id')
    return render(request, 'railtour/stanice.html', {'stanice_list': stanice_list, 'kraje': kraje})

def stanice_graph(request):
    stanice_list = Checkpoint.objects.filter(is_active=True).values_list('id',flat=True)
    graf = {}
    for i in stanice_list:
        if i==3334:
            continue
        podgraf = {}
        with open(f'railtour/data/hrany/hrany{i}.pickle', 'rb') as handle:
            seznam = pickle.load(handle)
        for j in stanice_list:
            podgraf[j] = seznam[j]
        graf[i] = podgraf

    with open('railtour/data/graf.pickle', 'wb') as handle:
        pickle.dump(graf, handle, protocol=pickle.HIGHEST_PROTOCOL)
    return redirect('railtour:stanice')

def stanice_schema(request):
    build_schema()
    return redirect('railtour:stanice')

def change_doba1(request):
    id = request.POST['id']
    new_doba = datetime.fromisostring(request.POST['doba'])
    checkpoint = Checkpoint.objects.get(id=id)
    checkpoint.cas_premie1 = new_doba
    checkpoint.save()
    return HttpResponse("")

def change_doba2(request):
    id = request.POST['id']
    new_doba = datetime.fromisostring(request.POST['doba'])
    checkpoint = Checkpoint.objects.get(id=id)
    checkpoint.cas_premie2 = new_doba
    checkpoint.save()
    return HttpResponse("")

def change_active(request):
    id = request.POST['id']
    is_active = int(request.POST['active'])
    checkpoint = Checkpoint.objects.get(id=id)
    checkpoint.is_active = (is_active == 1)
    today = datetime.today().date()
    if today > STARTTIME.date():
        rozdil1 = checkpoint.cas_premie1 - STARTTIME
        rozdil2 = checkpoint.cas_premie2 - STARTTIME
        checkpoint.cas_premie1 = today + rozdil1
        checkpoint.cas_premie2 = today + rozdil2
    checkpoint.save()
    return HttpResponse("")

def iterace(request):
    zadani = Zadani.objects.last()
    return HttpResponse(f'{zadani.level};{zadani.pocet_tras}')

def zastavit(request):
    zadani = Zadani.objects.last()
    zadani.level = -1
    zadani.save()
    return HttpResponse('')

def pocet_tras(request):
    praha = (request.POST.get('Praha',False) == '1')
    od = [int(x) for x in request.POST.getlist('start[]',[])]
    do = [int(x) for x in request.POST.getlist('cil[]',[])]
    with open('railtour/data/vysledky.pickle', 'rb') as handle:
        vysledky = pickle.load(handle)
    if praha:
        vysledky = [x for x in vysledky if PRAHA in x.hrany]
    if od:
        vysledky = [x for x in vysledky if list(x.hrany)[0] in od]
    if do:
        vysledky = [x for x in vysledky if list(x.hrany)[-1] in do]
    return HttpResponse(len(vysledky))


def fetch_trasy(request):
    praha = (request.POST.get('Praha',False) == '1')
    od = [int(x) for x in request.POST.getlist('start[]',[])]
    do = [int(x) for x in request.POST.getlist('cil[]',[])]
    row = int(request.POST.get('row', 0))
    razeni = int(request.POST.get('razeni', 1))
    with open('railtour/data/vysledky.pickle', 'rb') as handle:
        vysledky = pickle.load(handle)
    if praha:
        vysledky = [x for x in vysledky if PRAHA in x.hrany]
    if od:
        vysledky = [x for x in vysledky if list(x.hrany)[0] in od]
    if do:
        vysledky = [x for x in vysledky if list(x.hrany)[-1] in do]
    if razeni == 1:
        vysledky.sort(key=lambda x: (-x.vykon, -x.body, x.km))
    elif razeni == 2:
        vysledky.sort(key=lambda x: (-x.body, -x.vykon, x.km))
    elif razeni == 3:
        vysledky.sort(key=lambda x: (-x.body_premie, -x.vykon, -x.body, x.km))
    elif razeni == 4:
        vysledky.sort(key=lambda x: (-x.body+x.body_premie, -x.vykon, -x.body, x.km))
    elif razeni == 5:
        vysledky2 = {}
        for vysledek in vysledky:
            if (list(vysledek.hrany)[0] not in vysledky2) or (vysledky2[list(vysledek.hrany)[0]].vykon < vysledek.vykon):
                vysledky2[list(vysledek.hrany)[0]] = vysledek
        vysledky = list(vysledky2.values())
        vysledky.sort(key=lambda x: (-x.body, -x.vykon, x.km))
    elif razeni == 6:
        vysledky2 = {}
        for vysledek in vysledky:
            if (list(vysledek.hrany)[-1] not in vysledky2) or (vysledky2[list(vysledek.hrany)[-1]].vykon < vysledek.vykon):
                vysledky2[list(vysledek.hrany)[-1]] = vysledek
        vysledky = list(vysledky2.values())
        vysledky.sort(key=lambda x: (-x.body, -x.vykon, x.km))

    vysledky = vysledky[row:row+ROWS_PER_PAGE]

    modif_vysledky = []
    for vysledek in vysledky:
        cil = Stanice.objects.get(id=list(vysledek.hrany)[-1])
        if cil.id == SPANEK:
            cil = Stanice.objects.get(id=list(vysledek.hrany)[-2])
        prvni = Stanice.objects.get(id=list(vysledek.hrany)[0])
        if len(vysledek.hrany) > 1:
            druhy = Stanice.objects.get(id=list(vysledek.hrany)[1])
            druhy_nazev = druhy.nazev
        else:
            druhy_nazev = ''
        modif_vysledky.append({'checkpoint': cil.nazev,
                               'prijezd': vysledek.cas,
                               'body': str(vysledek.body)+' ('+str(vysledek.body_premie)+')',
                               'km': round(vysledek.km,1),
                               'vykon': round(vysledek.vykon,2),
                               'spanek': 'ano' if SPANEK in vysledek.hrany else 'ne',
                               'prvni': prvni.nazev,
                               'druhy': druhy_nazev,
                               'id': vysledek.id})

    return render(request, 'railtour/vypis_tras.html', {'vysledky': modif_vysledky})

def trasy(request):
    stanice_list = Checkpoint.objects.filter(is_active=True).order_by('id')
    kraje = Kraj.choices[:-1]
    zadani = Zadani.objects.last()
    return render(request, 'railtour/trasy.html', {'chps': stanice_list, 'kraje': kraje,
                                                   'zadani': zadani})

def vypocet_tras(request):
    od = int(request.POST.get('od',3333))
    cas1 = request.POST.get('cas1',STARTTIME.strftime('%Y-%m-%d'))
    cas2 = request.POST.get('cas2',STARTTIME.strftime('%H:%M'))
    cas = datetime.combine(datetime.strptime(cas1,'%Y-%m-%d').date(),datetime.strptime(cas2,'%H:%M').time())
    visited = [int(x) for x in request.POST.getlist('visited[]',list())]
    tempvisited = [int(x) for x in request.POST.getlist('tempvisited[]', list())]
    do = [int(x) for x in request.POST.getlist('cil[]',[3334])]
    body = int(request.POST.get('body',0))
    km = float(request.POST.get('km',0))
    spanek = (request.POST.get('spanek',False) == '1')
    mintime1 = request.POST.get('mintime1',STARTTIME.strftime('%Y-%m-%d'))
    mintime2 = request.POST.get('mintime2',STARTTIME.strftime('%H:%M'))
    mintime = datetime.combine(datetime.strptime(mintime1,'%Y-%m-%d').date(),datetime.strptime(mintime2,'%H:%M').time())
    maxtime1 = request.POST.get('maxtime1',STARTTIME.strftime('%Y-%m-%d'))
    maxtime2 = request.POST.get('maxtime2',STARTTIME.strftime('%H:%M'))
    maxtime = datetime.combine(datetime.strptime(maxtime1,'%Y-%m-%d').date(),datetime.strptime(maxtime2,'%H:%M').time())
    kroku = int(request.POST.get('kroku', 1000))
    koef_unavy = float(request.POST.get('koef_unavy', 0))
    uroven = int(request.POST.get('uroven', 0))
    kmcelk = float(request.POST.get('kmcelk', 185))
    C = float(request.POST.get('C', 0.25))
    temptime = int(request.POST.get('temptime', 0))
    metoda = int(request.POST.get('metoda', 1))
    limitpocet = int(request.POST.get('limitpocet', 20))
    limitvykon = float(request.POST.get('limitvykon', 0))
    usepremie = (request.POST.get('usepremie',False) == '1')
    nemazat = (request.POST.get('nemazat',False) == '1')
    spanekod = int(request.POST.get('spanekod', 0))
    spanekdo = int(request.POST.get('spanekdo', 103))
    kraje = [int(x) for x in request.POST.getlist('kraje[]', list())]
    postupka = [int(x) for x in request.POST.getlist('postupka[]', list())]

    zadani = Zadani.objects.last()
    zadani.od_id = od
    zadani.cas = cas
    zadani.visited = visited
    zadani.tempvisited = tempvisited
    zadani.do = do
    zadani.body = body
    zadani.km = km
    zadani.spanek = spanek
    zadani.mintime = mintime
    zadani.maxtime = maxtime
    zadani.kroku = kroku
    zadani.koef_unavy = koef_unavy
    zadani.uroven = uroven
    zadani.kmcelk = kmcelk
    zadani.C = C
    zadani.temptime = temptime
    zadani.metoda = metoda
    zadani.limitpocet = limitpocet
    zadani.limitvykon = limitvykon
    zadani.usepremie = usepremie
    zadani.spanekod = spanekod
    zadani.spanekdo = spanekdo
    zadani.kraje = kraje
    zadani.postupka = postupka
    if not nemazat:
        zadani.level = 0
        zadani.pocet_tras = 0

    zadani.save()
    rt = Railtour(zadani)
    rt.rt_schema(nemazat)
    return HttpResponse('')

