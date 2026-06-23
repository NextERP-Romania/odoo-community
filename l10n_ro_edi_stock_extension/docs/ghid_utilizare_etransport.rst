======================================================
Ghid de utilizare eTransport (configurare și situații)
======================================================

Ghid practic pentru configurarea și operarea declarațiilor eTransport către
ANAF din Odoo. Descrie pas cu pas configurarea inițială și toate situațiile
de lucru (per tip de operațiune, transferuri în lot, corecții, acțiuni pe UIT,
erori frecvente). Pentru detalii tehnice despre flux vezi
``docs/flux_etransport.rst``.

.. contents::
   :local:
   :depth: 2


1. Configurare inițială
=======================

1.1 Token de acces ANAF (per companie)
---------------------------------------

Obligatoriu. Fără el nicio declarație nu poate fi trimisă.

* În **Setări → Contabilitate / Inventar**, la secțiunea de localizare română
  (eTransport), generați sau completați **token-ul de acces ANAF**
  (``l10n_ro_edi_access_token``).
* Token-ul se obține prin autorizare OAuth în SPV-ul ANAF; este valabil pe
  companie și are termen de expirare (se reînnoiește din aceleași setări).

1.2 Transportatorul (curier)
----------------------------

eTransport se declară doar pentru transferurile care au un **transportator**
(``carrier_id``). Pe transportator:

* completați **partenerul de transport** (``l10n_ro_edi_stock_partner_id``);
* partenerul de transport trebuie să aibă **CUI**, **oraș** și **stradă**.

La confirmarea unui transfer eligibil, lipsa transportatorului sau a
partenerului de transport oprește validarea cu mesaj explicit.

1.3 Produsele
-------------

Pentru ca declarația să fie validă (mai puțin op. 60/70), fiecare produs are
nevoie de:

* **Cod tarifar NC8** – ``intrastat_code_id`` pe produs (sau pe categoria de
  produs); se acceptă coduri de 4, 6 sau 8 cifre. Fără cod valid, declarația
  este respinsă (nu se mai trimite ``00000000``).
* **Greutate** – pentru calculul greutății nete și brute; greutatea netă
  trebuie să fie > 0.
* **Preț** – în funcție de sursa de preț aleasă (cost, achiziție, vânzare sau
  preț de listă); valoarea fără TVA trebuie să fie > 0.

1.4 Adresele (depozit și parteneri)
-----------------------------------

Când o locație (start sau final) este de tip **adresă** (``location``),
partenerul corespunzător (depozitul sau partenerul transferului) trebuie să
aibă, pentru capătul din România: **județ, oraș, stradă și cod poștal**, iar
țara să fie România.

1.5 Setări eTransport suplimentare
----------------------------------

În același bloc de setări (adăugate de extensie):

* **Sursa de preț implicită** – valoarea inițială pentru transferuri noi
  (vezi secțiunea 4);
* **Sincronizare automată listă** – activează job-ul cron care interoghează
  periodic ANAF (vezi secțiunea 9);
* **Zile sincronizare listă** – intervalul interogat (1–60 de zile).


2. Pregătirea unui transfer (câmpuri comune)
============================================

Pe orice transfer eligibil (companie RO, tip transfer ≠ intern) apare fila
**eTransport**. Câmpuri comune tuturor situațiilor:

* **Tip operațiune** (10–70) – determină ce scopuri și ce tipuri de locație
  sunt permise;
* **Scop operațiune** – lista se filtrează automat după tipul de operațiune;
* **Vehicul** și opțional **Remorca 1 / Remorca 2** – numerele trebuie să fie
  unice între ele;
* **Locație start / Locație final** – fiecare de tip adresă / punct de
  frontieră / birou vamal;
* **Documente de transport** – cel puțin un rând (vezi secțiunea 8);
* **Observații**;
* **Sursa de preț** și, opțional, **Declarație post-avarie**.

.. note::

   Câmpurile devin needitabile (read-only) cât timp documentul este în starea
   „trimis, în procesare” (``stock_sent``).


3. Situații per tip de operațiune
=================================

Pentru fiecare operațiune sunt indicate: sensul, tipurile de locație
disponibile, cerința privind codul de țară al partenerului comercial, scopurile
permise și dacă datele de marfă (NC8 / greutate netă / valoare) sunt
obligatorii.

3.1 Transport național (30)
---------------------------

* Sens: intern, în România.
* Partener comercial: **din RO** (persoanele fizice fără cod TVA sunt marcate
  ``PF``).
* Locații: doar **adresă**.
* Scopuri permise: 101, 704 (transfer între gestiuni), 705 (bunuri puse la
  dispoziția clientului), 9901.
* Date marfă: **obligatorii**.

3.2 Achiziție intracomunitară (10)
----------------------------------

* Sens: intrare în RO dintr-un stat UE.
* Partener comercial: **țară UE, diferită de RO**.
* Locație start: **adresă / punct de frontieră**; locație final: adresă /
  punct de frontieră.
* Scopuri permise: 101, 201, 301, 401, 501, 601, 703, 801, 802, 901, 1001,
  1101, 9901.
* Date marfă: **obligatorii**.

3.3 Livrare intracomunitară (20)
--------------------------------

* Sens: ieșire din RO către un stat UE.
* Partener comercial: **țară UE, diferită de RO**.
* Locație final: **adresă / punct de frontieră**.
* Scopuri permise: 101, 301, 703, 801, 802, 9901.
* Date marfă: **obligatorii**.

3.4 Lohn UE – intrare (12) / ieșire (22)
----------------------------------------

* Operațiuni în sistem lohn cu un stat UE.
* Partener comercial: **țară UE, diferită de RO**.
* Locații: 12 – start adresă/frontieră; 22 – final adresă/frontieră.
* Scop permis: 9999 (același cu operațiunea).
* Date marfă: **obligatorii**.

3.5 Call-off stock – intrare (14) / ieșire (24)
-----------------------------------------------

* Stocuri la dispoziția clientului.
* Partener comercial: **țară UE, diferită de RO**.
* Locații: 14 – start adresă/frontieră; 24 – final adresă/frontieră.
* Scop permis: 9999.
* Date marfă: **obligatorii**.

3.6 Import (40)
---------------

* Sens: intrare în RO din afara UE.
* Partener comercial: **țară din afara UE**.
* Locație start: **adresă / punct de frontieră / birou vamal**.
* Scop permis: 9999.
* Date marfă: **obligatorii**.

3.7 Export (50)
---------------

* Sens: ieșire din RO către afara UE.
* Partener comercial: **țară din afara UE**.
* Locație final: **adresă / punct de frontieră / birou vamal**.
* Scop permis: 9999.
* Date marfă: **obligatorii**.

3.8 Stocare / formare transport nou – intrare (60) / ieșire (70)
----------------------------------------------------------------

* Tranzacții intracomunitare cu stocare/formare de transport nou.
* Partener comercial: **țară UE, diferită de RO**.
* Locații: 60 – start adresă/frontieră; 70 – final adresă/frontieră.
* Scop permis: 9999.
* **Notificare anterioară: obligatorie** (cel puțin un rând în
  „Notificări anterioare”, cu UIT-ul anterior).
* Date marfă: **opționale** (NC8 / greutate netă / valoare pot lipsi).


4. Sursa de preț (valoarea fără TVA)
====================================

``valoareLeiFaraTva`` se calculează după sursa aleasă pe transfer (sau după
implicita de pe companie):

* **Automat** – intrare/transfer intern: preț de cost; ieșire (și 30 la
  livrare): preț de vânzare.
* **Preț de cost** – ``standard_price`` (sau valoarea mișcării după validare);
  dacă e 0, cade pe prețul din comanda de achiziție.
* **Preț comandă de achiziție** – din linia de PO (fallback pe cost).
* **Preț comandă de vânzare** – din linia de SO (fallback pe prețul de listă).
* **Preț de listă** – ``list_price``.

Valorile în altă monedă se convertesc automat în RON la data programată a
transferului.


5. Trimitere, verificare, corecție
==================================

5.1 Trimitere
-------------

Butonul **Send eTransport** validează datele local, generează XML-ul și îl
încarcă la ANAF. Rezultatul:

* erori de validare locală sau eroare ANAF ⇒ stare **eroare**
  (mesajul apare pe document și în chatter);
* succes ⇒ se primește **UIT**-ul, starea devine **trimis (în procesare)** și
  XML-ul se atașează în chatter.

5.2 Verificare status
---------------------

Butonul **Fetch Status** interoghează ANAF:

* confirmat ⇒ stare **validat**;
* în prelucrare ⇒ rămâne **trimis** (reîncercați mai târziu);
* XML cu erori ⇒ stare **eroare**.

5.3 Corecție
------------

Butonul **Amend eTransport** (disponibil după validare) retrimite declarația
pe **același UIT**, cu element de corecție în XML. Util pentru corectarea
datelor după validare.


6. Acțiuni pe UIT: ștergere, confirmare, modificare vehicul
===========================================================

Pe un transfer cu UIT **validat** apar trei butoane (deschid un wizard):

* **Ștergere notificare** – anulează notificarea la ANAF; cere confirmare.
* **Confirmare transport** – cu tip confirmare: confirmat / parțial confirmat /
  refuzat.
* **Modificare vehicul** – noul număr de vehicul (și remorci) + data
  modificării; numerele noi se salvează și pe transfer.

Fiecare acțiune poate fi marcată ca **post-avarie** și lasă o urmă în istoricul
de documente eTransport (cu tipul de eveniment DEL / CON / MVH).


7. Declarația post-avarie
=========================

Bifa **Declarație post-avarie** se folosește când declarația se transmite după
restabilirea sistemului ANAF (OUG 41/2022 art. 8 alin. 1^3 – până la sfârșitul
zilei lucrătoare următoare). Adaugă marcajul corespunzător în XML la trimitere,
la modificarea vehiculului și la ștergere.


8. Documente de transport multiple
==================================

În secțiunea **Documente de transport** se pot adăuga mai multe rânduri, fiecare
cu:

* **Tip document**: 10 CMR / 20 Factură / 30 Aviz / 9999 Altele;
* **Număr document** (implicit numele transferului dacă e gol);
* **Data documentului** (obligatorie);
* **Observații** – **obligatorii** când tipul este „Altele (9999)”.

Fiecare rând devine un element ``documenteTransport`` în XML.


9. Transferuri în lot (batch)
=============================

Un transfer în lot generează **o singură** declarație eTransport pentru toate
mișcările din lot.

**Condiții la finalizarea lotului:**

* toate transferurile din lot trebuie să aibă **același transportator**;
* toate trebuie să aibă **același partener comercial**.

**Cum se lucrează:**

#. Adăugați transferurile în lot și finalizați-l.
#. Pe fila **eTransport** a lotului completați aceleași câmpuri ca la un
   transfer simplu (tip/scop operațiune, vehicul, locații, documente de
   transport, notificări anterioare, sursă preț, post-avarie).
#. Folosiți butoanele **Send / Amend / Fetch Status** de pe lot.
#. Acțiunile **Ștergere / Confirmare / Modificare vehicul** sunt disponibile pe
   formularul lotului, ca la transferuri.

Lista loturilor are filtre după starea eTransport (eroare / trimis / validat)
și un buton de **Fetch Status** în antet.


10. Servicii ANAF auxiliare
===========================

10.1 Listă notificări
---------------------

Meniu: **Inventar → … → „eTransport notifications list”**. Interoghează ANAF
pentru notificările din ultimele 1–60 de zile și le afișează (tip, stare, UIT,
partener, transportator, vehicul, mesaje). Reconciliază automat după UIT cu
transferurile/loturile din Odoo și loghează în chatter notificările cu erori.

10.2 Sincronizare automată (cron)
---------------------------------

Job-ul **„eTransport: ANAF notifications list sync”** (dezactivat implicit)
rulează același serviciu pentru companiile RO cu sincronizare activată și
loghează în chatter notificările cu erori, atât pe transferuri cât și pe loturi.
Se configurează din setări (activare + număr de zile).

10.3 Informații ca operator de transport
-----------------------------------------

Meniu: **Inventar → … → „Notifications as transport operator”**. Interoghează
ANAF pentru notificările în care compania figurează ca operator de transport
(după CUI operator, opțional CUI declarant / UIT / referință).


11. Erori frecvente și rezolvare
================================

Mesajele apar la trimitere, pe document și în chatter.

* **„Romanian access token not found…”** – completați/regenerați token-ul ANAF
  (1.1).
* **„The delivery carrier … is missing the partner field value.”** – setați
  partenerul de transport pe transportator (1.2).
* **„The delivery carrier partner is missing the VAT/City/Street field.”** –
  completați datele partenerului de transport.
* **„Operation type / scope is missing.”** – completați tipul, respectiv scopul
  operațiunii.
* **„Operation scope … is not allowed for type …”** – alegeți un scop din lista
  permisă pentru tipul respectiv (secțiunea 3).
* **„Vehicle number is missing.” / „… must be unique.”** – completați numărul
  de vehicul; numerele vehicul/remorci trebuie să fie distincte.
* **„… must be from RO / must be EU and different from RO / must be outside the
  EU.”** – corectați țara partenerului comercial conform operațiunii
  (secțiunea 3).
* **„The following products are missing a tariff (NC8) code: …”** – completați
  ``intrastat_code_id`` pe produs/categorie (1.3).
* **„The following products have 0 net weight: …”** – completați greutatea
  produsului.
* **„The following products have 0 value (check the price source): …”** –
  verificați sursa de preț și prețul produsului (secțiunea 4).
* **„Gross weight must be > 0 … / must be >= net weight …”** – verificați
  greutatea și ambalajele.
* **„Document type / date is missing …” / „remarks … mandatory (BR-026).”** –
  completați liniile de documente de transport; la tipul „Altele (9999)”,
  observațiile sunt obligatorii (secțiunea 8).
* **„For operation … at least one previous notification is required.”** –
  adăugați notificarea anterioară la operațiunile 60/70 (3.8).
* **„… is missing the State/City/Street/Postal Code field.” / „Warehouse … should
  be in Romania.”** – completați adresa de depozit/partener pentru capătul din
  RO (1.4).
* **„All Pickings in a Batch Transfer should have the same Carrier / Commercial
  Partner.”** – uniformizați transportatorul și partenerul în lot (secțiunea 9).


12. Recapitulare: stări și butoane
==================================

* **(gol)** → se poate **Trimite**.
* **Trimis (în procesare)** → **Verifică status**; câmpurile sunt blocate.
* **Validat** → **Corecție**, **Ștergere**, **Confirmare**, **Modificare
  vehicul**.
* **Eroare** → corectați datele și **Trimiteți** din nou (sau **Corecție**,
  dacă există deja un document validat).
