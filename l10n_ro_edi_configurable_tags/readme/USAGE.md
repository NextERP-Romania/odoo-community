Nothing to do on the invoice itself: the rules are applied every time the
CIUS-RO XML is generated, for the partner of the invoice.

When a contact of a company carries its own rules, it inherits those of the
company and refines them: of two rules writing the same node, the one of the
contact wins, and of a profile rule and a partner rule, the partner rule wins.

To replay a setup on another database, open the profile, copy the JSON on the
*JSON* tab, then on the target database create a profile and use *Import JSON*.

## Checking the result

Generate the XML as usual (*Send & Print*, or the ANAF button) and open the
attached `..._cius_ro.xml`. A rule marked as *Required* that produced no value
appears as a blocking error at that point, naming the rule and the partner.
