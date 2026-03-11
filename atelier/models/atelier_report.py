from odoo import models, api, fields
from datetime import datetime, date, timedelta


class AtelierPointageReport(models.AbstractModel):
    _name = 'report.atelier.report_pointage_employee'
    _description = 'Rapport de pointage atelier'

    @api.model
    def _get_report_values(self, docids, data=None):
        employees = self.env['hr.employee'].browse(docids)
        data = data or {}

        # Période : jour ciblé (par défaut aujourd'hui)
        report_date_str = data.get('report_date')
        if report_date_str:
            try:
                report_date = datetime.strptime(report_date_str, '%Y-%m-%d').date()
            except Exception:
                report_date = date.today()
        else:
            report_date = date.today()

        day_start = datetime(report_date.year, report_date.month, report_date.day, 0, 0, 0)
        day_end   = datetime(report_date.year, report_date.month, report_date.day, 23, 59, 59)

        # Chercher les blocs pour chaque employé
        all_blocks = {}
        total_minutes_map = {}
        for emp in employees:
            blocks = self.env['mrp.workcenter.productivity'].search([
                ('employee_id', '=', emp.id),
                ('date_start', '>=', fields.Datetime.to_string(day_start)),
                ('date_start', '<=', fields.Datetime.to_string(day_end)),
            ], order='date_start asc')
            all_blocks[emp.id] = blocks
            total_minutes_map[emp.id] = sum(b.duration or 0 for b in blocks)

        now = datetime.now()
        return {
            'docs': employees,
            'blocks_map': all_blocks,
            'total_map': total_minutes_map,
            # Shortcuts for the template – the template uses 'blocks' and 'total_minutes'
            # but since we loop over docs we need a helper
            'blocks': all_blocks.get(docids[0] if docids else 0, []),
            'total_minutes': total_minutes_map.get(docids[0] if docids else 0, 0),
            'today_str': report_date.strftime('%d/%m/%Y'),
            'now_str': now.strftime('%d/%m/%Y %H:%M'),
            'context': data,
        }
