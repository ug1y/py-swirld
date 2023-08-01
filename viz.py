# -*- coding: utf-8 -*-


from random import shuffle
import sys
from base64 import b64encode
from time import localtime, strftime

from bokeh.io import curdoc
from bokeh.layouts import column, row
from bokeh.plotting import figure
from bokeh.palettes import plasma, small_palettes
from bokeh.models import (
    Slider, PreText, TextAreaInput,
    FixedTicker, Button, ColumnDataSource, PanTool, Scroll,
    RadioButtonGroup, RadioGroup, Arrow, NormalHead, HoverTool)
from pysodium import crypto_sign_keypair

from utils import bfs, randrange
from swirld import Node

R_COLORS = list(small_palettes['Greens'][9])
shuffle(R_COLORS)


def round_color(r):
    return R_COLORS[r % 9]


I_COLORS = list(plasma(256))


def idx_color(r):
    return I_COLORS[r % 256]


class App:
    def __init__(self, n_nodes):
        self.tbd = {}
        self.active = 0
        self.i = 0
        kps = [crypto_sign_keypair() for _ in range(n_nodes)]
        stake = {kp[0]: 1 for kp in kps}

        network = {}
        self.nodes = [Node(kp, network, n_nodes, stake) for kp in kps]
        for n in self.nodes:
            network[n.pk] = n.ask_sync
        self.ids = {kp[0]: i for i, kp in enumerate(kps)}

        self.main_its = [n.main() for n in self.nodes]
        for m in self.main_its:
            next(m)

        def toggle():
            if play.label == '► Play':
                play.label = '❚❚ Pause'
                self.speed.disabled = True
                self.callfunc = curdoc().add_periodic_callback(self.animate, self.speed.value * 1000)
            else:
                play.label = '► Play'
                curdoc().remove_periodic_callback(self.callfunc)
                self.speed.disabled = False

        # widget 1 - [button] for start and pause the animation.
        play = Button(label='► Play', width=90, height=40)
        play.on_click(toggle)

        def sel_node(new):
            self.active = new
            node = self.nodes[new]
            self.tbd = {}
            self.tr_src.data, self.links_src.data = self.extract_data(
                node, bfs((node.head,), lambda u: node.hg[u].p), 0)
            for u, j in tuple(self.tbd.items()):
                self.tr_src.data['line_alpha'][j] = 1 if node.famous.get(u) else 0
                if u in node.idx:
                    self.tr_src.data['round_color'][j] = idx_color(node.idx[u])
                self.tr_src.data['idx'][j] = node.idx.get(u)
                if u in node.idx and u in node.famous:
                    del self.tbd[u]
                    # print('updated')
            self.tr_src.trigger('data', None, self.tr_src.data)
            self.status.text = self.show_info()

        # widget 2 - [radio button group] for select node to switch views.
        selector = RadioButtonGroup(
            labels=['Node %i' % i for i in range(n_nodes)], active=0,
            name='Node to inspect', width=60 * (n_nodes + 1), align=['center', 'center'])
        selector.on_click(sel_node)

        # widget 3 - [slider] for adjust the speed of animation.
        self.speed = Slider(start=0, end=3, value=0.1, step=0.1, title='speed(s)',
                            width=210, height=40, format='0[.]0')

        # widget 4 - [pre text] for put key variables' value.
        self.status = PreText(text='show alg info', width=880)

        # widget 5 - [text area input] for print the working log.
        self.console = TextAreaInput(value=">>> start animation <<<\n", width=520, rows=4, title="Runtime Output:")

        # widget 6 - [figure] for present the animation.
        plot = figure(
            height=600, width=900, y_range=(0, 30), x_range=(0-1/5, n_nodes-1+1/5),
            tools=[PanTool(dimensions='height')])
        plot.xgrid.grid_line_color = None
        plot.xaxis.minor_tick_line_color = None
        plot.ygrid.grid_line_color = None
        plot.yaxis.minor_tick_line_color = None
        plot.xaxis.ticker = list(range(n_nodes))

        self.links_src = ColumnDataSource(data={'x0': [], 'y0': [], 'x1': [],
                                                'y1': [], 'width': []})
        # self.links_rend = plot.add_layout(
        #        Arrow(end=NormalHead(fill_color='black'), x_start='x0', y_start='y0', x_end='x1',
        #        y_end='y1', source=self.links_src))
        self.links_rend = plot.segment(color='#777777',
                                       x0='x0', y0='y0', x1='x1',
                                       y1='y1', source=self.links_src, line_width='width')

        self.tr_src = ColumnDataSource(
            data={'x': [], 'y': [], 'round_color': [], 'idx': [],
                  'line_alpha': [], 'round': [], 'hash': [], 'payload': [],
                  'time': []})

        self.tr_rend = plot.circle(x='x', y='y', size=20, color='round_color',
                                   line_alpha='line_alpha', source=self.tr_src, line_width=5)

        hover = HoverTool(renderers=[self.tr_rend], tooltips=[
            ('round', '@round'), ('hash', '@hash'), ('timestamp', '@time'), ('payload', '@payload'),
            ('famous', '@line_alpha'), ('witness', '@witness'), ('number', '@idx')])
        plot.add_tools(hover)

        sel_node(0)
        curdoc().add_root(column([
            row(play, selector, self.speed),
            row(self.status, self.console),
            plot]))

    def extract_data(self, node, trs, i):
        tr_data = {'x': [], 'y': [], 'round_color': [], 'idx': [],
                   'line_alpha': [], 'round': [], 'hash': [], 'payload': [],
                   'time': []}
        links_data = {'x0': [], 'y0': [], 'x1': [], 'y1': [], 'width': []}
        for j, u in enumerate(trs):
            self.tbd[u] = i + j
            ev = node.hg[u]
            x = self.ids[ev.c]
            y = node.height[u]
            tr_data['x'].append(x)
            tr_data['y'].append(y)
            tr_data['round_color'].append(round_color(node.round[u]))
            tr_data['round'].append(node.round[u])
            tr_data['hash'].append(b64encode(u).decode('utf8'))
            tr_data['payload'].append(ev.d)
            tr_data['time'].append(strftime("%Y-%m-%d %H:%M:%S", localtime(ev.t)))

            tr_data['idx'].append(None)
            tr_data['line_alpha'].append(None)

            if ev.p:
                links_data['x0'].extend((x, x))
                links_data['y0'].extend((y, y))
                links_data['x1'].append(self.ids[node.hg[ev.p[0]].c])
                links_data['x1'].append(self.ids[node.hg[ev.p[1]].c])
                links_data['y1'].append(node.height[ev.p[0]])
                links_data['y1'].append(node.height[ev.p[1]])
                links_data['width'].extend((3, 1))

        return tr_data, links_data

    def animate(self):
        r = randrange(len(self.main_its))
        log = ('working node: %i, event number: %i' % (r, self.i))
        self.console.value = log + "\n" + self.console.value
        self.i += 1
        new = next(self.main_its[r])
        if r == self.active:
            tr, links = self.extract_data(self.nodes[r], new, len(self.tr_src.data['x']))
            self.tr_src.stream(tr)
            self.links_src.stream(links)
            for u, j in tuple(self.tbd.items()):
                self.tr_src.data['line_alpha'][j] = 1 if self.nodes[r].famous.get(u) else 0
                if u in self.nodes[r].idx:
                    self.tr_src.data['round_color'][j] = idx_color(self.nodes[r].idx[u])
                self.tr_src.data['idx'][j] = self.nodes[r].idx.get(u)
                if u in self.nodes[r].idx and u in self.nodes[r].famous:
                    del self.tbd[u]
                    # print('updated')
            self.tr_src.trigger('data', None, self.tr_src.data)
            self.status.text = self.show_info()

    def show_info(self):
        node = self.nodes[self.active]
        s = "Key Parameters: \n"
        s += "[head event hash]  : " + b64encode(node.head).decode('utf8') + "\n"
        s += "[number of events] : " + str(len(node.hg)) + "\n"
        s += "[max round number] : " + str(node.round[node.head]) + "\n"
        s += "[max consensus id] : " + ('-1' if len(node.consensus) == 0 else str(max(node.consensus))) + "\n"
        return s

    def show_data(self):
        pass

App(int(sys.argv[1]))
