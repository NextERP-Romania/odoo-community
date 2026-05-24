==============================
Romania - E-Transport Extra
==============================

Modul de corecții și extensii pentru ``l10n_ro_edi_stock`` (oficial Odoo)
ca să fie aliniat cu specificația ANAF eTransport v2 (XSD 2023-01-26,
Schematron v2.0.2 din 2024-08-12).

Corecții față de modulul oficial
================================

* ``valoareLeiFaraTva`` se calculează diferit în funcție de operațiune:

  * incoming (10, 12, 14, 30 transfer, 40, 60): preț de cost din mișcare
    sau, dacă există PO, ``purchase.order.line.price_unit`` convertit în RON
  * outgoing (20, 22, 24, 30 vânzare, 50, 70): preț de vânzare din
    ``sale.order.line.price_unit`` convertit în RON sau ``list_price``

* Cantitatea este convertită corect între ``move.product_uom`` și UoM-ul
  declarat în ``codUnitateMasura``.

* Greutatea brută nu mai dublează ``shipping_weight`` când un colet are
  mai multe ``move_lines``; se garantează ``greutateBruta >= greutateNeta``.

* ``codTarifar`` devine obligatoriu (fără fallback ``00000000``).

* ``denumireStrada`` se separă de ``numar/bloc/scara/etaj/apartament``
  conform LocatieType din XSD.

Funcționalitate nouă
====================

* ``tipDocument`` selectabil (10 CMR / 20 Factură / 30 Aviz / 9999 Altele)
  cu multiple documente per notificare.

* ``notificareAnterioara`` pentru operațiunile 60/70 (DIN/DIE).

* ``declPostAvarie`` (declarație post-avarie sistem).

* Acțiuni complete pe UIT: ștergere, confirmare (10/20/30),
  modificare vehicul (MVH).

* Serviciu LISTA - sincronizare automată notificări (cron 6h).

* Serviciu INFO TRANSPORTATORI - vizualizare notificări pentru
  organizator transport.
