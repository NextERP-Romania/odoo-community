Extend the inventory document of `nexterp_stock_inventory` for shops that
keep their goods at shelf price, as `l10n_ro_stock_account_retail`
books them.

In a retail warehouse account **371 Mărfuri** carries the PVA, not the
cost: the commercial markup sits on **378 Diferențe de preț la mărfuri**
and the VAT included in the shelf price on **4428 TVA neexigibilă**. A
counted difference therefore moves three accounts, and the *proces
verbal de inventariere* has to show all three — a document stating only
the cost cannot be reconciled against the shop's trial balance.

This module states the differences of a shop at the PVA — the summary
per location, the differences and their totals — and prints what each
of them is made of in a section of its own: the cost, the markup and
the deferred VAT. They are valued exactly the way the adjustment will
book them: a surplus from the shelf price the shop charges today, a
shortage from what the markup ledger carries, prorated over the
quantity carrying it.
