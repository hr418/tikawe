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
