# -*- coding: utf-8 -*-

from odoo import fields, models, api, _


class SaleOrderDocumentChecklist(models.Model):
    _name = "sale.order.document.checklist"
    _description = "Sale Order Document Checklist"

    name = fields.Char()
    sale_order_id = fields.Many2one(comodel_name="sale.order")
    attachment_ids = fields.Many2many(comodel_name='ir.attachment', string="Attach File", )

    @api.model_create_multi
    def create(self, vals_list):
        res = super(SaleOrderDocumentChecklist, self).create(vals_list)
        for vals in vals_list:
            if vals.get('attachment_ids', False):
                update_attachment_ids = []
                for attachment in vals.get('attachment_ids'):
                    update_attachment_ids.append(attachment[1])
                if update_attachment_ids and self.env['ir.attachment'].browse(update_attachment_ids).exists():
                    self.env['ir.attachment'].browse(update_attachment_ids).write({
                        'res_id': res.sale_order_id.id,
                        'res_name': res.sale_order_id.name,
                        'res_model': res.sale_order_id._name
                    })
        return res

    def write(self, values):
        res = super(SaleOrderDocumentChecklist, self).write(values)

        if 'attachment_ids' in values:
            unlink_attachment_ids = []
            update_attachment_ids = []

            for command in values['attachment_ids']:
                command_type = command[0]
                attachment_id = command[1] if len(command) > 1 else None

                if command_type == 3 and attachment_id:
                    unlink_attachment_ids.append(attachment_id)
                elif command_type == 4 and attachment_id:
                    update_attachment_ids.append(attachment_id)

            # Unlink attachments if any
            if unlink_attachment_ids and self.env['ir.attachment'].browse(unlink_attachment_ids).exists():
                self.env['ir.attachment'].browse(unlink_attachment_ids).unlink()

            # Update attachments if any
            if update_attachment_ids and self.env['ir.attachment'].browse(update_attachment_ids).exists():
                attachments = self.env['ir.attachment'].browse(update_attachment_ids)
                attachments.write({
                    'res_id': self.sale_order_id.id,
                    'res_name': self.sale_order_id.name,
                    'res_model': self.sale_order_id._name,
                })

        return res

    def unlink(self):
        # Get all attachment_ids in one go and unlink them in bulk
        attachments_to_unlink = self.mapped('attachment_ids')
        if attachments_to_unlink:
            attachments_to_unlink.unlink()

        # Call the super method to unlink the SaleOrderDocumentChecklist records
        return super(SaleOrderDocumentChecklist, self).unlink()
