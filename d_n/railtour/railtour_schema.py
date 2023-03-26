from datetime import timedelta
import heapdict
from .consts import *
from .Trasa import Trasa
from .models import DHrana, DSpoj, Checkpoint
import decimal

def presunHrana(idstanice,presun,cas):
    hrana = DHrana(presun.od,presun.do,presun.km,cas.time(),presun.doba,presun.doba)
    hrana.trasa = [DSpoj(idstanice,0,cas.time(),(cas+presun.doba).time())]
    return hrana

def spanekHrana(idstanice, cas):
    hrana = DHrana(idstanice, idstanice, 0, cas.time(), timedelta(hours=6), timedelta(0))
    hrana.trasa = []
    return hrana

def rt_schema_iterace(rt,iterace,x,schema):
    def getNewValues(new_cas,prev_cas,kraje,inday,body,cil,postupka):
        postupka1 = {2,3,4,5}
        postupka2 = {3,4,5,6}
        postupka3 = {4,5,6,7}

        druhyden = new_cas.date() > prev_cas.date()
        new_values = {}
        if druhyden:
            new_inday = 1
            new_kraje = set()
            new_postupka = set()
        else:
            new_inday = inday + 1
            new_kraje = kraje.copy()
            new_postupka = postupka.copy()
        stanice = Checkpoint.objects.get(id=cil)
        idkraj = stanice.kraj
        if idkraj in range(1,14):
            new_kraje.add(idkraj)
        new_values['kraje'] = new_kraje
        new_values['inday'] = new_inday
        new_body = body + stanice.body
        if new_inday in [6,7,8,9] and (cil != OLOMOUC):
            new_body += 1
            new_values['body_inday'] = 1
        else:
            new_values['body_inday'] = 0
        if (len(kraje) == 3) and (len(new_kraje) == 4):
            new_body += 2
            new_values['body_kraje'] = 2
        else:
            new_values['body_kraje'] = 0
        if (100 not in new_postupka) and \
            (postupka1.issubset(new_postupka) or postupka2.issubset(new_postupka) or postupka3.issubset(new_postupka)):
            new_postupka.add(100)
            new_body += 2
            new_values['body_postupka'] = 2
        else:
            new_values['body_postupka'] = 0
        new_postupka.add(stanice.body)
        new_values['postupka'] = new_postupka
        if rt.zadani.usepremie and (new_cas <= stanice.cas_premie1):
            new_body += 2
            premie = 2
        elif rt.zadani.usepremie and (new_cas <= stanice.cas_premie2):
            new_body += 1
            premie = 1
        else:
            premie = 0
        new_values['body'] = new_body
        new_values['body_premie'] = premie
        return new_values

    pocet = 0
    new_iterace = heapdict.heapdict()
    while len(iterace) and (pocet < rt.zadani.kroku):
        pocet += 1
        in_it = 0
        ((idstanice,frozen_visited),trasa) = iterace.popitem()
        visited = set(frozen_visited)
        if (idstanice,trasa.cas.time()) not in schema:
            raise KeyError(trasa.Hlavicka())
        for cil,info in schema[(idstanice,trasa.cas.time())].items():
            if (cil not in visited) and ((trasa.cas>=rt.blocktime) or (cil not in rt.zadani.tempvisited)) \
            and ((cil != SPANEK) or ((trasa.cas>=rt.spanek_od) and (trasa.cas<=rt.spanek_do))) \
            and (trasa.cas<=rt.zadani.maxtime):
                (doba,hrana,vykon) = info
                if (vykon<rt.zadani.limitvykon) and (cil != OLOMOUC):
                    continue
                new_cas = trasa.cas + doba
                if (cil != SPANEK) and (cil != OLOMOUC) and (new_cas > rt.chps[cil].do_cile):
                    continue
                in_it += 1
                if (in_it>rt.zadani.limitpocet) and (x>1):
                    break
                new_visited = visited.copy()
                new_visited.add(cil)
                if (cil != SPANEK):
                    new_values = getNewValues(new_cas,trasa.cas,trasa.kraje,trasa.inday,trasa.body,cil,trasa.postupka)
                else:
                    if new_cas.date() > trasa.cas.date():
                        new_inday = 0
                        new_kraje = set()
                        new_postupka = set()
                    else:
                        new_inday = trasa.inday
                        new_kraje = trasa.kraje
                        new_postupka = trasa.postupka
                    new_values = {}
                    new_values['kraje'] = new_kraje
                    new_values['inday'] = new_inday
                    new_values['postupka'] = new_postupka
                    new_values['body'] = trasa.body + 5
                    new_values['body_premie'] = 0
                    new_values['body_kraje'] = 0
                    new_values['body_inday'] = 0
                    new_values['body_postupka'] = 0
                new_hrany = trasa.hrany.copy()
                new_hrany[cil] = (hrana,new_values['body'],new_values['body_premie'],new_values['body_kraje'],
                                  new_values['body_inday'],new_values['body_postupka'])
                new_trasa = Trasa(new_cas,new_values['body'],trasa.km + hrana.km,
                                  new_values['kraje'],new_hrany,rt.countVykon,new_values['inday'],
                                  new_values['postupka'],trasa.body_premie+new_values['body_premie'])
                if cil == SPANEK:
                    cil_stanice = idstanice
                else:
                    cil_stanice = cil
                if (cil_stanice != OLOMOUC) and \
                (((cil_stanice,frozenset(new_visited)) not in new_iterace)
                or (new_iterace[(cil_stanice,frozenset(new_visited))].vykon < new_trasa.vykon)):
                    new_iterace[(cil_stanice,frozenset(new_visited))] = new_trasa
                if (new_cas <= rt.zadani.maxtime) and (new_cas >= rt.zadani.mintime) and (cil_stanice in rt.do):
                    rt.vysledky.append(Trasa(new_cas,new_values['body'],trasa.km + hrana.km,
                                  new_values['kraje'],new_hrany,rt.countVykonF,new_values['inday'],
                                  new_values['postupka'],trasa.body_premie))
            # elif (cil in CILS) and (((cil not in visited)) or (cil == OLOMOUC)):
            #     (doba,hrana,vykon) = info
            #     new_cas = trasa.cas + doba
            #     if ((new_cas > CIL_DO) or (new_cas < CIL_OD)) or ((cil != OLOMOUC)  and (new_cas > stan[cil]['docile'])):
            #         continue
            #     new_values = getNewValues(new_cas,trasa.cas,trasa.kraje,trasa.inday,trasa.body,cil,trasa.postupka)
            #     new_hrany = trasa.hrany.copy()
            #     new_hrany[cil] = (hrana,new_values['premie'],0)
            #     vysledky.append(Trasa(new_cas,trasa.idstart,new_values['body'],trasa.km + hrana.km,\
            #                       new_values['kraje'],new_hrany,countVykonF,new_values['inday'],0,\
            #                       new_values['postupka']))
    return new_iterace





