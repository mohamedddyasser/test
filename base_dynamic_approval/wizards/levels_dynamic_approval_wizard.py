from odoo import models, fields, _, api
from odoo.exceptions import ValidationError, AccessError, UserError


class DynamicApprovalWizard(models.TransientModel):
    _name = 'levels.dynamic.approval.wizard'
    _description = 'Define Levels Advanced Approval Wizard'

    name = fields.Char(
        default='There is no approval levels found, Are you sure to define new levels?',
    )

    dynamic_approval_id = fields.Many2one(
        comodel_name='dynamic.approval',
        string='Dynamic Approval')

    dynamic_approval_level_id = fields.One2many(
        comodel_name='dynamic.approval.level.wizard',
        inverse_name='define_levels_id',
        string='Levels',
        required=False)

    model = fields.Char(
        string='Model',
        required=False)

    record = fields.Integer(
        string='Record',
        required=False)

    def action_set_approvers(self, manager=None):
        record = self.env[self._context.get('active_model')].browse(self._context.get('active_id'))
        matched_approval = self.dynamic_approval_id

        approval_request_values = self._prepare_approval_request_values_wiz(self._context.get('active_model'), record)
        if approval_request_values:
            pass
        else:
            raise AccessError("Dynamic Approval Levels must have one Approver User at least.")
        self.env['dynamic.approval.request'].create(approval_request_values)

        record.apply_dynamic_approval(matched_approval)

        # if matched_approval and record:
        #     if record.dynamic_approve_request_ids:
        #         record.write({
        #             record._state_field: record._state_under_approval,
        #             'approve_requester_id': self.env.user.id,
        #             'dynamic_approval_id': matched_approval.id,
        #             'state_from_name': getattr(record, record._state_field),
        #         })
        # next_waiting_approval = record.dynamic_approve_request_ids.sorted(lambda x: (x.sequence, x.id))[0]
        # next_waiting_approval.status = 'pending'
        # if next_waiting_approval.get_approve_user():
        #     user = next_waiting_approval.get_approve_user()[0]
        #     record._notify_next_approval_request(matched_approval, user)

    def _prepare_approval_request_values_wiz(self, model, res):
        """ return values for approval request """
        self.ensure_one()
        return [level.prepare_approval_request_values_wiz(model=model, res=res) for level in
                self.dynamic_approval_level_id]

    @api.model
    def default_get(self, fields):
        res = super(DynamicApprovalWizard, self).default_get(fields)
        find_model = self.env['ir.model'].sudo().search([('model', '=', self._context.get('active_model'))]).id
        rec = self.env['dynamic.approval'].sudo().search([('model_id', '=', find_model)])
        active_rec = self.env[self._context.get('active_model')].sudo().browse(int(self._context.get('active_id')))
        levels = rec.approval_level_ids
        if not rec.self_approval:
            levels = levels.filtered(lambda l: l.user_id != active_rec.create_uid)

        approval_val_list = []

        line_manager = None
        if rec.line_manager_approval:
            employee_field = rec.employee_field
            employee = getattr(active_rec, employee_field, None)
            if not employee or not employee.user_id:
                raise UserError('invalid employee or invalid manager')
            # print('employee_field')
            # print(employee_field)
            # print(employee)
            line_manager = employee.parent_id.user_id
        # line_manager = self.env['hr.employee'].search([('user_id', '=', active_rec.create_uid.id)]).parent_id.user_id
            if rec.line_manager_approval and not employee.user_id.has_group('hr_exit_process.group_department_manager_for_exit'):
                if line_manager:
                    approval_val_list.append(
                        (0, 0, {
                            'sequence': 1,
                            'user_id': line_manager,
                            'group_id': None,
                        }))
        for value in levels:
            if line_manager and value.user_id == line_manager:
                continue
            approval_val_list.append(
                (0, 0, {
                    'sequence': value.sequence+1,
                    'user_id': value.user_id,
                    'group_id': value.group_id,
                }))

        res.update({'dynamic_approval_level_id': approval_val_list,
                    'dynamic_approval_id': rec.id,
                    })
        return res


class DynamicApprovalLevelWizard(models.TransientModel):
    _name = 'dynamic.approval.level.wizard'

    define_levels_id = fields.Many2one(
        comodel_name='levels.dynamic.approval.wizard',
        string=' Define Levels',
        required=False)
    sequence = fields.Integer(
        default=1,
    )
    user_id = fields.Many2one(
        comodel_name='res.users',
        string='Approver User',
    )
    group_id = fields.Many2one(
        comodel_name='res.groups',
        string='Approver Group',
    )

    @api.onchange('sequence')
    def onchange_method(self):
        if self.define_levels_id and not self.define_levels_id.dynamic_approval_id.self_approval:
            active_rec = self.env[self._context.get('active_model')].sudo().browse(int(self._context.get('active_id')))
            return {'domain': {'user_id': [('id', '!=', active_rec.create_uid.id)]}}

    def prepare_approval_request_values_wiz(self, model, res):
        """ return values for create approval request """
        self.ensure_one()
        group = self.group_id
        user = self._get_approval_user(model, res)
        if group or user:
            return {
                'res_model': model,
                'res_id': res.id,
                'sequence': self.sequence,
                'user_id': user.id if user else False,
                'group_id': self.group_id.id if self.group_id else False,
                'status': 'new',
                'approve_date': False,
                'approved_by': False,
            }

    def _get_approval_user(self, model, res):
        """ allow to override to select user in other modules """
        self.ensure_one()
        return self.user_id
