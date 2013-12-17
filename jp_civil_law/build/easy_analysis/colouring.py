# encoding: utf-8

import colors
import colors.primary
import colors.rainbow


def set_graphcolor(agraph, rankcolor=False, rankmap=None, fullrange=False):
    if rankcolor and rankmap is not None:
        colormap = pwrvariation_with_ranks(agraph, rankmap, fullrange=fullrange)
        blueback = True
    else:
        colormap = default_colormap(agraph)
        blueback = False
    color_graph(agraph, colormap, blueback=blueback)

def default_colormap(agraph):
    return dict.fromkeys(agraph.nodes(), 'edf1f2')

def set_mixed_graphcolor(agraph, rankmap_1, rankmap_2, fullrange=False):
    diffmap = {}
    for node in rankmap_1:
        rank_1, rank_2 = rankmap_1[node], rankmap_2[node]
        diffmap[node] = rank_1 - rank_2
    colormap = pwrvariation_with_ranks(agraph, diffmap, fullrange=fullrange)

    color_graph(agraph, colormap, blueback=True)

def pwrvariation_with_ranks(agraph, rankmap, pivot=0.6, fullrange=False):
    colormap = {}
    if fullrange:
        minval = min(rankmap.values())
        maxval = max(rankmap.values())
    else:
        minval = 0.0
        maxval = 1.0
    if minval * maxval > 0.0:
        semi_range = True
        valrange = maxval - minval
    else:
        semi_range = False
        valrange = max(maxval, abs(minval))
    if valrange == 0.0:
        return dict.fromkeys(agraph.nodes(), str(colors.hsv(0.6, 0.8, pivot).hex))
    for node in agraph.nodes():
        if semi_range:
            colordepth = (rankmap[node] - minval) / valrange
        else:
            colordepth = rankmap[node] / valrange
        rankval = pivot + 0.4 * colordepth
        colormap[node] = str(colors.hsv(0.6, 0.8, rankval).hex)
    return colormap

def color_graph(agraph, colormap, blueback=False):
    for node in agraph.nodes():
        node_obj = agraph.get_node(node)
        color = colormap[node]
        inverted = str(colors.hex(color).invert().hex)
        node_obj.attr['style'] = 'filled'
        node_obj.attr['fillcolor'] = '#' + color
        node_obj.attr['fontcolor'] = '#' + inverted
    if blueback:
        agraph.graph_attr['bgcolor'] = '#' + str(colors.hsv(0.6, 0.8, 0.6).hex)
        for node in agraph.nodes():
            nodeobj = agraph.get_node(node)
            nodeobj.attr['penwidth'] = '0'

def color_nodeborders(agraph, target_nodes,
                      preset_with_fill=None, color=colors.primary.red):
    if preset_with_fill == 'a':
        color = colors.rainbow.green + colors.hsv(0.0, 0.0, 0.3)
    elif preset_with_fill == 'b':
        color = colors.rainbow.orange + colors.hsv(0.0, 0.0, 0.3)
    elif preset_with_fill == 'ab':
        color = colors.rainbow.violet + colors.hsv(0.0, 0.0, 0.3)
    agraph.graph_attr['color'] = '#' + str(color.hex)
    for node in agraph.nodes():
        if node in target_nodes:
            node_obj = agraph.get_node(node)
            node_obj.attr['color'] = '#' + str(color.hex)
            node_obj.attr['penwidth'] = '1'
