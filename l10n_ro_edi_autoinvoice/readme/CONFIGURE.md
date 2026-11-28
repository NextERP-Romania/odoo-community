1. Go to **Invoicing > Configuration > Settings**, section **Customer
   Invoices**, and check that **Create Customer Self-Invoices** is
   enabled for the company.
2. For every customer who issues self-invoices in your name, open
   **Invoicing > Configuration > Accounting > Journals** and create a
   journal with:
   - **Type**: *Sales*;
   - in the **Ro Auto Invoicing** group, **Ro Sequence Type**:
     *Customer Auto Invoicing*;
   - **Ro Partner**: the customer.
3. For the self-invoices you issue in a supplier's name, create a
   *Purchase* journal the same way, with **Ro Sequence Type**
   *Supplier Auto Invoicing* and the supplier as **Ro Partner**.

Without a journal for a customer, its self-invoices are created as drafts
in the first sales journal. The self-invoicing type and partner of a
journal can no longer be changed once the journal has posted entries.

The SPV connection itself (ANAF credentials) is the one set up for
e-Factura.
