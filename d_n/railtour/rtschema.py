from datetime import date, time, datetime, timedelta
import pickle
import bisect
from .models import Checkpoint, Presun, Hrana, DSpoj
from .utils import add_time





IDPESKY = 9999
IDSPANEK = 9998
SPANEK = 3999

def build_schema(FULL=False):

    active = Checkpoint.objects.filter(is_active=True).values_list('id',flat=True)

    with open('railtour/data/graf.pickle', 'rb') as handle:
        graf = pickle.load(handle)

    pres = dict()
    for obj in Presun.objects.all():
        pres.setdefault(obj.od_id, []).append(obj)

    stan = Checkpoint.objects.in_bulk()


    vysledky = []
    zpracovat = []
    presuny = {}
    spanky = []

    for start_p in graf:
        for cil_p in graf[start_p]:
            for hrana in graf[start_p][cil_p]:
                prijezd = add_time(hrana.odjezd,hrana.doba)
                if (cil_p, prijezd) not in vysledky:
                    vysledky.append((cil_p, prijezd))

    if (3333, time(hour=9, minute=0)) not in vysledky:
        vysledky.append((3333, time(hour=9, minute=0)))

    if (3000, time(hour=8, minute=22)) not in vysledky:
        vysledky.append((3000, time(hour=8, minute=22)))

    if (3000, time(hour=20, minute=22)) not in vysledky:
        vysledky.append((3000, time(hour=20, minute=22)))

    for (idstanice, cas) in vysledky:
        if idstanice in pres:
            for presun in pres[idstanice]:
                new_stanice = presun.do_id
                if new_stanice not in active:
                    continue
                new_cas = add_time(cas, presun.doba)
                if ((new_stanice, new_cas) not in vysledky):
                    zpracovat.append((new_stanice, new_cas))
                    if (new_stanice, new_cas) not in presuny:
                        presuny[(new_stanice, new_cas)] = [idstanice]
                    else:
                        presuny[(new_stanice, new_cas)] = []

    while len(zpracovat):
        (idstanice, cas) = zpracovat.pop()
        if ((idstanice, cas) not in vysledky):
            vysledky.append((idstanice, cas))
        for presun in pres[idstanice]:
            new_stanice = presun.do_id
            if new_stanice not in active:
                continue
            curr_presuny = presuny[(idstanice, cas)]
            if new_stanice not in curr_presuny:
                new_cas = add_time(cas, presun.doba)
                if ((new_stanice, new_cas) not in vysledky) or (
                        ((new_stanice, new_cas) in presuny) and (presuny[(new_stanice, new_cas)] != [])):
                    zpracovat.append((new_stanice, new_cas))
                    if (new_stanice, new_cas) not in presuny:
                        presuny[(new_stanice, new_cas)] = [*curr_presuny, idstanice]
                    else:
                        presuny[(new_stanice, new_cas)] = []


    for (idstanice, cas) in vysledky:
        if (cas >= time(20, 0)) or (cas <= time(2, 0)):
            new_cas = add_time(cas, timedelta(hours=6))
            if (idstanice, new_cas) not in vysledky:
                spanky.append((idstanice, new_cas))

    for (idstanice, cas) in spanky:
        vysledky.append((idstanice, cas))
        if idstanice in pres:
            for presun in pres[idstanice]:
                new_stanice = presun.do_id
                if new_stanice not in active:
                    continue
                new_cas = add_time(cas, presun.doba)
                if ((new_stanice, new_cas) not in vysledky) or (
                        ((new_stanice, new_cas) in presuny) and (presuny[(new_stanice, new_cas)] != [])):
                    zpracovat.append((new_stanice, new_cas))
                    if (new_stanice, new_cas) not in presuny:
                        presuny[(new_stanice, new_cas)] = [idstanice]
                    else:
                        presuny[(new_stanice, new_cas)] = []


    while len(zpracovat):
        (idstanice, cas) = zpracovat.pop()
        if ((idstanice, cas) not in vysledky):
            vysledky.append((idstanice, cas))
        for presun in pres[idstanice]:
            new_stanice = presun.do_id
            if new_stanice not in active:
                continue
            curr_presuny = presuny[(idstanice, cas)]
            if new_stanice not in curr_presuny:
                new_cas = add_time(cas, presun.doba)
                if ((new_stanice, new_cas) not in vysledky) or (
                        ((new_stanice, new_cas) in presuny) and (presuny[(new_stanice, new_cas)] != [])):
                    zpracovat.append((new_stanice, new_cas))
                    if (new_stanice, new_cas) not in presuny:
                        presuny[(new_stanice, new_cas)] = [*curr_presuny, idstanice]
                    else:
                        presuny[(new_stanice, new_cas)] = []

    with open('railtour/data/stops.pickle', 'wb') as handle:
        pickle.dump(vysledky, handle, protocol=pickle.HIGHEST_PROTOCOL)
    stops = vysledky

    vysledky = {}
    x = 0
    kmsec = 185 / 103 / 60 / 60
    PENALE = 0.25

    for (idstanice, cas) in stops:
        x += 1
        # print(x)
        sousede = {}
        if idstanice != 3334:
            for cil, hrany in graf[idstanice].items():
                if len(hrany):
                    ind = bisect.bisect_left(hrany, cas, key=lambda x: x.odjezd)
                    if ind == len(hrany):
                        hrana = hrany[0]
                        new_cas = datetime.combine(date(2021, 8, 3), hrana.odjezd) + hrana.doba
                    else:
                        hrana = hrany[ind]
                        new_cas = datetime.combine(date(2021, 8, 2), hrana.odjezd) + hrana.doba
                    doba = new_cas - datetime.combine(date(2021, 8, 2), cas)
                    if (doba > timedelta(hours=9)) and (not FULL):
                        continue
                    penale = max(0, (hrana.km - kmsec * doba.total_seconds()) * PENALE)
                    vykon = (stan[cil].body - penale) / doba.total_seconds() * 60.0 * 60.0
                    sousede[cil] = (doba, hrana, vykon)

            if idstanice in pres:
                presuny = pres[idstanice]
                for nextstan in presuny:
                    cil = nextstan.do_id
                    if (cil in active):
                        doba = nextstan.doba
                        new_hrana = Hrana(od_id=idstanice,
                                          do_id=cil,
                                          km=nextstan.km,
                                          odjezd=cas,
                                          doba=doba,
                                          presun_do=timedelta(0))
                        new_hrana.trasa=[DSpoj(idstanice,0,cas,add_time(cas,nextstan.doba))]
                        penale = max(0, (float(new_hrana.km) - kmsec * doba.total_seconds()) * PENALE)
                        vykon = (stan[cil].body - penale) / doba.total_seconds() * 60.0 * 60.0
                        if (cil not in sousede) or (sousede[cil][2] < vykon):
                            sousede[cil] = (doba, new_hrana, vykon)

            if ((cas <= time(hour=2)) or (cas >= time(hour=20))):
                doba = timedelta(hours=6)
                new_hrana = Hrana(od_id=idstanice,
                                  do_id=idstanice,
                                  km=0,
                                  odjezd=cas,
                                  doba=timedelta(hours=6),
                                  presun_do=timedelta(0))
                new_hrana.trasa = []
                sousede[SPANEK] = (doba, new_hrana, 5.0 / 6.0)
            sousede = dict(sorted(sousede.items(), key=lambda item: item[1][2], reverse=True))
        vysledky[(idstanice, cas)] = sousede

    if not FULL:
        with open('railtour/data/schema.pickle', 'wb') as handle:
            pickle.dump(vysledky, handle, protocol=pickle.HIGHEST_PROTOCOL)
    else:
        with open('railtour/data/schema_full.pickle', 'wb') as handle:
            pickle.dump(vysledky, handle, protocol=pickle.HIGHEST_PROTOCOL)