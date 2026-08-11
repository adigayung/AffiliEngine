# -*- coding: utf-8 -*-
"""Sisa patch: template fallback defensif (anchor indentasi 4 spasi)."""
import io


def read(path):
    with io.open(path, 'r', encoding='utf-8', newline='') as f:
        return f.read()


def write(path, content):
    with io.open(path, 'w', encoding='utf-8', newline='') as f:
        f.write(content)


def apply(path, old, new, label):
    raw = open(path, 'rb').read()
    nl = '\r\n' if b'\r\n' in raw else '\n'
    content = read(path)
    old = old.replace('\n', nl)
    new = new.replace('\n', nl)
    n = content.count(old)
    print(f'{label}: occurrences={n}')
    assert n == 1, f'{label} anchor not unique/found ({n})'
    content = content.replace(old, new)
    write(path, content)
    print(f'{label}: OK')


T = 'templates/production_monitor/index.html'

apply(T, '''    var chartData = {{ chart_45_hari | tojson | safe }};''',
'''    var chartData = {{ chart_45_hari | tojson | safe if chart_45_hari is defined else '{}' }};''',
'template: fallback defensif chart_45_hari')

print('TEMPLATE EDIT DONE')
