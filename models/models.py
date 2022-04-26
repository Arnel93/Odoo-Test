# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class RegimenImportacion(models.Model):
    _name = 'regimen.importacion'
    _description = 'Regimen de Importaciones'

    name = fields.Char(string='Name', required=True)
    date_regimen = fields.Date(string="Date")
    type = fields.Char(string='Tipo')
    campo = fields.Boolean(string='Campo', default=True)


class TipoAforo(models.Model):
    _name = 'tipo.aforo'
    _description = 'Tipos de Aforo'

    name = fields.Char(string='Name', required=True)
    campo = fields.Boolean(string='Campo', default=True)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    importacion = fields.Boolean(string='Importación', default=True)


class ProductPartner(models.Model):
    _inherit = 'res.partner'

    importacion = fields.Boolean(string='Importación', default=True)


class FreightLote(models.Model):
    _inherit = 'freight.operation'

    regimen_importacion = fields.Many2one(comodel_name="regimen.importacion", string="Regimen de Importacion")
    tipo_aforo = fields.Many2one(comodel_name="tipo.aforo", string="Tipo de Aforo")

    freig_rel = fields.Boolean(string='Coste', default=False)#Para el dominio en el coste en destino

    def action_open_costes(self):

        if self.stage_id.name != 'Cancelado':

            return {
                'name': _("Costes en Destino"),
                'type': "ir.actions.act_window",
                'view_mode': 'form',
                'res_model': 'stock.landed.cost',
                'target': 'current',
                'context': {'default_lote_coste': self.id, 'default_coste_rel': True}

            }
        else:
            raise ValidationError("El lote está cancelado")

    pedidos = fields.One2many('purchase.order', 'lote_importacion', string='Pedidos',
                              compute='_compute_pedidos')

    def _compute_pedidos(self):

        self.pedidos = self.env['purchase.order'].search(
            [('lote_importacion.id', '=', self.id), ('state', 'not in', ['draft', 'sent', 'cancel'])])


    transferencia = fields.One2many('stock.picking', 'stock_lote', string='Pedidos', compute='_compute_transfer')

    def _compute_transfer(self):

        self.transferencia = self.env['stock.picking'].search([('stock_lote.id', '=', self.id), ('state', '=', 'done')])


    factura = fields.One2many('account.move', 'account_lote', string='Facturas')


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    accont_idd = fields.One2many('stock.landed.cost.lines','aco_id' ,'Costoo')


class StockLandedCostLine(models.Model):
    _inherit = 'stock.landed.cost.lines'

    cost_id = fields.Many2one(
        'stock.landed.cost', 'Landed Cost',
         ondelete='cascade')

    aco_id = fields.Many2one(
        "account.move.line", 'Tira contra la s facturas')

    cost_id2 = fields.Many2one(
        'stock.landed.cost', 'Landed Cost para el computo',
        ondelete='cascade')

    price_unit = fields.Monetary('Cost')


class CostesDestino(models.Model):
    _inherit = 'stock.landed.cost'

    lote_coste = fields.Many2one(comodel_name="freight.operation", string="Lote Imp")

    coste_rel = fields.Boolean(string='Coste', default=False)


    cost_lines = fields.One2many(
        'stock.landed.cost.lines', 'cost_id', 'Cost Lines',
        copy=True, states={'done': [('readonly', True)]},index=True,compute='_compute_products2')



    lote_rel = fields.Boolean(string='Coste',default=False)

    lote_rell = fields.Boolean(string='Coste2', default=False)

    lote_id = fields.Integer(string='Coste3', related='picking_ids.stock_lote.id')


    @api.depends('lote_coste')
    def _compute_products2(self):
        A = []
        if len(self.lote_coste)!=0:

            c = self.env['stock.landed.cost'].search([])
            if len(c)==0:
                raise ValidationError(_("Debe haber al menos un lote "))
            else:
                    mid = int(c[0].name[-4:])

                    for j in self.lote_coste.factura:
                        for k in j.invoice_line_ids:
                            if len(k.product_id) != 0  and k.product_id.type == 'service' and k.product_id.landed_cost_ok == True:
                                con=False
                                id=0
                                for l in k.accont_idd:
                                    if l.cost_id2.name==self.name:
                                        con=True
                                        id=l.id
                                        break

                                if con:
                                    A.append(id)
                                else:

                                    vals = {
                                        "product_id": k.product_id.id,
                                        "cost_id": mid,
                                        "price_unit": 0.00,
                                        "split_method": 'equal'

                                    }

                                    if self.name != _('New'):
                                        vals["cost_id2"]=int(self.name[-4:])
                                        vals["cost_id"] = int(self.name[-4:])


                                    c=self.env['stock.landed.cost.lines'].create(vals)

                                    k.update(
                                        {
                                            'accont_idd':[4,c.id]
                                        }
                                    )

                                    A.append((c.id))

                    self.update(
                        {
                            "cost_lines":[(6,0,A)]
                        }
                    )
        else:
            self.cost_lines=self.env['stock.landed.cost.lines']

    @api.onchange('lote_coste')
    def onchange_lote_coste(self):

        if self.lote_coste:
            self.vendor_bill_id = self.env['account.move']
            self.picking_ids = self.env['stock.picking'].search([('stock_lote.id','=',self.lote_coste.id)])


        if len(self.lote_coste)==0:
                self.lote_rel = False
        else:
            self.lote_rel = True

    @api.onchange('picking_ids')
    def onchange_picking_ids(self):
        if len(self.picking_ids) == 0:
            self.lote_rell = False
        else:
            self.lote_rell = True


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    lote_importacion = fields.Many2one(comodel_name="freight.operation", string="Lote Imp")

    importacion_rel = fields.Boolean(string='Importación', related='partner_id.importacion', default=False)

    def _prepare_picking(self):
        values = super(PurchaseOrder, self)._prepare_picking()

        if self.importacion_rel:
            values.update({'stock_lote': self.lote_importacion.id})

        return values

    def _prepare_invoice(self):

        values = super(PurchaseOrder, self)._prepare_invoice()

        values.update({'account_rel2': True})

        if self.importacion_rel:
            values.update({'account_lote': self.lote_importacion.id})

        return values

    def button_confirm(self):
        if self.importacion_rel and len(self.lote_importacion) == 0:
            raise ValidationError(_("You must select a Lote"))
        else:
            return super(PurchaseOrder, self).button_confirm()


class StockPicking(models.Model):
    _inherit = "stock.picking"

    stock_lote = fields.Many2one(comodel_name="freight.operation", string="Lote Imp")

    stock_rel = fields.Boolean(string='Transfer', related='partner_id.importacion', default=False)

    lote_rel2 = fields.Boolean(string='Coste', default=False)


class FacturaAccount(models.Model):
    _inherit = 'account.move'

    account_lote = fields.Many2one(comodel_name="freight.operation", string="Lote Imp")

    account_rel = fields.Boolean(string='Factura', related='partner_id.importacion', default=False)

    account_rel2 = fields.Boolean(string='Factura', default=False)
