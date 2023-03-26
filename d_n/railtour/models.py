from django.db import models
from django.contrib.postgres.fields import ArrayField
from datetime import timedelta
from .consts import *

class Stanice(models.Model):
    nazev = models.CharField(max_length=100)

    def __str__(self):
        return self.nazev

    @classmethod
    def get_nazev(cls, id):
        if id == SPANEK:
            return 'Spánek'
        stanice = cls.objects.get(id=id)
        return stanice.nazev

class Kraj(models.IntegerChoices):
    L = 1, 'Liberecký'
    U = 2, 'Ústecký'
    K = 3, 'Karlovarský'
    P = 4, 'Plzeňský'
    C = 5, 'Jihočeský'
    S = 6, 'Středočeský'
    H = 7, 'Královehradecký'
    E = 8, 'Pardubický'
    J = 9, 'Vysočina'
    B = 10, 'Jihomoravský'
    Z = 11, 'Zlínský'
    M = 12, 'Olomoucký'
    T = 13, 'Moravskoslezský'
    HE = 14, 'Horské etapy'

class Checkpoint(Stanice):
    is_active = models.BooleanField(default=False)
    cas_premie1 = models.DateTimeField(default=STARTTIME)
    cas_premie2 = models.DateTimeField(default=STARTTIME)
    body = models.PositiveIntegerField()
    assoc_text = models.CharField(max_length=200)
    do_cile = models.DateTimeField(default=CILTIME)
    kraj = models.IntegerField(choices=Kraj.choices)
    presun = models.DurationField(default=timedelta(0))

class Presun(models.Model):
    od = models.ForeignKey(Checkpoint, on_delete=models.CASCADE, related_name='presun_od')
    do = models.ForeignKey(Checkpoint, on_delete=models.CASCADE, related_name='presun_do')
    km = models.FloatField()
    doba = models.DurationField()

class Hrana(models.Model):
    od = models.ForeignKey(Checkpoint, on_delete=models.CASCADE, related_name='hrana_od')
    do = models.ForeignKey(Checkpoint, on_delete=models.CASCADE, related_name='hrana_do')
    km = models.FloatField()
    odjezd = models.TimeField()
    doba = models.DurationField()
    presun_do = models.DurationField()
    trasa = []

    def vypisSpoje(self):
        s = ''
        if not self.trasa:
            return s
        for spoj in self.trasa:
            strvlak = 'pěšky' if spoj.vlak == 0 else str(spoj.vlak)
            stanice = Stanice.objects.get(id=spoj.id)
            s += f' {stanice.nazev}, Odjezd  {spoj.odjezd}, Vlak {strvlak}<br>Příjezd {spoj.prijezd}'
        stanice = self.do
        s += f' {stanice.nazev}'
        return s

class Spoj(models.Model):
    od = models.ForeignKey(Stanice, on_delete=models.CASCADE, related_name='spoj_od')
    do = models.ForeignKey(Stanice, on_delete=models.CASCADE, related_name='spoj_do')
    vlak = models.CharField(max_length=10)
    odjezd = models.TimeField()
    prijezd = models.TimeField()
    hrana = models.ForeignKey(Hrana,on_delete=models.CASCADE)

class DHrana:
    def __init__(self, od, do, km, odjezd, doba, presun_do):
        self.od = od
        self.do = do
        self.km = km
        self.odjezd = odjezd
        self.doba = doba
        self.presun_do = presun_do
        self.trasa = []

class DSpoj:
    def __init__(self, id, vlak, odjezd, prijezd):
        self.id = id
        self.vlak = vlak
        self.odjezd = odjezd
        self.prijezd = prijezd

    def to_string(self):
        return str(self.vlak)+'--'+str(self.odjezd)+'-'+str(self.prijezd)

class Zadani(models.Model):
    od = models.ForeignKey(Checkpoint,on_delete=models.CASCADE)
    cas = models.DateTimeField()
    body = models.PositiveIntegerField()
    km = models.FloatField()
    mintime = models.DateTimeField()
    maxtime = models.DateTimeField()
    visited = ArrayField(models.IntegerField(), blank=True)
    spanek = models.BooleanField()
    usepremie = models.BooleanField()
    tempvisited = ArrayField(models.IntegerField(), blank=True)
    temptime = models.PositiveIntegerField()
    do = ArrayField(models.IntegerField(), blank=True)
    kroku = models.IntegerField()
    koef_unavy = models.FloatField()
    limitpocet = models.IntegerField()
    limitvykon = models.FloatField()
    kmcelk = models.FloatField()
    C = models.FloatField()
    uroven = models.IntegerField()
    metoda = models.IntegerField(choices=[(1,"podle výkonu 1"),(2,"podle výkonu 2")])
    spanekod = models.IntegerField()
    spanekdo = models.IntegerField()
    kraje = ArrayField(models.IntegerField(), blank=True)
    postupka = ArrayField(models.IntegerField(choices=[(2,'2'),(3,'3'),(4,'4'),(5,'5'),(6,'6'),(7,'7')]), blank=True)
    level = models.IntegerField()
    pocet_tras = models.IntegerField()

