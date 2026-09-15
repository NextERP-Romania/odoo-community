# Changelog

## 19.0.3.0.0

- Moved out of `l10n-romania-enterprise`: nothing about keeping several
  sessions open is Romanian. The module keeps its name, so a database that
  already has it installed simply finds it in the new repository.
- Only the handling of several open sessions survives. The session-close
  invoice grouping is gone -- fiscal receipts now reach D394 and the sales
  journal through `l10n_ro_declaration_pos` -- and so are the refund
  workflow, the ANAF customer lookup and the generic POS customer.
- Multiple open sessions are switched on per register with
  **Multiple Open Sessions**, and start off. The old workflow flag gated the
  invoice grouping, so carrying it over would have turned multi-session on
  for registers that never asked for it.
- Core's one-session-per-register rule is lifted for registers that ask for
  it. Until now it was not, which is what made the rest of this module
  unreachable: the second session was never created.
