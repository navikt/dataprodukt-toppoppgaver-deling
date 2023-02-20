# Deling av svar fra toppoppgaver på nav.no

Dette er en mvp for å dele svar fra toppoppgavemålingen på nav.no med andre team i NAV

[main.py](main.py) sjekker om svarene inneholder kjente personopplysninger og fjerner disse før svarene deles med andre team.

Hvordan sjekker vi om det er personopplysninger i fritekstsvar?

Først skiller vi på kategorivariabler og svar som inneholder  fritekst. Dette skiller vi på ved å se på svaralternativene i spørreundersøkelsen.

Deretter sjekker vi om det er noen treff på fornavn eller etternavn blant fritekstsvarene som dukker opp i SSB sine navnelister.

Deretter bruker vi [Name Entity Recognition](https://en.wikipedia.org/wiki/Named-entity_recognition) (NER) fra Spacy-biblioteket. [Spacy](https://spacy.io/) er en modul for natural language processing, en gren innenfor maskinlæring. 

For hvert treff erstatter vi innholdet med en annen tekst for å kjennetegne hva slags data modellen har erstattet: Navn, telefonnummer og epost.

Deretter fører vi statistikk på antall treff totalt sett og som andel av fritekstsvarene for å kartlegge omfanget.

Merk at modellen er litt overivrig. Den prøver å finne treff blant ord som ligner navn, og derfor må vi lage unntak for ord som er verb, substantiv og navn. Disse ligger i filen [unntak](patterns/unntak.txt) i mappen "patterns".