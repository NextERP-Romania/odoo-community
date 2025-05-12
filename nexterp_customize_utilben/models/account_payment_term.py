# -*- coding: utf-8 -*-

from odoo import api, fields, models, _, Command
from odoo.exceptions import UserError, ValidationError
from odoo.tools import format_date, formatLang, frozendict, date_utils
from odoo.tools.float_utils import float_round

from dateutil.relativedelta import relativedelta


class AccountPaymentTerm(models.Model):
    _inherit = "account.payment.term"
    _description = "Payment Terms"
    _order = "sequence, id"
    _check_company_domain = models.check_company_domain_parent_of

    

class AccountPaymentTermLine(models.Model):
    _inherit = "account.payment.term.line"
    _description = "Payment Terms Line"
    _order = "id"

   
        
    delay_type = fields.Selection(
             selection_add=[('day_of_the_month', 'Day of the current Month'),]
        , ondelete={"day_of_the_month": "cascade"},)
   

    def _get_due_date(self, date_ref):
        self.ensure_one()
        due_date = fields.Date.from_string(date_ref) or fields.Date.today()
        if self.delay_type == 'day_of_the_month':
            return date_utils.start_of(due_date, 'month') + relativedelta(days=self.nb_days)
        return super(AccountPaymentTermLine, self)._get_due_date(date_ref)
      

   
