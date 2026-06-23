==========================================
Fluxul eTransport (documentație detaliată)
==========================================

Acest document descrie, pas cu pas, fluxul complet de declarare eTransport
către ANAF așa cum este implementat de modulele NextERP peste localizarea
oficială Odoo. Se referă strict la comportamentul implementat în cod.

.. contents::
   :local:
   :depth: 2


1. Module implicate
===================

Fluxul este construit în straturi, fiecare modul adăugând peste cel anterior:

``l10n_ro_edi_stock`` (oficial Odoo)
    Baza: câmpurile eTransport pe ``stock.picking``, modelul
    ``l10n_ro_edi.document``, șablonul QWeb ``l10n_ro_template_etransport``,
    clientul HTTP ``ETransportAPI`` (autentificare OAuth2, ``upload_data``,
    ``get_status``) și fluxul trimitere / verificare status / corecție.

``l10n_ro_edi_stock_extension`` (NextERP)
    Corecții și completări pentru conformitate cu XSD v2 / Schematron v2.0.2:
    calcul corect al valorii (sursă de preț configurabilă), greutăți net/brut,
    cantitate + UoM consecvente, ``codTarifar`` (NC8), separare stradă/număr,
    validări stricte, documente de transport multiple, notificări anterioare
    (operațiuni 60/70), declarație post-avarie, acțiunile ANAF
    ștergere / confirmare / modificare vehicul, plus serviciile auxiliare
    LISTĂ și „informații operator de transport”.

``l10n_ro_edi_stock_batch`` (oficial Odoo)
    Aduce eTransport pe ``stock.picking.batch`` (transferuri în lot): o
    singură notificare pentru toate mișcările din lot.

``l10n_ro_edi_stock_batch_extension`` (NextERP)
    Aduce toate facilitățile din ``l10n_ro_edi_stock_extension`` și pe
    transferurile în lot (vezi secțiunea 9).


2. Modelul de date
==================

``l10n_ro_edi.document``
    Istoricul evenimentelor trimise la ANAF pentru un transfer. Fiecare
    trimitere/răspuns creează o înregistrare nouă; documentul „curent” este
    cel mai recent. Câmpuri relevante:

    * ``state`` – starea documentului (vezi secțiunea 3);
    * ``l10n_ro_edi_stock_uit`` – UIT-ul atribuit de ANAF;
    * ``l10n_ro_edi_stock_load_id`` – ``index_incarcare`` (id-ul de încărcare
      folosit la interogarea statusului);
    * ``attachment`` – XML-ul trimis (base64);
    * ``message`` – mesajul de eroare, când e cazul;
    * ``l10n_ro_edi_stock_event_type`` – tipul evenimentului ANAF
      (NOT / COR / DEL / CON / MVH);
    * ``picking_id`` **sau** ``batch_id`` – la ce transfer aparține.

``l10n.ro.edi.stock.document.line``
    Documentele de transport însoțitoare (CMR / factură / aviz / altele).
    Mai multe linii ⇒ mai multe elemente ``documenteTransport`` în XML.
    Legat prin ``picking_id`` sau ``batch_id``.

``l10n.ro.edi.stock.previous.notification``
    Notificările anterioare (``notificareAnterioara``), obligatorii pentru
    operațiunile 60 și 70. Legat prin ``picking_id`` sau ``batch_id``.

Câmpuri de date pe transfer (``stock.picking`` / ``stock.picking.batch``):
tip operațiune, scop operațiune, numere vehicul/remorci, tip locație
start/final (location / bcp / customs) și punctele/birourile aferente,
observații, sursa de preț, declarație post-avarie.


3. Stările documentului
=======================

Stări de bază (``l10n_ro_edi_stock``):

``stock_sent``
    XML trimis la ANAF, în curs de procesare (s-a primit ``index_incarcare``;
    pentru o trimitere nouă s-a primit deja și UIT).
``stock_sending_failed``
    Trimitere eșuată (eroare la validare locală sau eroare returnată de ANAF).
    Mesajul de eroare este în chatter și pe document.
``stock_validated``
    ANAF a confirmat declarația (``stare = ok``).

Stări adăugate de extensie (pentru evenimentele post-validare):

``stock_deleted``
    Notificare ștearsă la ANAF (eveniment DEL).
``stock_confirmed``
    Transport confirmat (eveniment CON).
``stock_vehicle_modified``
    Vehicul modificat (eveniment MVH).

Câmpurile de control al vizibilității butoanelor
(``l10n_ro_edi_stock_enable_send`` / ``_enable_fetch`` / ``_enable_amend``)
sunt calculate din starea curentă a documentului și din starea transferului.


4. Fluxul principal pentru un transfer (picking)
================================================

4.1 Pregătirea datelor
----------------------

Pe fila **eTransport** a transferului se completează:

* **Tip operațiune** (10–70) și **Scop operațiune** – lista scopurilor
  permise se restrânge automat în funcție de tipul de operațiune;
* **Vehicul** și, opțional, **Remorca 1 / Remorca 2** (numerele trebuie să
  fie unice între ele);
* **Locație start** și **Locație final** – fiecare poate fi de tip
  ``location`` (adresă), ``bcp`` (punct de trecere a frontierei) sau
  ``customs`` (birou vamal); tipurile disponibile depind de operațiune;
* **Documente de transport** (una sau mai multe linii);
* **Notificări anterioare** – doar la operațiunile 60/70;
* **Sursa de preț** pentru ``valoareLeiFaraTva`` (vezi secțiunea 6);
* **Declarație post-avarie** dacă se declară după restabilirea sistemului
  ANAF (OUG 41/2022 art. 8 alin. 1^3).

Transportatorul (``carrier_id``) trebuie să aibă un partener cu CUI, oraș și
stradă completate; validarea transportatorului se face la confirmarea
transferului.

4.2 Trimiterea inițială (Send)
------------------------------

La apăsarea **Send eTransport** (``send_type='send'``):

#. Se construiește dicționarul ``data`` cu toate câmpurile transferului.
#. **Validare locală** (``_l10n_ro_edi_stock_validate_data``) – vezi
   secțiunea 5. Dacă apar erori, se creează un document ``stock_sending_failed``
   cu mesajul agregat și fluxul se oprește.
#. **Generarea XML** din șablonul ``l10n_ro_template_etransport`` cu datele
   îmbogățite de extensie (``_l10n_ro_edi_stock_get_template_data``).
#. **Upload la ANAF** (``ETransportAPI().upload_data``).

   * La eroare ⇒ document ``stock_sending_failed`` (cu XML-ul atașat).
   * La succes ⇒ se șterg documentele vechi ``stock_sending_failed`` /
     ``stock_sent``, se citește UIT-ul din răspuns, se creează un document
     ``stock_sent`` și se atașează XML-ul în chatter.

4.3 Verificarea statusului (Fetch)
----------------------------------

La **Fetch Status** (disponibil cât timp documentul e ``stock_sent``):
se apelează ``ETransportAPI().get_status`` pe baza ``index_incarcare`` și,
în funcție de câmpul ``stare`` din răspuns:

* ``ok`` ⇒ document ``stock_validated``;
* ``in prelucrare`` ⇒ rămâne ``stock_sent`` (se reîncearcă mai târziu);
* ``XML cu erori nepreluat de sistem`` ⇒ ``stock_sending_failed``;
* altă valoare ⇒ se înregistrează în chatter ca stare netratată.

4.4 Corecția (Amend)
--------------------

Disponibilă când există un document ``stock_validated``. Retrimite declarația
cu același UIT, adăugând în XML elementul ``corectie`` (atributul ``uit``).
Mecanica de validare/upload este identică cu trimiterea inițială, dar UIT-ul
și ``index_incarcare`` provin din ultimul document validat.

4.5 Acțiuni post-validare (DEL / CON / MVH)
-------------------------------------------

Pe transferul cu UIT validat sunt disponibile trei acțiuni (wizard
``l10n.ro.edi.stock.action.wizard``), fiecare generând un XML dedicat și
creând un document cu starea și ``event_type`` corespunzătoare:

* **Ștergere notificare** (DEL) – element ``stergere`` ⇒ ``stock_deleted``;
* **Confirmare transport** (CON) – element ``confirmare`` cu tipul de
  confirmare (confirmat / parțial / refuzat) ⇒ ``stock_confirmed``;
* **Modificare vehicul** (MVH) – element ``modifVehicul`` cu noile numere și
  data modificării ⇒ ``stock_vehicle_modified``; numerele noi se scriu și pe
  transfer.

Toate trei acceptă opțional declarația post-avarie.


5. Validările stricte (Schematron v2.0.2)
=========================================

Peste validările de bază, extensia adaugă:

* **Scop vs. tip operațiune** – scopul trebuie să fie în lista permisă pentru
  tipul de operațiune (BR-068/069/070/205);
* **Cod țară partener** vs. operațiune (BR-004/005/006):

  * op. 30 (transport național) ⇒ partener din RO;
  * op. 10/12/14/20/22/24/60/70 ⇒ țară UE diferită de RO;
  * op. 40/50 (import/export) ⇒ țară din afara UE;

* **Date marfă obligatorii** (BR-206/207/208) pentru toate operațiunile cu
  excepția 60/70: ``codTarifar`` (NC8) prezent, greutate netă > 0 și valoare
  fără TVA > 0;
* **Greutăți** (BR-218/020/029): greutatea brută > 0 și ≥ greutatea netă;
* **Linii documente** – tipul documentului obligatoriu; la tipul „Altele”
  (9999) observațiile sunt obligatorii (BR-026); data documentului obligatorie;
* **Notificare anterioară** obligatorie la operațiunile 60/70.


6. Calculul valorii (sursa de preț)
===================================

``valoareLeiFaraTva`` se calculează în funcție de **sursa de preț** aleasă pe
transfer (sau implicita de pe companie):

``auto`` (implicit)
    operațiuni de intrare / transfer intern ⇒ preț de cost;
    operațiuni de ieșire (și 30 la livrare) ⇒ preț de vânzare.
``cost``
    ``standard_price`` al produsului (sau valoarea contabilă a mișcării după
    validare); dacă e 0, cade pe prețul din comanda de achiziție.
``purchase``
    ``purchase.order.line.price_unit`` (cu fallback pe cost).
``sale``
    ``sale.order.line.price_unit`` (cu fallback pe ``list_price``).
``list``
    ``list_price`` al produsului.

Valorile în altă monedă sunt convertite în RON (moneda companiei) la data
programată a transferului.


7. Mărimi derivate per mișcare
==============================

* **Cantitate + UoM** – cantitatea și codul UNECE sunt emise în aceeași
  unitate de măsură (``move.product_uom``), pentru consecvență.
* **Greutate netă** – greutatea produsului × cantitatea în UoM-ul de bază.
* **Greutate brută** – greutatea netă + greutatea ambalajelor (din
  ``shipping_weight`` / ``base_weight`` al tipului de pachet, numărate o
  singură dată per pachet).
* **codTarifar (NC8)** – din ``intrastat_code_id`` al produsului, apoi al
  categoriei; se acceptă doar coduri de 4, 6 sau 8 cifre (fără ``00000000``).
* **Stradă / număr** – câmpul ``street`` este împărțit în ``denumireStrada``
  și ``numar`` (atribut separat în XML), cu ``street2`` în ``alteInfo``.


8. Locațiile (start / final)
============================

Pentru fiecare capăt al traseului:

* ``location`` ⇒ se emite ``locatie`` cu județ, localitate, stradă, număr,
  cod poștal și alte informații; partenerul-adresă este depozitul sau
  partenerul transferului, în funcție de sensul operațiunii;
* ``bcp`` ⇒ ``codPtf`` (punct de trecere a frontierei);
* ``customs`` ⇒ ``codBirouVamal`` (birou vamal).


9. Fluxul pe transferuri în lot (batch)
=======================================

Un transfer în lot generează **o singură** notificare eTransport pentru toate
mișcările din lot. Particularități:

* La finalizarea lotului se validează că **toate** transferurile au **același
  transportator** și **același partener comercial**.
* Câmpurile eTransport (tip/scop operațiune, vehicul, locații, observații,
  sursă preț, declarație post-avarie), liniile de documente de transport și
  notificările anterioare se completează **pe lot**.
* Butoanele **Send / Amend / Fetch Status** și acțiunile **Delete / Confirm /
  Modify vehicle** apar pe formularul lotului, cu aceeași semantică de stări
  ca la un transfer simplu.
* Reutilizarea logicii: la trimitere, lotul este expus prin context ca
  „înregistrare-sursă” (``_picking_record``), astfel încât validările stricte
  și îmbogățirea șablonului din ``l10n_ro_edi_stock_extension`` se aplică
  identic. Valoarea per mișcare folosește prețul preluat de pe transferul
  fiecărei mișcări (cost/achiziție/vânzare), dar **sursa de preț** și
  **sensul** sunt cele de pe lot.


10. Servicii ANAF auxiliare
===========================

**LISTĂ notificări** (``l10n.ro.edi.stock.list.wizard``)
    Interoghează ANAF pentru notificările din ultimele 1–60 de zile și le
    afișează (tip, stare, UIT, partener, transportator, vehicul, mesaje).
    Reconciliază automat după UIT cu transferurile/loturile din Odoo și
    înregistrează în chatter notificările cu erori.

**Sincronizare automată (cron)**
    Job-ul ``eTransport: ANAF notifications list sync`` (dezactivat implicit)
    rulează același serviciu LISTĂ pentru companiile RO cu sincronizare
    activată și loghează în chatter notificările cu erori, atât pe transferuri
    cât și pe loturi. Se configurează din setări (interval în zile + activare).

**Informații operator de transport**
    (``l10n.ro.edi.stock.transporter.info.wizard``) – interoghează ANAF pentru
    notificările în care compania figurează ca operator de transport.


11. Declarația post-avarie
==========================

Bifa **Post-Outage Declaration** adaugă atributul ``declPostAvarie="D"`` în
XML (la trimitere, la modificarea vehiculului și la ștergere). Se folosește
când declarația se transmite după restabilirea sistemului ANAF, conform
OUG 41/2022 art. 8 alin. 1^3 (până la sfârșitul zilei lucrătoare următoare).


12. Configurare
===============

* **Token ANAF** (``l10n_ro_edi_access_token``) – obligatoriu; se generează /
  completează în setările companiei.
* **Sursa de preț implicită** (``l10n_ro_edi_stock_default_price_source``) –
  valoarea inițială pentru transferuri/loturi noi.
* **Sincronizare listă** – activare + număr de zile (1–60) pentru cron.
