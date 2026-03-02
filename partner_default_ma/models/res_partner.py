from odoo import models, api, _
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def default_get(self, fields_list):
        defaults = super().default_get(fields_list)
        if 'country_id' in fields_list and not defaults.get('country_id'):
            morocco = self.env.ref('base.ma', raise_if_not_found=False)
            if morocco:
                defaults['country_id'] = morocco.id
        return defaults

    def _get_immediate_payment_term(self):
        """Return the first 'Paiement immédiat' / 'Immediate' payment term found."""
        term = self.env['account.payment.term'].search(
            ['|',
             ('name', 'ilike', 'immédiat'),
             ('name', 'ilike', 'immediate')],
            limit=1,
        )
        return term

    @api.model_create_multi
    def create(self, vals_list):
        immediate_term = self._get_immediate_payment_term()
        morocco = self.env.ref('base.ma', raise_if_not_found=False)

        for vals in vals_list:
            # --- Block duplicate customer names ---
            name = (vals.get('name') or '').strip()
            if name:
                existing = self.with_context(active_test=True).search(
                    [('name', '=ilike', name), ('customer_rank', '>', 0)],
                    limit=1,
                )
                if existing:
                    raise ValidationError(
                        _('Un client avec le nom "%s" existe déjà (réf: %s).')
                        % (name, existing.ref or str(existing.id))
                    )

            # --- Default country = Morocco ---
            if not vals.get('country_id') and morocco:
                vals['country_id'] = morocco.id

            # --- Default payment terms = Paiement immédiat ---
            if immediate_term:
                if not vals.get('property_payment_term_id'):
                    vals['property_payment_term_id'] = immediate_term.id
                if not vals.get('property_payment_lock_term_id'):
                    vals['property_payment_lock_term_id'] = immediate_term.id

        return super().create(vals_list)
