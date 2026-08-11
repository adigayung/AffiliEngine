# -*- coding: utf-8 -*-
import io

try:
    import app as app_module
    print('APP IMPORT: OK')
    print('routes / ->', app_module.app.view_functions.get('dashboard.dashboard'))
    print('routes /production_monitor/ ->', app_module.app.view_functions.get('production_monitor.index'))
except Exception as e:
    import traceback
    traceback.print_exc()
    print('APP IMPORT: FAIL', type(e).__name__, e)
