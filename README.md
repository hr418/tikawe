# Tapahtumakalenteri

## Sovelluksen toiminnot

- ✅ Käyttäjä pystyy luomaan tunnuksen ja kirjautumaan sisään sovellukseen.
- ✅ Käyttäjä pystyy lisäämään, muokkaamaan, poistamaan ja perumaan tapahtumia. Tapahtumalla on
  - ✅ ajankohta
  - ✅ kesto
  - ✅ otsikko
  - ✅ kuvaus
  - ✅ mahdollinen paikkamäärä
  - ✅ ilmoittautuneet
  - ✅ yksi tai useampi luokittelu
- ✅ Käyttäjä näkee sovellukseen lisätyt tapahtumat.
- ✅ Käyttäjä pystyy etsimään tapahtumia
  - ✅ hakusanalla (otsikko)
  - ✅ alku-ajankohdalla
  - ✅ luokittelulla
- ✅ Sovelluksessa on käyttäjäsivut, jotka näyttävät tilastoja ja käyttäjän lisäämät tapahtumat.
- ✅ Käyttäjä pystyy ilmoittautumaan tapahtumaan.
- ✅ Käyttäjä pystyy perumaan ilmoittautumisensa.

## Sovelluksen asennus

Asenna `flask`-kirjasto:

```
$ pip install flask
```

Luo tietokannan taulut ja lisää alkutiedot:

```
$ sqlite3 database.db < schema.sql
$ sqlite3 database.db < init.sql
```

Voit käynnistää sovelluksen näin:

```
$ flask run
```

## Sovelluksen suorituskyky

Suorituskykyä voi testata ajamalla `seed.py`. Tiedosto lisää tietokantaan 1000 käyttäjää, 10^5 tapahtumaa sekä tapahtumiin yhteensä (noin) 10^6 osallistujaa. Tapahtumilla on myös satunnaisesti luokkia. Luokalla on 50% mahdollisuus kuulua tapahtumaan.

Tapahtumien lisääminen, muokkaus, ilmoittautuminen, kirjautuminen, käyttäjän lisääminen yms ovat nopeita ~ 0.01 s.\
Etusivun lataaminen kestää ~ 4.11 s.\
Käyttäjäsivun lataaminen kestää ~ 0.15 s.\
Haku kaikille tapahtumille joissa on luku 5 otsikossa (40951 kpl) kestää ~ 1.9 s.\
Haku kaikille tapahtumille jotka ovat luokiteltu maksullisiksi (24978 kpl) kestää ~ 0.89 s.\
Haku tapahtumalle jolla on otsikossa 12345 (1 kpl) kestää ~ 0.02 s.

Kyselyt jotka käsittelevät pientä määrää dataa ovat siis hyvin nopeita tietokannan indeksien ansiosta. Kuitenkin koska sovelluksessa ei ole sivutusta (ainakaan vielä), ovat kyselyt jotka käsittelevät paljon dataa hitaita. Testattu prosessorilla Intel i3-1315U.
