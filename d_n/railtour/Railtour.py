from .railtour_schema import rt_schema_iterace
import pickle
from .consts import *
from datetime import timedelta
import heapdict
from .Trasa import Trasa
from .models import DHrana, DSpoj, Checkpoint, Zadani

class Railtour:
    aktivni = list(Checkpoint.objects.filter(is_active=True).values_list('id', flat=True))
    chps = Checkpoint.objects.in_bulk(aktivni)

    def countVykon1(self, trasa):
        doba = trasa.cas - STARTTIME
        doba = doba.total_seconds()
        # zbyva = CIL_DO - trasa.cas
        # if (zbyva < zlom) and trasa.hrany:
        #     idstanice = list(trasa.hrany)[-1]
        #     if idstanice == SPANEK:
        #         idstanice = list(trasa.hrany)[-2]
        #     penale_cil = (zlom-zbyva)/zlom*(CIL_DO-stan[idstanice]['docile'])
        # else:
        # if zbyva < zlom:
        #     penale = max(0,(trasa.km-kmsec*doba)*PENALE)
        # else:
        #     penale = (trasa.km-kmsec*doba)*PENALE
        penale = max(0, (trasa.km - self.kmsec * doba) * self.zadani.C)
        if doba:
            trasa.vykon = (trasa.body - penale) / doba * 60 * 60
        else:
            trasa.vykon = 0
        # trasa.vykon = trasa.vykon * (1+random.random()/5)

    def countVykon2(self, trasa):
        doba = trasa.cas - STARTTIME
        doba = doba.total_seconds()
        #    penale = max(0,(trasa.km-kmsec*doba)*PENALE)
        penale = (trasa.km - self.kmsec * doba) * self.zadani.C
        if doba:
            trasa.vykon = trasa.body - penale - doba / 60 / 60
        else:
            trasa.vykon = 0

    def countVykonF(self, trasa):
        if trasa.cas > CILTIME - timedelta(hours=4):
            doba = self.zadani.maxtime - STARTTIME
        else:
            doba = trasa.cas - STARTTIME
        doba = doba.total_seconds()
        penale = max(0, (trasa.km - self.zadani.kmcelk) * self.zadani.C)
        if doba:
            trasa.vykon = (trasa.body - penale) / doba * 60 * 60
        else:
            trasa.vykon = 0

    def __init__(self, zadani):
        self.zadani = zadani

        if not self.zadani.do:
            self.do = self.aktivni
        else:
            self.do = self.zadani.do

        self.blocktime = STARTTIME + timedelta(hours=zadani.temptime)
        self.spanek_od = STARTTIME + timedelta(hours=zadani.spanekod)
        self.spanek_do = STARTTIME + timedelta(hours=zadani.spanekdo)
        self.celkdoba = zadani.maxtime - STARTTIME
        self.zlom = self.celkdoba * 0.5

        self.kmsec = zadani.kmcelk / self.celkdoba.total_seconds()
        if zadani.metoda == 2:
            self.countVykon = self.countVykon2
        else:
            self.countVykon = self.countVykon1

    def presunHrana(idstanice, presun, cas):
        hrana = DHrana(presun.od, presun.do, presun.km, cas.time(), presun.doba, presun.doba)
        hrana.trasa = [DSpoj(idstanice, 0, cas.time(), (cas + presun.doba).time())]
        return hrana

    def spanekHrana(idstanice, cas):
        hrana = DHrana(idstanice, idstanice, 0, cas.time(), timedelta(hours=6), timedelta(0))
        hrana.trasa = []
        return hrana

    def rt_schema(self, nemazat):
        def rt_schema_iterace(iterace, x, schema, new_id):
            def getNewValues(new_cas, prev_cas, kraje, inday, body, cil, postupka):
                postupka1 = {2, 3, 4, 5}
                postupka2 = {3, 4, 5, 6}
                postupka3 = {4, 5, 6, 7}

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
                stanice = rt.chps[cil]
                idkraj = stanice.kraj
                if idkraj in range(1, 14):
                    new_kraje.add(idkraj)
                new_values['kraje'] = new_kraje
                new_values['inday'] = new_inday
                new_body = body + stanice.body
                if new_inday in [6, 7, 8, 9] and (cil != OLOMOUC):
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
                        (postupka1.issubset(new_postupka) or postupka2.issubset(new_postupka) or postupka3.issubset(
                            new_postupka)):
                    new_postupka.add(100)
                    new_body += 2
                    new_values['body_postupka'] = 2
                else:
                    new_values['body_postupka'] = 0
                new_postupka.add(stanice.body)
                new_values['postupka'] = new_postupka
                if zadani.usepremie and (new_cas <= stanice.cas_premie1):
                    new_body += 2
                    premie = 2
                elif zadani.usepremie and (new_cas <= stanice.cas_premie2):
                    new_body += 1
                    premie = 1
                else:
                    premie = 0
                new_values['body'] = new_body
                new_values['body_premie'] = premie
                return new_values

            pocet = 0
            new_iterace = heapdict.heapdict()

            while len(iterace) and (pocet < zadani.kroku):
                pocet += 1
                in_it = 0
                ((idstanice, frozen_visited), trasa) = iterace.popitem()
                visited = set(frozen_visited)
                if (idstanice, trasa.cas.time()) not in schema:
                    raise KeyError(trasa.Hlavicka())
                for cil, info in schema[(idstanice, trasa.cas.time())].items():
                    if (cil not in visited) and (cil not in zadani.visited) and \
                            ((trasa.cas >= rt.blocktime) or (cil not in zadani.tempvisited)) \
                            and (
                            (cil != SPANEK) or ((trasa.cas >= rt.spanek_od) and (trasa.cas <= rt.spanek_do))) \
                            and (trasa.cas <= zadani.maxtime):
                        (doba, hrana, vykon) = info
                        if (vykon < zadani.limitvykon) and (cil != OLOMOUC):
                            continue
                        new_cas = trasa.cas + doba
                        if (cil != SPANEK) and (cil != OLOMOUC) and (new_cas > rt.chps[cil].do_cile):
                            continue
                        in_it += 1
                        if (in_it > zadani.limitpocet) and (x > 1):
                            break
                        new_visited = visited.copy()
                        new_visited.add(cil)
                        if cil != SPANEK:
                            new_values = getNewValues(new_cas, trasa.cas, trasa.kraje, trasa.inday, trasa.body, cil,
                                                      trasa.postupka)
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
                        new_hrany[cil] = (
                        hrana, new_values['body'], new_values['body_premie'], new_values['body_kraje'],
                        new_values['body_inday'], new_values['body_postupka'])
                        new_trasa = Trasa(new_cas, new_values['body'], trasa.km + hrana.km,
                                          new_values['kraje'], new_hrany, countVykon, new_values['inday'],
                                          new_values['postupka'],trasa.body_premie+new_values['body_premie'],-1)
                        if cil == SPANEK:
                            cil_stanice = idstanice
                        else:
                            cil_stanice = cil
                        if (cil_stanice != OLOMOUC) and \
                                (((cil_stanice, frozenset(new_visited)) not in new_iterace)
                                 or (new_iterace[(cil_stanice, frozenset(new_visited))].vykon < new_trasa.vykon)):
                            new_iterace[(cil_stanice, frozenset(new_visited))] = new_trasa
                        if (new_cas <= zadani.maxtime) and (new_cas >= zadani.mintime) and (cil_stanice in zadani.do):
                            vysledky.append(Trasa(new_cas, new_values['body'], trasa.km + hrana.km,
                                                       new_values['kraje'], new_hrany, countVykonF,
                                                       new_values['inday'],
                                                       new_values['postupka'],trasa.body_premie+new_values['body_premie'],
                                                       new_id))
                            new_id += 1

            return (new_iterace, new_id)


        with open('railtour/data/schema.pickle', 'rb') as handle:
            schema = pickle.load(handle)

        iterace = heapdict.heapdict()
        countVykon = self.countVykon
        countVykonF = self.countVykonF
        if not nemazat:
            iterace[(START, frozenset([START]))] = Trasa(STARTTIME, 0, 0, set(), {}, countVykon, 0, set(), 0, -1)
        x = 0
        vysledky = []
        zadani = Zadani.objects.last()
        rt = self
        new_id = 1

        while len(iterace):
            x += 1
            (iterace, new_id) = rt_schema_iterace(iterace, x, schema, new_id)
            zadani2 = Zadani.objects.last()
            if zadani2.level > -1:
                zadani.level = x
                zadani.pocet_tras = len(iterace)
                zadani.save()
            else:
                break

        vysledky.sort(reverse=True, key=lambda x: (x.vykon, -x.km))
        vysledky = vysledky[:50000]
        zadani.level = -1
        zadani.pocet_tras = len(vysledky)
        zadani.save()

        with open(f'railtour/data/vysledky.pickle', 'wb') as handle:
            pickle.dump(vysledky, handle, protocol=pickle.HIGHEST_PROTOCOL)
