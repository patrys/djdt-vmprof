import os.path
import sys
import tempfile

import vmprof
from debug_toolbar.panels import Panel
from django.template import Context, Template

from . import flamegraph


TEMPLATE = r"""
<style>
    svg {
        width: 100%;
        height: auto;
    }
</style>
{{ flamegraph|safe }}
<script>
    init();
</script>
"""


def tree_to_flame(parent, node, lines):
    if ':' in node.name:
        block_type, funcname, *rest = node.name.split(':')
        if len(rest) >= 2:
            lineno = rest[0]
            filename = rest[1]
            suffix = ''
            rel_name = os.path.relpath(filename)
            for prefix in sorted(sys.path, key=lambda p: len(p), reverse=True):
                if os.path.relpath(prefix) == '.':
                    continue
                if filename.startswith(prefix):
                    rel_name = os.path.relpath(filename, prefix)
                    suffix = '_[i]'
                    break
            if not rel_name.startswith('..'):
                filename = rel_name
            else:
                suffix = '_[k]'
            funcname = '%s [%s:%s]%s' % (funcname, filename, lineno, suffix)
        if parent:
            current = '%s;%s' % (parent, funcname)
        else:
            current = funcname
    else:
        current = node.name
    count = node.count
    if count > 10:
        print(node.name, node.count)
    for c in node.children.values():
        count -= c.count
        tree_to_flame(current, c, lines)
    lines.append('%s %s' % (current, count))


class VMProfPanel(Panel):
    title = 'VMProf'

    def process_request(self, request):
        self.output = tempfile.NamedTemporaryFile()
        vmprof.enable(self.output.fileno())

    def process_response(self, request, response):
        vmprof.disable()

    def generate_stats(self, request, response):
        stats = vmprof.read_profile(self.output.name)
        tree = stats.get_tree()
        lines = []
        tree_to_flame(None, tree, lines)
        self.record_stats({'lines': '\n'.join(lines)})

    @property
    def content(self):
        stats = self.get_stats()
        ctx = {'flamegraph': flamegraph.stats_to_svg(stats['lines'])}
        return Template(TEMPLATE).render(Context(ctx))
