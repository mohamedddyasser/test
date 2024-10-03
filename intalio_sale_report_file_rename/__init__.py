from . import models


def uninstall_hook(env):
    env.ref('sale.action_report_saleorder').write({
        'print_report_name': "(object.state in ('draft', 'sent') and 'Quotation - %s' % (object.name)) or 'Order - %s' % (object.name)"
    })
