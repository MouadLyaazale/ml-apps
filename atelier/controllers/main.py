from odoo import http
from odoo.http import request
from odoo.exceptions import UserError
import logging
import calendar as cal_module
from datetime import datetime, date, timedelta
from psycopg2 import OperationalError as PG_OperationalError

_logger = logging.getLogger(__name__)


class AtelierController(http.Controller):

    # ═══════════════════════════════════════════════════════════════
    # Pages HTML
    # ═══════════════════════════════════════════════════════════════

    @http.route('/atelier', type='http', auth='public', website=False)
    def atelier_index(self, **kwargs):
        return request.render('atelier.kiosk_page', {})

    @http.route('/atelier/supervisor', type='http', auth='user', website=False)
    def atelier_supervisor(self, **kwargs):
        return request.render('atelier.supervisor_page', {
            'user_name': request.env.user.name,
        })

    # ═══════════════════════════════════════════════════════════════
    # Configuration kiosque
    # ═══════════════════════════════════════════════════════════════

    @http.route('/atelier/config', type='jsonrpc', auth='public', methods=['POST'], csrf=False)
    def atelier_config(self, **kwargs):
        ICP = request.env['ir.config_parameter'].sudo()
        auto_logout = int(ICP.get_param('atelier.auto_logout_minutes', default='10'))
        shifts = request.env['atelier.shift'].sudo().search([('active', '=', True)])
        shift_data = []
        for s in shifts:
            h_start = '%02d:%02d' % (int(s.start_hour), int(round((s.start_hour % 1) * 60)))
            h_end   = '%02d:%02d' % (int(s.end_hour),   int(round((s.end_hour   % 1) * 60)))
            shift_data.append({'id': s.id, 'name': s.name, 'start': h_start, 'end': h_end})
        return {'auto_logout_minutes': auto_logout, 'shifts': shift_data}

    # ═══════════════════════════════════════════════════════════════
    # Authentification (PIN ou badge)
    # ═══════════════════════════════════════════════════════════════

    @http.route('/atelier/auth', type='jsonrpc', auth='public', methods=['POST'], csrf=False)
    def atelier_auth(self, pin=None, badge=None, **kwargs):
        if badge:
            domain = [('atelier_badge_id', '=', badge.strip())]
        elif pin:
            domain = [('atelier_pin', '=', str(pin).strip())]
        else:
            return {'success': False, 'error': 'Aucun identifiant fourni'}

        employee = request.env['hr.employee'].sudo().search(domain, limit=1)
        if not employee:
            return {'success': False, 'error': 'PIN ou badge invalide'}

        ICP = request.env['ir.config_parameter'].sudo()
        global_logout = int(ICP.get_param('atelier.auto_logout_minutes', default='10'))
        auto_logout = employee.atelier_auto_logout_minutes or global_logout

        return {
            'success': True,
            'employee': {
                'id': employee.id,
                'name': employee.name,
                'job_title': employee.job_title or '',
                'image': '/web/image/hr.employee/%d/avatar_128' % employee.id,
                'is_supervisor': employee.atelier_is_supervisor,
                'shift': employee.atelier_shift_id.name if employee.atelier_shift_id else '',
                'auto_logout_minutes': auto_logout,
            },
        }

    # ═══════════════════════════════════════════════════════════════
    # OF Lancés assignés au technicien
    # ═══════════════════════════════════════════════════════════════

    @http.route('/atelier/orders', type='jsonrpc', auth='public', methods=['POST'], csrf=False)
    def atelier_orders(self, employee_id=None, **kwargs):
        if not employee_id:
            return {'success': False, 'error': 'employee_id manquant'}
        emp_id = int(employee_id)
        employee = request.env['hr.employee'].sudo().browse(emp_id)
        if not employee.exists():
            return {'success': False, 'error': 'Technicien introuvable'}

        productions = request.env['mrp.production'].sudo().search([
            ('is_lancer', '=', True),
            ('state', 'not in', ['done', 'cancel']),
            ('atelier_worker_ids', 'in', [emp_id]),
        ], order='atelier_priority desc, date_start asc')

        if not productions:
            return {'success': True, 'orders': []}

        # ── Collecte des IDs de tous les work orders en une fois ──
        all_wo_ids = productions.mapped('workorder_ids').filtered(
            lambda w: w.state not in ('done', 'cancel')
        ).ids

        if not all_wo_ids:
            return {'success': True, 'orders': []}

        # ── Batch fetch : blocs ouverts de CET employé ──
        my_open_blocks = request.env['mrp.workcenter.productivity'].sudo().search([
            ('workorder_id', 'in', all_wo_ids),
            ('employee_id', '=', emp_id),
            ('date_end', '=', False),
        ])
        my_open_by_wo = {b.workorder_id.id: b for b in my_open_blocks}

        # ── Batch fetch : durée accumulée (blocs fermés) de cet employé ──
        my_closed = request.env['mrp.workcenter.productivity'].sudo().search([
            ('workorder_id', 'in', all_wo_ids),
            ('employee_id', '=', emp_id),
            ('date_end', '!=', False),
        ])
        my_dur_by_wo = {}
        for b in my_closed:
            my_dur_by_wo[b.workorder_id.id] = my_dur_by_wo.get(b.workorder_id.id, 0.0) + (b.duration or 0.0)

        # ── Batch fetch : blocs ouverts des AUTRES employés ──
        others_open = request.env['mrp.workcenter.productivity'].sudo().search([
            ('workorder_id', 'in', all_wo_ids),
            ('employee_id', '!=', emp_id),
            ('date_end', '=', False),
        ])
        others_by_wo = {}
        for b in others_open:
            wid = b.workorder_id.id
            if wid not in others_by_wo:
                others_by_wo[wid] = []
            others_by_wo[wid].append(b)

        # ── Batch fetch : nombre de quality checks par work order ──
        qc_counts = {}
        if all_wo_ids:
            request.env.cr.execute(
                """
                SELECT workorder_id, COUNT(*) FROM quality_check
                WHERE workorder_id = ANY(%s)
                  AND (employee_id = %s OR employee_id IS NULL)
                GROUP BY workorder_id
                """,
                (all_wo_ids, emp_id)
            )
            for wo_id, cnt in request.env.cr.fetchall():
                qc_counts[wo_id] = cnt

        result = []
        for prod in productions:
            workorders = []
            for wo in prod.workorder_ids.filtered(lambda w: w.state not in ('done', 'cancel')):
                open_block = my_open_by_wo.get(wo.id)
                my_dur     = my_dur_by_wo.get(wo.id, 0.0)
                # Ajouter la durée du bloc en cours (ouvert) dans le total affiché
                if open_block and open_block.date_start:
                    my_dur += (datetime.utcnow() - open_block.date_start).total_seconds() / 60.0
                other_open = others_by_wo.get(wo.id, [])

                workorders.append({
                    'id': wo.id, 'name': wo.name,
                    'workcenter': wo.workcenter_id.name if wo.workcenter_id else '',
                    'state': wo.state,
                    'duration_expected': wo.duration_expected,
                    'duration': round(wo.duration or 0, 2),
                    'my_duration': round(my_dur, 2),
                    'is_running': bool(open_block),
                    'start_time': open_block.date_start.isoformat() if open_block else False,
                    'check_count': qc_counts.get(wo.id, 0),
                    'other_employees': [{
                        'id': b.employee_id.id, 'name': b.employee_id.name,
                        'image': '/web/image/hr.employee/%d/avatar_128' % b.employee_id.id,
                        'start_time': b.date_start.isoformat() if b.date_start else False,
                    } for b in other_open],
                })

            total_exp  = sum(w['duration_expected'] for w in workorders) or 0
            total_done = sum(w['duration'] for w in workorders)
            burndown   = round((total_done / total_exp * 100) if total_exp else 0.0, 1)

            result.append({
                'id': prod.id, 'name': prod.name,
                'product': prod.product_id.display_name if prod.product_id else '',
                'product_qty': prod.product_qty,
                'product_uom': prod.product_uom_id.name if prod.product_uom_id else '',
                'state': prod.state,
                'priority': prod.atelier_priority,
                'burndown': burndown,
                'date_start': prod.date_start.isoformat() if prod.date_start else None,
                'workorders': workorders,
            })
        return {'success': True, 'orders': result}

    # ═══════════════════════════════════════════════════════════════
    # Chrono : Start / Pause / Stop
    # ═══════════════════════════════════════════════════════════════

    @http.route('/atelier/workorder/start', type='jsonrpc', auth='public', methods=['POST'], csrf=False)
    def workorder_start(self, workorder_id=None, employee_id=None, **kwargs):
        if not workorder_id or not employee_id:
            return {'success': False, 'error': 'Paramètres manquants'}
        try:
            request.env['mrp.workorder'].sudo().browse(int(workorder_id)).atelier_start(int(employee_id))
            return {'success': True}
        except UserError as e:
            # Erreur métier (ex : opération concurrente) → signalée sans stack trace
            return {'success': False, 'error': str(e.args[0]), 'blocking': True}
        except PG_OperationalError:
            # Verrou DB NOWAIT déclenché : une autre transaction est en cours pour cet employé
            _logger.warning("atelier_start: DB lock contention for employee %s", employee_id)
            return {'success': False, 'error': 'Opération en cours de traitement, réessayez dans un instant.', 'blocking': False}
        except Exception as e:
            _logger.exception("atelier_start error")
            return {'success': False, 'error': str(e)}

    @http.route('/atelier/workorder/pause', type='jsonrpc', auth='public', methods=['POST'], csrf=False)
    def workorder_pause(self, workorder_id=None, employee_id=None, **kwargs):
        if not workorder_id or not employee_id:
            return {'success': False, 'error': 'Paramètres manquants'}
        try:
            request.env['mrp.workorder'].sudo().browse(int(workorder_id)).atelier_pause(int(employee_id))
            return {'success': True}
        except Exception as e:
            _logger.exception("atelier_pause error")
            return {'success': False, 'error': str(e)}

    @http.route('/atelier/workorder/stop', type='jsonrpc', auth='public', methods=['POST'], csrf=False)
    def workorder_stop(self, workorder_id=None, employee_id=None, **kwargs):
        if not workorder_id or not employee_id:
            return {'success': False, 'error': 'Paramètres manquants'}
        try:
            request.env['mrp.workorder'].sudo().browse(int(workorder_id)).atelier_stop(int(employee_id))
            return {'success': True}
        except Exception as e:
            _logger.exception("atelier_stop error")
            return {'success': False, 'error': str(e)}

    # ═══════════════════════════════════════════════════════════════
    # Pointage du jour (technicien)
    # ═══════════════════════════════════════════════════════════════

    @http.route('/atelier/timesheet', type='jsonrpc', auth='public', methods=['POST'], csrf=False)
    def atelier_timesheet(self, employee_id=None, **kwargs):
        if not employee_id:
            return {'success': False, 'error': 'employee_id manquant'}
        today = date.today()
        day_start = datetime(today.year, today.month, today.day, 0, 0, 0)
        day_end   = datetime(today.year, today.month, today.day, 23, 59, 59)

        blocks = request.env['mrp.workcenter.productivity'].sudo().search([
            ('employee_id', '=', int(employee_id)),
            ('date_start', '>=', day_start),
            ('date_start', '<=', day_end),
        ], order='date_start asc')

        rows = []
        total_minutes = 0.0
        for b in blocks:
            dur = b.duration or 0.0
            if not b.date_end:
                dur = round((datetime.utcnow() - b.date_start).total_seconds() / 60, 2)
            total_minutes += dur
            rows.append({
                'id': b.id,
                'workorder': b.workorder_id.name if b.workorder_id else '—',
                'mo_name': b.workorder_id.production_id.name if b.workorder_id else '—',
                'workcenter': b.workcenter_id.name if b.workcenter_id else '—',
                'date_start': b.date_start.isoformat() if b.date_start else None,
                'date_end':   b.date_end.isoformat()   if b.date_end   else None,
                'duration': round(dur, 2),
                'is_open': not bool(b.date_end),
            })
        return {
            'success': True, 'rows': rows,
            'total_minutes': round(total_minutes, 2),
            'date': today.strftime('%A %d %B %Y'),
        }

    # ═══════════════════════════════════════════════════════════════
    # Tableau de bord superviseur
    # ═══════════════════════════════════════════════════════════════

    @http.route('/atelier/api/supervisor/overview', type='jsonrpc', auth='user', methods=['POST'], csrf=False)
    def supervisor_overview(self, **kwargs):
        today = date.today()
        day_start = datetime(today.year, today.month, today.day, 0, 0, 0)

        active_blocks = request.env['mrp.workcenter.productivity'].sudo().search([
            ('date_end', '=', False), ('date_start', '>=', day_start),
        ])
        active_list = [{
            'id': b.id,
            'employee_id': b.employee_id.id,
            'employee_name': b.employee_id.name,
            'image': '/web/image/hr.employee/%d/avatar_128' % b.employee_id.id,
            'wo_name': b.workorder_id.name if b.workorder_id else '—',
            'mo_name': b.workorder_id.production_id.name if b.workorder_id else '—',
            'workcenter': b.workcenter_id.name if b.workcenter_id else '—',
            'date_start_ts': b.date_start.timestamp(),
        } for b in active_blocks]

        mos = request.env['mrp.production'].sudo().search([
            ('is_lancer', '=', True), ('state', 'not in', ['done', 'cancel']),
        ], order='atelier_priority desc, date_start asc')

        mo_list = []
        for mo in mos:
            total_exp  = sum(mo.workorder_ids.mapped('duration_expected')) or 0
            total_done = sum(mo.workorder_ids.mapped('duration'))
            burndown   = round((total_done / total_exp * 100) if total_exp else 0.0, 1)
            mo_list.append({
                'id': mo.id, 'name': mo.name,
                'product': mo.product_id.display_name if mo.product_id else '',
                'priority': mo.atelier_priority,
                'state': mo.state,
                'burndown': burndown,
                'total_expected': round(total_exp, 2),
                'total_done': round(total_done, 2),
                'workers': [{'name': e.name, 'image': '/web/image/hr.employee/%d/avatar_128' % e.id}
                             for e in mo.atelier_worker_ids],
            })

        today_blocks = request.env['mrp.workcenter.productivity'].sudo().search([
            ('date_start', '>=', day_start),
        ])
        emp_summary = {}
        for b in today_blocks:
            eid = b.employee_id.id
            if eid not in emp_summary:
                emp_summary[eid] = {
                    'id': eid,
                    'name': b.employee_id.name,
                    'image': '/web/image/hr.employee/%d/avatar_128' % eid,
                    'total_minutes': 0.0,
                    'is_active': False,
                    'ops_count': 0,
                    'current_mo': None,
                    'current_op': None,
                    'current_workcenter': None,
                }
            dur = b.duration or 0
            if not b.date_end:
                dur = (datetime.utcnow() - b.date_start).total_seconds() / 60
                emp_summary[eid]['is_active'] = True
                emp_summary[eid]['current_op'] = b.workorder_id.name if b.workorder_id else None
                emp_summary[eid]['current_mo'] = b.workorder_id.production_id.name if b.workorder_id else None
                emp_summary[eid]['current_workcenter'] = b.workcenter_id.name if b.workcenter_id else None
            emp_summary[eid]['total_minutes'] = round(emp_summary[eid]['total_minutes'] + dur, 2)
            emp_summary[eid]['ops_count'] += 1

        shifts = request.env['atelier.shift'].sudo().search([('active', '=', True)])
        shift_list = [{
            'id': s.id,
            'name': s.name,
            'start_hour': s.start_hour,
            'end_hour': s.end_hour,
            'auto_close_timers': s.auto_close_timers,
            'employee_names': s.employee_ids.mapped('name'),
        } for s in shifts]

        return {
            'success': True,
            'active_blocks': active_list,
            'mo_list': mo_list,
            'employee_summary': list(emp_summary.values()),
            'shifts': shift_list,
            'now': datetime.utcnow().isoformat(),
        }

    # ═══════════════════════════════════════════════════════════════
    # Autocontrôle qualité – récupérer / créer les checks du technicien
    # ═══════════════════════════════════════════════════════════════

    @http.route('/atelier/quality/checks', type='jsonrpc', auth='public', methods=['POST'], csrf=False)
    def quality_checks(self, workorder_id=None, employee_id=None, **kwargs):
        """
        Retourne les quality.check pour ce technicien sur cette opération.
        Si aucun check n'existe encore pour lui, clone les checks génériques
        (employee_id=False) et les assigne au technicien.
        """
        if not workorder_id or not employee_id:
            return {'success': False, 'error': 'Paramètres manquants'}

        wo_id  = int(workorder_id)
        emp_id = int(employee_id)
        QC     = request.env['quality.check'].sudo()
        Emp    = request.env['hr.employee'].sudo()

        employee = Emp.browse(emp_id)
        if not employee.exists():
            return {'success': False, 'error': 'Technicien introuvable'}

        # Chercher les checks déjà créés pour ce technicien
        my_checks = QC.search([
            ('workorder_id', '=', wo_id),
            ('employee_id', '=', emp_id),
        ])

        # S'il n'en a pas encore, cloner les checks génériques du workorder
        if not my_checks:
            template_checks = QC.search([
                ('workorder_id', '=', wo_id),
                ('employee_id', '=', False),
            ])
            for tmpl in template_checks:
                tmpl.copy({'employee_id': emp_id, 'quality_state': 'none'})
            my_checks = QC.search([
                ('workorder_id', '=', wo_id),
                ('employee_id', '=', emp_id),
            ])

        def _check_json(c):
            return {
                'id':            c.id,
                'title':         c.title or c.point_id.title or '—',
                'note':          c.note or '',
                'test_type':     c.test_type or 'passfail',
                'quality_state': c.quality_state,
                'measure':       c.measure if c.test_type == 'measure' else None,
                'tolerance_min': c.tolerance_min if c.test_type == 'measure' else None,
                'tolerance_max': c.tolerance_max if c.test_type == 'measure' else None,
                'norm_unit':     c.norm_unit or '',
            }

        return {'success': True, 'checks': [_check_json(c) for c in my_checks]}

    @http.route('/atelier/quality/save', type='jsonrpc', auth='public', methods=['POST'], csrf=False)
    def quality_save(self, check_id=None, quality_state=None, measure=None, employee_id=None, **kwargs):
        """Enregistre le résultat d'un quality.check par le technicien."""
        if not check_id or not quality_state:
            return {'success': False, 'error': 'Paramètres manquants'}
        check = request.env['quality.check'].sudo().browse(int(check_id))
        if not check.exists():
            return {'success': False, 'error': 'Contrôle introuvable'}
        vals = {'quality_state': quality_state}
        if measure is not None and check.test_type == 'measure':
            vals['measure'] = float(measure)
        if employee_id:
            emp = request.env['hr.employee'].sudo().browse(int(employee_id))
            if emp.exists() and emp.user_id:
                vals['user_id'] = emp.user_id.id
        check.write(vals)
        return {'success': True}

    # ═══════════════════════════════════════════════════════════════
    # Forcer clôture bloc (superviseur)
    # ═══════════════════════════════════════════════════════════════

    @http.route('/atelier/api/supervisor/force_stop', type='jsonrpc', auth='user', methods=['POST'], csrf=False)
    def supervisor_force_stop(self, block_id=None, **kwargs):
        if not block_id:
            return {'success': False, 'error': 'block_id manquant'}
        block = request.env['mrp.workcenter.productivity'].sudo().browse(int(block_id))
        if not block.exists() or block.date_end:
            return {'success': False, 'error': 'Bloc introuvable ou déjà clôturé'}
        block.write({'date_end': datetime.utcnow()})
        block._compute_duration()
        mo = block.workorder_id.production_id
        if mo:
            mo.sudo().message_post(body=(
                '⚠️ Clôture forcée par <b>%s</b> : %s – %s'
                % (request.env.user.name, block.employee_id.name, block.workorder_id.name)
            ))
        return {'success': True, 'duration': round(block.duration or 0, 2)}

    # ═══════════════════════════════════════════════════════════════
    # Clôture vacation (superviseur)
    # ═══════════════════════════════════════════════════════════════

    @http.route('/atelier/api/supervisor/close_shift', type='jsonrpc', auth='user', methods=['POST'], csrf=False)
    def supervisor_close_shift(self, shift_id=None, **kwargs):
        if not shift_id:
            return {'success': False, 'error': 'shift_id manquant'}
        shift = request.env['atelier.shift'].sudo().browse(int(shift_id))
        if not shift.exists():
            return {'success': False, 'error': 'Vacation introuvable'}
        shift.close_open_blocks()
        return {'success': True}

    # ═══════════════════════════════════════════════════════════════
    # Stats techniciens – périodique (superviseur)
    # ═══════════════════════════════════════════════════════════════

    @http.route('/atelier/api/supervisor/stats', type='jsonrpc', auth='user', methods=['POST'], csrf=False)
    def supervisor_stats(self, period='day', target_date=None, **kwargs):
        """Stats par technicien : total heures, OFs, opérations et score de productivité."""
        today = date.today()
        if target_date:
            try:
                today = datetime.strptime(target_date, '%Y-%m-%d').date()
            except Exception:
                pass

        if period == 'week':
            start_date = today - timedelta(days=today.weekday())
            end_date   = start_date + timedelta(days=6)
        elif period == 'month':
            start_date = today.replace(day=1)
            last_day   = cal_module.monthrange(today.year, today.month)[1]
            end_date   = today.replace(day=last_day)
        else:  # day
            start_date = today
            end_date   = today

        day_start = datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0)
        day_end   = datetime(end_date.year,   end_date.month,   end_date.day,   23, 59, 59)

        blocks = request.env['mrp.workcenter.productivity'].sudo().search([
            ('date_start', '>=', day_start),
            ('date_start', '<=', day_end),
            ('employee_id', '!=', False),
        ], order='employee_id, date_start')

        emp_stats = {}
        timeline  = []

        for b in blocks:
            eid = b.employee_id.id
            if eid not in emp_stats:
                emp_stats[eid] = {
                    'id':               eid,
                    'name':             b.employee_id.name,
                    'image':            '/web/image/hr.employee/%d/avatar_128' % eid,
                    'total_minutes':    0.0,
                    'expected_minutes': 0.0,
                    'blocks_count':     0,
                    'wo_ids':           set(),
                    'mo_ids':           set(),
                }

            dur = b.duration or 0.0
            if not b.date_end and b.date_start:
                dur = (datetime.utcnow() - b.date_start).total_seconds() / 60.0

            emp_stats[eid]['total_minutes'] += dur
            emp_stats[eid]['blocks_count']  += 1
            if b.workorder_id:
                emp_stats[eid]['wo_ids'].add(b.workorder_id.id)
                emp_stats[eid]['expected_minutes'] += (b.workorder_id.duration_expected or 0.0)
                if b.workorder_id.production_id:
                    emp_stats[eid]['mo_ids'].add(b.workorder_id.production_id.id)

            timeline.append({
                'employee_id':   eid,
                'employee_name': b.employee_id.name,
                'wo_name':       b.workorder_id.name if b.workorder_id else '—',
                'mo_name':       (b.workorder_id.production_id.name
                                  if b.workorder_id and b.workorder_id.production_id else '—'),
                'date_start': b.date_start.isoformat() if b.date_start else None,
                'date_end':   b.date_end.isoformat()   if b.date_end   else datetime.utcnow().isoformat(),
                'duration':   round(dur, 2),
                'is_open':    not bool(b.date_end),
            })

        result = []
        for eid, s in emp_stats.items():
            exp_min = s['expected_minutes']
            tot_min = s['total_minutes']
            score   = round(tot_min / exp_min * 100, 1) if exp_min > 0 else None
            result.append({
                'id':            eid,
                'name':          s['name'],
                'image':         s['image'],
                'total_minutes': round(tot_min, 2),
                'blocks_count':  s['blocks_count'],
                'wo_count':      len(s['wo_ids']),
                'mo_count':      len(s['mo_ids']),
                'score':         score,
            })
        result.sort(key=lambda x: x['total_minutes'], reverse=True)

        return {
            'success':    True,
            'stats':      result,
            'timeline':   timeline,
            'period':     period,
            'start_date': start_date.isoformat(),
            'end_date':   end_date.isoformat(),
        }
