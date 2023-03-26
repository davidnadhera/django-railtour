from datetime import datetime, date
from .models import Stanice, Checkpoint
import decimal

def make_date(x):
    return datetime.combine(date(2021, 6, 1), x)


class Trasa:
    def __init__(self, cas, body, km, kraje, hrany, countVykon, inday, postupka, body_premie, id):
        self.cas = cas
        self.body = body
        self.km = km
        self.kraje = kraje
        self.hrany = hrany
        self.countVykon = countVykon
        self.postupka = postupka
        self.inday = inday
        self.body_premie = body_premie
        self.countVykon(self)
        self.id = id

    def setBody(self, x):
        self.body = x
        self.countVykon(self)

    def setCas(self, x):
        self.cas = x
        self.countVykon(self)

    def __lt__(self, other):
        return self.vykon > other.vykon

    def vypisSpoje(self):
        for (hrana, body, body_premie, body_kraje, body_postupka, body_inday) in self.hrany.values():
            hrana.vypisSpoje(body, body_premie, body_kraje, body_postupka, body_inday)

    def Hlavicka(self):
        premie = [x[1] for x in self.hrany.values() if x[1] > 0]
        cil = Stanice.get_nazev(list(self.hrany.keys())[-1])
        return f'Stanice: {cil}, Cas: {self.cas}, '\
               f'Visited: {list(map(lambda x: Stanice.get_nazev(x), list(self.hrany.keys())))}, '\
               f'Body: {self.body}, Km: {round(self.km, 1)}, Vykon: {round(self.vykon, 2)}, '\
               f'Premie: {sum(premie)}'

    def vypisPointy(self):
        od = self.idstart
        for cil, (hrana, premie, koef_unavy) in self.hrany.items():
            if cil == 3999:
                cil = od
                body = 5
                odjezd = hrana.odjezd
                prijezd = hrana.prijezd
            elif len(hrana.trasa) <= 1:
                stanice = Checkpoint.objects.get(id=cil)
                body = stanice.body
                odjezd = hrana.odjezd
                prijezd = hrana.prijezd
            else:
                stanice = Checkpoint.objects.get(id=cil)
                body = stanice.body
                odjezd = make_date(hrana.odjezd)
                odjezd = odjezd.time()
                prijezd = make_date(hrana.prijezd)
                prijezd = prijezd.time()
            print(f'Od: {Stanice.get_nazev(od)}, Do: {Stanice.get_nazev(cil)}, Odjezd: {odjezd}, Prijezd: {prijezd}, '
                  f'Km: {round(hrana.km, 1)}, Body: {body}, Premie: {premie}')
            od = cil






