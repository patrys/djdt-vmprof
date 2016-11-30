from __future__ import division, unicode_literals

from cgi import escape
from hashlib import md5
import os.path
import sys

def path_to_module_mapper():
    cache = {}
    name = None
    while True:
        path = yield name
        path = os.path.abspath(path)
        if not path in cache:
            cache[path] = None
            for name, module in sys.modules.items():
                if (module and
                        hasattr(module, '__file__') and
                        module.__file__.startswith(path)):
                    cache[path] = module.__name__
                    break
        name = cache[path]


def name_to_color_mapper():
    cache = {}
    color = None
    while True:
        name = yield color
        if not name in cache:
            main_module = name.split('.')[0]
            if main_module:
                main_hash = md5(main_module).digest()
                hue = ord(main_hash[0])
                full_hash = md5(name).digest()
                lightness = 50 + ord(full_hash[0]) // 10
                cache[name] = 'hsla(%d, 70%%, %d%%, 0.9)' % (hue, lightness)
            else:
                cache[name] = 'transparent'
        color = cache[name]


def stats_to_flame(tree):
    name_mapper = path_to_module_mapper()
    color_mapper = name_to_color_mapper()
    next(name_mapper)
    next(color_mapper)
    def visit_node(node, level, left, total):
        parts = node.name.split(':')
        if len(parts) > 1:
            func_name = parts[1]
        else:
            func_name = parts[0]
        if len(parts) > 3:
            path = parts[3]
            module_name = name_mapper.send(path) or ''
        else:
            module_name = ''
        percent = 100 * node.count / total
        color = color_mapper.send(module_name)
        left_edge = 100 * left / total
        yield (
            '<div'
            ' class="func"'
            ' style="background: %s; left: %0.2f%%; top: %dpx; width: %0.2f%%;"'
            ' title="%s (%d samples, %0.1f%%)">'
            '%s'
            ' <small>%s</small>'
            '</div>' % (
                color,
                left_edge,
                level * 20,
                percent,
                escape(node.name),
                node.count,
                percent,
                escape(func_name),
                escape(module_name)))
        offset = 0
        for child in node.children.values():
            for result in visit_node(child, level + 1, left + offset, total):
                yield result
            offset += child.count
    return visit_node(tree, 0, 0, tree.count)
