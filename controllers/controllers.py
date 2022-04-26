# -*- coding: utf-8 -*-
# from odoo import http


# class EntrebamientoFreig(http.Controller):
#     @http.route('/entrebamiento_freig/entrebamiento_freig/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/entrebamiento_freig/entrebamiento_freig/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('entrebamiento_freig.listing', {
#             'root': '/entrebamiento_freig/entrebamiento_freig',
#             'objects': http.request.env['entrebamiento_freig.entrebamiento_freig'].search([]),
#         })

#     @http.route('/entrebamiento_freig/entrebamiento_freig/objects/<model("entrebamiento_freig.entrebamiento_freig"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('entrebamiento_freig.object', {
#             'object': obj
#         })
