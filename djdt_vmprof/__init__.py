import os.path
import tempfile
import threading

import vmprof
from debug_toolbar.panels import Panel
from django.template import Context, Template

from . import flamegraph


terrible_performance = threading.Lock()

TEMPLATE = r"""
<style>
    #djDebug .vmprof-flamegraph {
        position: relative;
    }
    #djDebug .vmprof-flamegraph .func {
        border: 1px solid rgba(255, 255, 255, 0.75);
        border-radius: 3px;
        box-sizing: border-box;
        height: 20px;
        line-height: 20px;
        overflow: hidden;
        padding: 0 2px;
        position: absolute;
        text-overflow: ellipsis;
        white-space: nowrap;
    }
    #djDebug .vmprof-flamegraph .func:hover {
        border: 1px solid rgba(0, 0, 0, 0.75);
    }
    #djDebug .vmprof-flamegraph .func small {
        color: rgba(0, 0, 0, 0.5);
    }
</style>
<div class="vmprof-flamegraph">
    {{ data|safe }}
</div>
"""


class VMProfPanel(Panel):
    title = 'VMProf'

    def process_request(self, request):
        self.output = tempfile.NamedTemporaryFile()
        terrible_performance.acquire()
        vmprof.enable(self.output.fileno())

    def process_response(self, request, response):
        vmprof.disable()
        terrible_performance.release()
        stats = vmprof.read_profile(self.output.name)
        tree = stats.get_tree()
        self.record_stats({'tree': tree})
        os.unlink(self.output.name)

    @property
    def content(self):
        stats = self.get_stats()
        tree = stats['tree']
        data = ''.join(flamegraph.stats_to_flame(tree))
        ctx = {'data': data}
        return Template(TEMPLATE).render(Context(ctx))
