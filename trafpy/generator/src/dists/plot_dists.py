'''Module for plotting node and value distributions.'''

from trafpy.generator.src import tools
from trafpy.generator.src.dists import val_dists 
from trafpy.generator.src.dists import node_dists 

import numpy as np
import copy
np.set_printoptions(threshold=np.inf)
import matplotlib.pyplot as plt
import matplotlib
from matplotlib import colors
from matplotlib.ticker import ScalarFormatter
import seaborn as sns
from statsmodels.distributions.empirical_distribution import ECDF
from scipy import stats
from scipy import interpolate
import networkx as nx
from nxviz.plots import CircosPlot
import json

# import warnings # for catching warnings rather than just exceptions
# warnings.filterwarnings('error')


def get_plot_params_config(font_size):
    params = {'legend.fontsize': font_size*0.75,
              'axes.labelsize': font_size,
              'axes.titlesize': font_size,
              'xtick.labelsize': font_size*0.75,
              'ytick.labelsize': font_size*0.75}
    return params


def plot_heat_map(proportion_nodes_skewed, 
                  skewed_nodes_traffic_requested, 
                  _heat_map, 
                  roof_skew_factor, 
                  **kwargs):
    heat_map = copy.deepcopy(_heat_map)

    if 'title' not in kwargs:
        kwargs['title'] = None
    if 'font_size' not in kwargs:
        kwargs['font_size'] = 10
    if 'figsize' not in kwargs:
        kwargs['figsize'] = (4, 4)
    if 'path_to_save' not in kwargs:
        kwargs['path_to_save'] = None

    plt.rcParams.update(get_plot_params_config(font_size=kwargs['font_size']))

    # cap cals at roof val for plotting
    for row_idx in range(len(heat_map[:, 0])):
        for col_idx in range(len(heat_map[0, :])):
            heat_map[row_idx, col_idx] = min(heat_map[row_idx, col_idx], roof_skew_factor)

    fig = plt.figure(figsize=kwargs['figsize'])
    cmap = matplotlib.cm.get_cmap('coolwarm')
    # plt.pcolormesh(proportion_nodes_skewed*100, skewed_nodes_traffic_requested*100, heat_map, cmap=cmap, vmin=0, vmax=1)
    # plt.pcolormesh(proportion_nodes_skewed*100, skewed_nodes_traffic_requested*100, heat_map, cmap=cmap)
    plt.pcolormesh(proportion_nodes_skewed*100, skewed_nodes_traffic_requested*100, heat_map, cmap=cmap, vmin=1, vmax=roof_skew_factor)
    plt.xlabel('% of Overall Traffic Requested')
    plt.ylabel('% Skewed Nodes')
    if kwargs['title'] is not None:
        plt.title(kwargs['title'])
    cbar=plt.colorbar()
    cbar.ax.set_ylabel('Skew Factor')
    if kwargs['path_to_save'] is not None:
        plt.savefig(kwargs['path_to_save'])
    if kwargs['show_fig']:
        plt.show()

    return fig

def get_val_idx_in_matrix(matrix, val, axis=None, axis_vals=None):  
    '''Find indices of values in 2D numpy matrix.

    Args:
        matrix (2D numpy array): Matrix in which to find values and return indices of.
        val (int, float): Value to find indices of in matrix.
        axis (None, str): If None, will return [row_idx, col_idx] of element in matrix
            which is closest to val being searched for. If 'x' or 'y', will return col_idx
            of x- or y-value being searched for respectively.
        axis_vals (None, list): Must specify axis values is axis is not None. 
            Are the x- or y-axis label values of the matrix to search in and return the idx of
            the element in axis_vals closest to val.
    '''
    val_to_diff = {} # store how close each element in matrix or axis_vals is to val being searched for
    for x_idx in range(len(matrix[0, :])): # columns
        for y_idx in range(len(matrix[:, 0])): # rows
            if axis is None:
                val_to_diff[matrix[y_idx, x_idx]] = abs(val - matrix[y_idx, x_idx])
            else:
                if axis_vals is None:
                    raise Exception('Must provide axis vals if want to find val idx of matrix for specific axis.')
                if axis == 'x':
                    val_to_diff[x_idx] = abs(val - axis_vals[x_idx])
                elif axis == 'y':
                    val_to_diff[y_idx] = abs(val - axis_vals[y_idx])
                else:
                    raise Exception('axis must be one of \'x\' or \'y\'.')

    return min(val_to_diff, key=val_to_diff.get)

def plot_labeled_heat_map(proportion_nodes_skewed, skewed_nodes_traffic_requested, _heat_map, resolution, **kwargs):
    heat_map = copy.deepcopy(_heat_map)
    if heat_map.shape != (101, 102):
        raise Exception('Heat map must have shape (101, 102) for labeled heat map plotting, but has shape {}.'.format(heat_map.shape))

    if 'title' not in kwargs:
        kwargs['title'] = None
    if 'font_size' not in kwargs:
        kwargs['font_size'] = 10
    if 'path_to_save' not in kwargs:
        kwargs['path_to_save'] = None
    kwargs['figsize'] = (8, 8)

    plt.rcParams.update(get_plot_params_config(font_size=kwargs['font_size']))

    fig, ax = plt.subplots(figsize=kwargs['figsize'])
    nodes_skewed_to_plot = np.arange(proportion_nodes_skewed[0], proportion_nodes_skewed[-1], resolution)
    traffic_requested_to_plot = np.arange(skewed_nodes_traffic_requested[0], skewed_nodes_traffic_requested[-1], resolution)
    _heat_map = np.zeros((len(heat_map[:, 0]), len(heat_map[0, :])))
    ax.matshow(_heat_map, cmap=plt.cm.Blues)
    for nodes_skewed in nodes_skewed_to_plot:
        for traffic_requested in traffic_requested_to_plot:
            row_idx = get_val_idx_in_matrix(heat_map, axis='y', val=nodes_skewed, axis_vals=proportion_nodes_skewed)
            col_idx = get_val_idx_in_matrix(heat_map, axis='x', val=traffic_requested, axis_vals=skewed_nodes_traffic_requested)
            # print('original heatmap val: {}'.format(heat_map[col_idx, row_idx]))
            if heat_map[col_idx, row_idx] > 1e9:
                # tending to infinity
                heat_map[col_idx, row_idx] = float('inf')
                ax.text(row_idx, col_idx, str(heat_map[col_idx, row_idx]), va='center', ha='center')
            elif heat_map[col_idx, row_idx] < 10 and round(heat_map[col_idx, row_idx], 1) % 1 != 0:
                # save space on grid by only letting vals <10 and != int being a float
                heat_map[col_idx, row_idx] = round(heat_map[col_idx, row_idx], 1)
                ax.text(row_idx, col_idx, str(heat_map[col_idx, row_idx]), va='center', ha='center')
            else:
                # val is an int and/or > 10 -> make int to save space on grid
                heat_map[col_idx, row_idx] = int(heat_map[col_idx, row_idx])
                ax.text(row_idx, col_idx, str(int(heat_map[col_idx, row_idx])), va='center', ha='center')

    ax.set_xlim(traffic_requested_to_plot[0]*100, traffic_requested_to_plot[-1]*100)
    ax.set_ylim(nodes_skewed_to_plot[0]*100, nodes_skewed_to_plot[-1]*100)
    major_tick_res = int(len(traffic_requested_to_plot)/10)
    ax.set_xticks(traffic_requested_to_plot[::major_tick_res]*100, minor=False)
    ax.set_yticks(nodes_skewed_to_plot[::major_tick_res]*100, minor=False)
    ax.set_xticks(traffic_requested_to_plot*100, minor=True)
    ax.set_yticks(nodes_skewed_to_plot*100, minor=True)
    ax.grid(which='major', axis='both', linestyle='-', color='gray', alpha=0.3)
    ax.grid(which='minor', axis='both', linestyle='--', color='gray', alpha=0.3)
    ax.set_xlabel('% of Overall Traffic Requested')
    ax.set_ylabel('% Skewed Nodes')
    ax.set_axisbelow(True)
    if kwargs['title'] is not None:
        ax.set_title(kwargs['title'])
    if kwargs['show_fig']:
        plt.show()
    if kwargs['path_to_save'] is not None:
        plt.savefig(kwargs['path_to_save'])

    return fig


def plot_node_dist(node_dist, 
                   eps=None,
                   node_to_index_dict=None,
                   add_labels=False, 
                   add_ticks=False,
                   cbar_label='%',
                   conv_to_percentage=True,
                   plot_chord=True,
                   chord_edge_width_range=[1, 25],
                   chord_edge_display_threshold=0.3,
                   font_size=10,
                   figsize=(4,4),
                   show_fig=False):
    '''Plots network node demand distribution as (1) 2d matrix and (2) chord diagram.

    Args:
        node_dist (list or 2d numpy array): Source-destination pair probabilities 
            of being chosen. Must be either a 2d numpy matrix of probabilities or 
            a 1d list/array of node pair probabilities.
        eps (list): List of node endpoint labels.
        node_to_index_dict (dict): Maps node labels (keys) to integer indices (values).
        add_labels (bool): Whether or not to node labels to plot.
        add_ticks (bool): Whether or not to add ticks to x- and y-axis.
        cbar_label (str): Label for colour bar.
        chord_edge_width_range (list): Range [min, max] of edge widths for chord diagram.
        chord_edge_display_threshold (float): Float between 0 and 1 of fraction/probability
            of end point pair above which to draw an edge on the chord diagram. E.g. if 
            0.3, will draw all edges which have a load pair higher than 0.3*max_pair_load.
            Higher threshold -> fewer edges plotted -> can increase clarity.
        show_fig (bool): Whether or not to plot and show fig. If True, will
            return and display fig.

    Returns:
        matplotlib.figure.Figure: node distribution plotted as a 2d matrix. 

    '''
    plt.rcParams.update(get_plot_params_config(font_size=font_size))

    # print(node_dist)
    if type(node_dist[0]) == str and eps is None:
        eps = list(set(node_dist))
    # else:
        # assert eps is not None, 'must provide list of end points as arg if node_dist contains no endpoint labels.'
    else:
        eps = [str(i) for i in range(np.array(node_dist).shape[0])]

    if conv_to_percentage:
        # conv node dist to percentage
        for row in node_dist:
            for el in row:
                el *= 100

    if node_to_index_dict is None:
        _,_,node_to_index_dict,_=tools.get_network_params(eps) 

    figs = []

    # 1. PLOT NODE DIST
    matfig = plt.figure(figsize=figsize)
    fig = plt.matshow(node_dist, cmap='YlOrBr', fignum=matfig.number)
    plt.style.use('default')
    cbar = plt.colorbar()
    if add_labels == True:
        for (i, j), z in np.ndenumerate(node_dist):
            plt.text(j, 
                     i, 
                     '{}'.format(z), 
                     ha='center', 
                     va='center',
                     bbox = dict(boxstyle='round', 
                     facecolor='white', 
                     edgecolor='0.3'))
    plt.xlabel('Dst')
    plt.ylabel('Src')
    cbar.ax.set_ylabel(cbar_label, rotation=270, x=0.5, fontsize=font_size*0.75)
    if add_ticks:
        plt.xticks([node_to_index_dict[node] for node in eps])
        plt.yticks([node_to_index_dict[node] for node in eps])
    figs.append(fig)

    if show_fig:
        plt.show()


    # 2. PLOT CHORD DIAGRAM
    if plot_chord:
        probs = node_dists.assign_matrix_to_probs(eps, node_dist)
        graph = nx.Graph()
        node_to_load = {}
        _, _, node_to_index, index_to_node = tools.get_network_params(eps)
        max_pair_load = max(list(probs.values()))
        for pair in probs.keys():
            pair_load = probs[pair]
            p = json.loads(pair)
            src, dst = str(p[0]), str(p[1])
            if src not in node_to_load:
                node_to_load[src] = pair_load
            else:
                node_to_load[src] += pair_load
            if dst not in node_to_load:
                node_to_load[dst] = pair_load
            else:
                node_to_load[dst] += pair_load
            if pair_load > chord_edge_display_threshold*max_pair_load:
                graph.add_weighted_edges_from([(src, dst, pair_load)])
            else:
                graph.add_nodes_from([src, dst])

        nodelist = [n for n in graph.nodes]
        try:
            ws = _rescale([float(graph[u][v]['weight']) for u, v in graph.edges], newmin=chord_edge_width_range[0], newmax=chord_edge_width_range[1])
            plot_chord = True
        except ZeroDivisionError:
            print('Src-dst edge weights in chord diagram are all the same, leading to 0 rescaled values. Decrease chord_edge_display_threshold to ensure a range of edge values are included in the chord diagram.')
            plot_chord = False

        if plot_chord:
            # only plot chord if have at least 2 different node loads
            all_same = True
            for load in node_to_load.values():
                if load != node_to_load[nodelist[0]]:
                    all_same = False
            if all_same:
                plot_chord = False
                print('Node loads all same, will not plot chord diagram.')

        if plot_chord:
            edgelist = [(str(u),str(v),{"weight":ws.pop(0)}) for u,v in graph.edges]

            graph2 = nx.Graph()
            graph2.add_nodes_from(nodelist)
            graph2.add_edges_from(edgelist)

            for v in graph2:
                graph2.nodes[v]['load'] = node_to_load[v]

            plt.set_cmap('YlOrBr')
            plt.style.use('default')
            chord_diagram = CircosPlot(graph2, 
                                       node_labels=True,
                                       edge_width='weight',
                                       figsize=figsize,
                                       # edge_color='weight',
                                       # node_size='load',
                                       node_grouping='load',
                                       node_color='load')
            chord_diagram.draw()
            figs.append(chord_diagram)
        else:
            # do not plot chord
            pass
    
    if show_fig:
        plt.show()




    return figs


def _rescale(l, newmin, newmax):
    '''Rescales list l values to range between newmin and newmax.'''
    arr = list(l)
    return [round((x-min(arr))/(max(arr)-min(arr))*(newmax-newmin)+newmin,2) for x in arr]

def plot_dict_scatter(_dict,
                      logscale=False,
                      rand_var_name='Random Variable',
                      ylabel='Probability',
                      xlim=None,
                      marker_size=30,
                      font_size=10,
                      plot_style='default',
                      gridlines=True,
                      figsize=(6.4, 4.8),
                      aspect='auto',
                      show_fig=False):
    '''
    Plots scatter of dict with keys (x-axis random variables) values (corresponding
    y-axis values) pairs.

    This is useful for plotting discrete probability distributions i.e. _dict keys are
    random variable values, _dict values are their respective probabilities of
    occurring.
    '''

    fig = plt.figure(figsize=figsize)
    plt.style.use(plot_style)
    plt.rcParams.update(get_plot_params_config(font_size=font_size))
    if logscale:
        ax = plt.gca()
        ax.set_xscale('log')

    plt.scatter(list(_dict.keys()), list(_dict.values()), s=marker_size)
    plt.xlabel(rand_var_name)
    plt.ylabel(ylabel)

    if gridlines:
        plt.grid(which='both', axis='both', color='gray', linestyle='dashed', alpha=0.3)
    if aspect != 'auto':
        plt.gca().set_aspect(aspect=_get_matplotlib_aspect_ratio(fig, aspect_ratio=aspect))

    if xlim is not None:
        plt.xlim(xlim)

    if show_fig:
        plt.show()

    return fig





def plot_val_dist(rand_vars, 
                  dist_fit_line=None, 
                  xlim=None, 
                  logscale=False,
                  transparent=True,
                  rand_var_name='Random Variable', 
                  prob_rand_var_less_than=None,
                  num_bins=0,
                  plot_cdf=True,
                  plot_horizontally=True,
                  fig_scale=1,
                  font_size=20,
                  gridlines=True,
                  figsize=(12.4, 2),
                  aspect='auto',
                  plot_style='default',
                  use_scientific_notation_yaxis=False,
                  print_characteristics=True,
                  show_fig=False):
    '''Plots (1) probability distribution and (2) cumulative distribution function.
    
    Args:
        rand_vars (list): Random variable values.
        dist_fit_line (str): Line to fit to named distribution. E.g. 'exponential'.
            If not plotting a named distribution, leave as None.
        xlim (list): X-axis limits of plot. E.g. xlim=[0,10] to plot random
            variable values between 0 and 10.
        logscale (bool): Whether or not plot should have logscale x-axis and bins.
        transparent (bool): Whether or not to make plot bins slightly transparent.
        rand_var_name (str): Name of random variable to label plot's x-axis.
        num_bins (int): Number of bins to use in plot. Default is 0, in which
            case the number of bins chosen will be automatically selected.
        plot_cdf (bool): Whether or not to plot the CDF as well as the probability
            distribution.
        plot_horizontally (bool): Wheter to plot PDF and CDF horizontally (True)
            or vertically (False).
        fig_scale (int/float): Scale by which to multiply figure size.
        font_size (int): Size of axes ticks and titles.
        print_characteristics (bool): Whether to print characteristics of rand_vars
            distribution.
        show_fig (bool): Whether or not to plot and show fig. If True, will
            return and display fig.
    
    Returns:
        matplotlib.figure.Figure: node distribution plotted as a 2d matrix. 

    '''
    plt.rcParams.update(get_plot_params_config(font_size=font_size))

    if print_characteristics:
        description = stats.describe(rand_vars)
        print('Characteristics of {} distribution: {}'.format(rand_var_name, description))

    if num_bins==0:
        histo, bins = np.histogram(rand_vars,density=True,bins='auto')
    else:
        histo, bins = np.histogram(rand_vars,density=True,bins=num_bins)
    if transparent:
        alpha=0.50
    else:
        alpha=1.0
    # HISTOGRAM
    if plot_horizontally:
        # fig = plt.figure(figsize=(15*fig_scale,5*fig_scale))
        fig = plt.figure(figsize=figsize)
        plt.subplot(1,2,1)
        plt.xlabel(rand_var_name)
    else:
        # fig = plt.figure(figsize=(10*fig_scale,15*fig_scale))
        fig = plt.figure(figsize=figsize)
        ax1 = plt.subplot(2,1,1)
        plt.setp(ax1.get_xticklabels(), visible=False)
    plt.style.use(plot_style)
    if logscale:
        ax = plt.gca()
        ax.set_xscale('log')
        if bins[0] == 0:
            bins[0] = 1
        logbins = np.logspace(np.log10(bins[0]),np.log10(bins[-1]),len(bins))
        plotbins = logbins
    else:
        plotbins = bins
    
    plt.hist(rand_vars,
             bins=plotbins,
             align='mid',
             color='tab:red',
             edgecolor='tab:red',
             alpha=alpha)
    if use_scientific_notation_yaxis:
        plt.ticklabel_format(axis="y", style="sci", scilimits=(0,0))
    else:
        plt.ticklabel_format(axis="y", style="plain")

    if gridlines:
        plt.grid(which='both', axis='both', color='gray', linestyle='dashed', alpha=0.3)
    if aspect != 'auto':
        plt.gca().set_aspect(aspect=_get_matplotlib_aspect_ratio(fig, aspect_ratio=aspect))
    
    # can't have 0 vals for fitting
    for i, val in enumerate(rand_vars):
        if val == 0:
            rand_vars[i] = 1e-12
    if dist_fit_line is None:
        pass
    elif dist_fit_line == 'exponential':
        loc, scale = stats.expon.fit(rand_vars, floc=0)
        y = stats.expon.pdf(plotbins, loc, scale)
    elif dist_fit_line == 'lognormal':
        shape, loc, scale = stats.lognorm.fit(rand_vars, floc=0)
        y = stats.lognorm.pdf(plotbins, shape, loc, scale)
    elif dist_fit_line == 'weibull':
        shape, loc, scale = stats.weibull_min.fit(rand_vars, floc=0)
        y = stats.weibull_min.pdf(plotbins, shape, loc, scale)
    elif dist_fit_line == 'pareto':
        shape, loc, scale = stats.pareto.fit(rand_vars, floc=0)
        y = stats.pareto.pdf(plotbins, shape, loc, scale)

    plt.ylabel('Counts')
    try:
        plt.xlim(xlim)
    except NameError:
        pass
    
    if plot_cdf:
        plt.rcParams.update(get_plot_params_config(font_size=font_size))
        # CDF
        # empirical hist
        if plot_horizontally:
            plt.subplot(1,2,2)
        else:
            plt.subplot(2,1,2)
        if logscale:
            ax = plt.gca()
            ax.set_xscale('log')
        else:
            pass
        n,bins_temp,patches = plt.hist(rand_vars, 
                                       bins=plotbins, 
                                       cumulative=True,
                                       density=True,
                                       histtype='step',
                                       color='tab:red',
                                       edgecolor='tab:red')
        patches[0].set_xy(patches[0].get_xy()[:-1])
        # theoretical line
        ecdf = ECDF(rand_vars)
        plt.plot(ecdf.x, ecdf.y, alpha=0.5, color='tab:blue')
        plt.xlabel(rand_var_name)
        plt.ylabel('CDF')
        try:
            plt.xlim(xlim)
        except NameError:
            pass
        plt.ylim(top=1)

        if gridlines:
            plt.grid(which='both', axis='both', color='gray', linestyle='dashed', alpha=0.3)
        if aspect != 'auto':
            plt.gca().set_aspect(aspect=_get_matplotlib_aspect_ratio(fig, aspect_ratio=aspect))
    
    # PRINT ANY EXTRA ANALYSIS OF DISTRIBUTION
    if prob_rand_var_less_than is None:
        pass
    else:
        for prob in prob_rand_var_less_than:
            print('P(x<{}): {}'.format(prob, ecdf(prob)))
    
    if show_fig:
        plt.show()

    return fig


def plot_val_bar(x_values,
                 y_values,
                 ylabel='Random Variable',
                 ylim=None,
                 xlabel=None,
                 plot_all_x_ticks=True,
                 bar_width=0.8,
                 gridlines=True,
                 aspect='auto',
                 figsize=(6.4, 4.8),
                 font_size=10,
                 alpha=0.5,
                 plot_style='default',
                 show_fig=False):
    '''Plots standard bar chart.'''

    x_pos = [x for x in range(len(x_values))]

    fig = plt.figure(figsize=figsize)
    plt.style.use(plot_style)
    plt.rcParams.update(get_plot_params_config(font_size=font_size))

    plt.bar(x_pos, 
            y_values, 
            bar_width, 
            alpha=alpha,
            color='tab:red',
            edgecolor='tab:red')

    plt.ylabel(ylabel)
    if plot_all_x_ticks:
        plt.xticks(x_pos, (x_val for x_val in x_values))
    if xlabel is not None:
        plt.xlabel(xlabel)

    try:
        plt.ylim(ylim)
    except NameError:
        pass

    # fig.autofmt_xdate()

    if gridlines:
        plt.grid(which='both', axis='both', color='gray', linestyle='dashed', alpha=0.3)
    if aspect != 'auto':
        plt.gca().set_aspect(aspect=_get_matplotlib_aspect_ratio(fig, aspect_ratio=aspect))

    if show_fig:
        plt.show()

    return fig



def plot_radar(plot_dict,
               title=None,
               n_ordinate_levels=5,
               fill=True,
               figsize=(6.4, 4.8),
               font_size=10,
               linewidth=1,
               fill_alpha=0.1,
               line_alpha=1,
               linestyle='-',
               plot_legend=True,
               legend_ncol=1,
               plot_style='default',
               show_fig=True):
    '''Plots radar plot.

    Required structure of plot dict (keys in <> can be user-defined, otherwise 
    must use exact key):

    plot_dict = {'<rand_var_name1>': {'range': [0, 1], 'classes': {'<class1>': 0.2, '<class2>': 0.7}},
                 '<rand_var_name2>': {'range': [10, 100], 'classes': {'<class1>': 20, '<class2>': 90}}}

    e.g.2:

    plot_dict = {'rand_var1': {'range': [0, 1], 'classes': {'class1': 0.2,
                                                         'class2': 0.4}},
                 'rand_var2': {'range': [0, 100], 'classes': {'class1': 60,
                                                               'class2': 20}},
                 'rand_var3': {'range': [1, 5], 'classes': {'class1': 2,
                                                             'class2': 5}},
                 'rand_var4': {'range': [0, 10], 'classes': {'class1': 7,
                                                              'class2': 3}},
                 'rand_var5': {'range': [10, 0], 'classes': {'class1': 1,
                                                              'class2': 8}}
                }

    To flip axes values (i.e. have lower values going to edge of radar), enter
    reversed range array (e.g. 'range': [100, 10] instead of 'range': [10, 100])

    Args:
        n_ordinate_levels (int): Number of gridlines to plot for the radar plot.

    '''

    fig = plt.figure(figsize=figsize)
    plt.style.use(plot_style)
    plt.rcParams.update(get_plot_params_config(font_size=font_size))

    rand_var_names = list(plot_dict.keys())

    classes = []
    for rand_var in rand_var_names:
        for _class in plot_dict[rand_var]['classes'].keys():
            classes.append(_class)
    classes = np.sort(np.unique(classes))
    class_colours = iter(sns.color_palette(palette='hls', n_colors=len(classes), desat=None))

    ranges = [plot_dict[rand_var_name]['range'] for rand_var_name in rand_var_names]

    angles = np.arange(0, 360, 360./len(rand_var_names))
    axes = [fig.add_axes([0.1, 0.1, 0.9, 0.9], polar=True, label='axes{}'.format(rand_var_name)) for rand_var_name in range(len(rand_var_names))]
    l, text = axes[0].set_thetagrids(angles, labels=rand_var_names, fontsize=font_size)
    for txt, angle in zip(text, angles):
        txt.set_rotation(angle-90)

    for ax in axes[1:]:
        ax.patch.set_visible(False)
        ax.grid('off')
        ax.xaxis.set_visible(False)

    # plot radar gridlines
    for i, ax in enumerate(axes):
        grid = np.linspace(*ranges[i], num=n_ordinate_levels)
        gridlabel = ['{}'.format(round(x,2)) for x in grid]
        gridlabel[0] = '' # clean up origin
        ax.set_rgrids(grid, labels=gridlabel, angle=angles[i])
        ax.set_ylim(*ranges[i])
        ax.yaxis.grid(linestyle='--', color='gray', alpha=0.075, linewidth=1)

        # label_position = ax.get_rlabel_position()
        # print('label_position: {}'.format(label_position))
        # if i == 0:
            # ax.set_rlabel_position(-22.5)


        # remove outer edge
        ax.spines["polar"].set_visible(False)

        # make gridlines polygon
        gridlines = ax.yaxis.get_gridlines()
        for gl in gridlines:
            gl.get_path()._interpolation_steps = len(rand_var_names)


    angle = np.deg2rad(np.r_[angles, angles[0]])
    ax = axes[0]

    for _class in classes:
        colour = next(class_colours)
        data = [plot_dict[rand_var]['classes'][_class] for rand_var in rand_var_names]
        sdata = _scale_data(data, ranges)
        ax.plot(angle, 
                np.r_[sdata, sdata[0]], 
                color=colour,
                label=str(_class),
                alpha=line_alpha,
                linestyle=linestyle,
                linewidth=linewidth)
        if fill:
            ax.fill(angle, 
                    np.r_[sdata, sdata[0]], 
                    color=colour,
                    alpha=fill_alpha,
                    linestyle=linestyle,
                    linewidth=linewidth)

    if plot_legend:
        ax.legend(ncol=legend_ncol)
    if title is not None:
        ax.set_title(title, va='bottom')

    if show_fig:
        plt.show()

    return fig


def _invert(x, limits):
    """inverts a value x on a scale from
    limits[0] to limits[1]"""
    return limits[1] - (x - limits[0])

def _scale_data(data, ranges):
    """scales data[1:] to ranges[0],
    inverts if the scale is reversed"""
    for d, (y1, y2) in zip(data[1:], ranges[1:]):
        assert (y1 <= d <= y2) or (y2 <= d <= y1)
    x1, x2 = ranges[0]
    d = data[0]
    # if x1 > x2:
        # d = _invert(d, (x1, x2))
        # x1, x2 = x2, x1
    sdata = [d]
    for d, (y1, y2) in zip(data[1:], ranges[1:]):
        if y1 > y2:
            d = _invert(d, (y1, y2))
            y1, y2 = y2, y1
        sdata.append((d-y1) / (y2-y1) 
                     * (x2 - x1) + x1)
    return sdata


def plot_val_line(plot_dict={},
                 xlabel='Random Variable',
                 ylabel='Random Variable Value',
                 ylim=None,
                 linewidth=1,
                 alpha=1,
                 ylogscale=False,
                 title=None,
                 vertical_lines=[],
                 gridlines=True,
                 aspect='auto',
                 plot_style='default',
                 font_size=10,
                 figsize=(6.4, 4.8),
                 plot_legend=True,
                 legend_ncol=1,
                 show_fig=False):
    '''Plots line plot.

    plot_dict= {'class_1': {'x_values': [0.1, 0.2, 0.3], 'y_values': [20, 40, 80]},
                'class_2': {'x_values': [0.1, 0.2, 0.3], 'y_values': [80, 60, 20]}}

    '''

    keys = list(plot_dict.keys())

    fig = plt.figure(figsize=figsize)
    plt.style.use(plot_style)
    plt.rcParams.update(get_plot_params_config(font_size=font_size))

    class_colours = iter(sns.color_palette(palette='hls', n_colors=len(keys), desat=None))
    for _class in sorted(plot_dict.keys()):
        plt.plot(plot_dict[_class]['x_values'], plot_dict[_class]['y_values'], color=next(class_colours), linewidth=linewidth, alpha=alpha, label=str(_class))
        for vline in vertical_lines:
            plt.axvline(x=vline, color='r', linestyle='--')

    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    ax = plt.gca()
    if ylogscale:
        ax.set_yscale('log')
    if ylim is not None:
        plt.ylim(bottom=ylim[0], top=ylim[1])
    if plot_legend:
        plt.legend(ncol=legend_ncol)

    if gridlines:
        plt.grid(which='both', axis='both', color='gray', linestyle='dashed', alpha=0.3)
    if aspect != 'auto':
        plt.gca().set_aspect(aspect=_get_matplotlib_aspect_ratio(fig, aspect_ratio=aspect))
    if title is not None:
        plt.title(title)

    if show_fig:
        plt.show()
    
    return fig



def plot_val_scatter(plot_dict={},
                     xlabel='Random Variable',
                     ylabel='Random Variable Value',
                     ghost_classes=[],
                     title=None,
                     alpha=1,
                     marker_size=40,
                     marker_style='.',
                     plot_line=False,
                     horizontal_lines=[],
                     linewidth=1,
                     logscale=False,
                     ylogscale=False,
                     gridlines=True,
                     xlim=None,
                     ylim=None,
                     error_bar_axis=None,
                     apply_smoothing=False,
                     use_scientific_notation_yaxis=False,
                     use_scientific_notation_xaxis=False,
                     font_size=10,
                     figsize=(6.4, 4.8),
                     aspect='auto',
                     plot_style='default',
                     legend_ncol=1,
                     plot_legend=True,
                     show_fig=False):
    '''Plots scatter plot.

    plot_dict = {'class_1': {'x_values': [0.1, 0.2, 0.3], 'y_values': [20, 40, 80]},
                 'class_2': {'x_values': [0.1, 0.2, 0.3], 'y_values': [80, 60, 20]}}

    OPTIONAL: Can also include error bars: 
    plot_dict = {'class_1': {'x_values': [0.1, 0.2, 0.3], 'y_values': [20, 40, 80], 'errors': [0.001, 0.001, 0.003]}}
    error_bar_axis = 'yerr' (set to 'xerr' or 'yerr' to have error bars on x or y axis respectively)

    if alpha is a list, will assign each class an alpha value correponding to list

    N.B. ghost classes is useful for where are doing a particular plot where plotting
    e.g. 2 of the usual 4 classes that you'd plot, but want to keep the class
    names having the same colours in the plot. E.g. If usually plot classes A, B, C
    and D, but now plotting A and C but want to keep same class colours, should
    enter ghost_classes=[B, D].

    '''

    keys = list(plot_dict.keys())
    # num_vals = len(plot_dict[keys[0]]['x_values'])
    # for key in keys:
        # if len(plot_dict[key]['x_values']) != num_vals or len(plot_dict[key]['y_values']) != num_vals:
            # raise Exception('Must have equal number of x and y values to plot.')

    if type(alpha) == list:
        multiple_alphas = True
        alphas = iter(alpha)
    else:
        multiple_alphas = False

    fig = plt.figure(figsize=figsize)
    plt.style.use(plot_style)
    plt.rcParams.update(get_plot_params_config(font_size=font_size))

    colour_keys = copy.deepcopy(keys)
    for ghost in ghost_classes:
        colour_keys.append(ghost)
    class_colours = iter(sns.color_palette(palette='hls', n_colors=len(colour_keys), desat=None))

    printed_warning = False
    for _class in sorted(colour_keys):
        colour = next(class_colours)
        # sort in order of x-values
        if _class in keys:
            sorted_indices = np.argsort(plot_dict[_class]['x_values'])
            if multiple_alphas:
                alpha = next(alphas)
            # OLD
            # plt.scatter(np.asarray(plot_dict[_class]['x_values'])[sorted_indices], np.asarray(plot_dict[_class]['y_values'])[sorted_indices], color=colour, s=marker_size, alpha=alpha, marker=marker_style, label=str(_class))
            # if plot_line:
                # plt.plot(np.asarray(plot_dict[_class]['x_values'])[sorted_indices], np.asarray(plot_dict[_class]['y_values'])[sorted_indices], linewidth=linewidth, color=colour, alpha=1)

            if error_bar_axis is None and 'errors' in plot_dict[_class] and not printed_warning:
                print('WARNING: If provide \'errors\' in plot_dict, must specify error_bar_axis arg as either \'yerr\' or \'xerr\' if you still want your error bars to be plotted.')
                printed_warning = True
            if error_bar_axis is not None and 'errors' not in plot_dict[_class]:
                raise Exception('Must provide \'errors\' in plot_dict if error_bar_axis is not None.')

            # NEW
            x_vals = np.asarray(plot_dict[_class]['x_values'])[sorted_indices]
            y_vals = np.asarray(plot_dict[_class]['y_values'])[sorted_indices]
            if error_bar_axis is not None:
                errors = np.asarray(plot_dict[_class]['errors'])[sorted_indices]
            if apply_smoothing:
                x_new = np.linspace(min(x_vals), max(x_vals), 300)
                a_BSpline = interpolate.make_interp_spline(x_vals, y_vals)
                x_vals = x_new
                y_vals = a_BSpline(x_vals)
                plt.plot(x_vals, y_vals, color=colour, linewidth=linewidth, alpha=alpha, label=str(_class))
                plt.scatter(np.asarray(plot_dict[_class]['x_values'])[sorted_indices], np.asarray(plot_dict[_class]['y_values'])[sorted_indices], color=colour, s=marker_size, alpha=alpha, marker=marker_style)
            else:
                if error_bar_axis is not None:
                    # plot scatter with error bars
                    scatter_size_factor = 0.15 # need to re-size to keep consistent with plt.scatter()
                    if error_bar_axis == 'yerr':
                        plt.errorbar(x_vals, y_vals, yerr=errors, fmt=marker_style, color=colour, ms=marker_size*scatter_size_factor, alpha=alpha, label=str(_class))
                    else:
                        plt.errorbar(x_vals, y_vals, xerr=errors, fmt=marker_style, color=colour, ms=marker_size*scatter_size_factor, alpha=alpha, label=str(_class))
                else:
                    # no error bars, normal scatter
                    plt.scatter(x_vals, y_vals, color=colour, s=marker_size, alpha=alpha, marker=marker_style, label=str(_class))
                if plot_line:
                    plt.plot(np.asarray(plot_dict[_class]['x_values'])[sorted_indices], np.asarray(plot_dict[_class]['y_values'])[sorted_indices], linewidth=linewidth, color=colour, alpha=1)

    for hline in horizontal_lines:
        plt.axhline(y=hline, color='tab:red', linestyle='--')


    if use_scientific_notation_yaxis:
        plt.ticklabel_format(axis="y", style="sci", scilimits=(0,0))
    else:
        plt.ticklabel_format(axis="y", style="plain", useOffset=False)
    if use_scientific_notation_xaxis:
        plt.ticklabel_format(axis="x", style="sci", scilimits=(0,0))
    else:
        plt.ticklabel_format(axis="x", style="plain", useOffset=False)


    ax = plt.gca()
    if logscale:
        ax.set_xscale('log')
    if ylogscale:
        ax.set_yscale('log')


    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    if plot_legend:
        plt.legend(ncol=legend_ncol)
    if title is not None:
        ax.set_title(title)

    if gridlines:
        plt.grid(which='both', axis='both', color='gray', linestyle='dashed', alpha=0.3)
    if aspect != 'auto':
        plt.gca().set_aspect(aspect=_get_matplotlib_aspect_ratio(fig, aspect_ratio=aspect))

    if xlim is not None:
        plt.xlim(xlim)
    if ylim is not None:
        plt.ylim(ylim)

    plt.tick_params(axis='x', which='minor')

    if show_fig:
        plt.show()
    

    return fig

def plot_multiple_kdes(plot_dict={},
                       plot_hist=False,
                       xlabel='Random Variable',
                       ylabel='Density',
                       logscale=False,
                       plot_style='default',
                       gridlines=True,
                       aspect='auto',
                       font_size=10,
                       figsize=(6.4, 4.8),
                       legend_ncol=1,
                       show_fig=False):

    fig = plt.figure(figsize=figsize)
    plt.style.use(plot_style)
    plt.rcParams.update(get_plot_params_config(font_size=font_size))
    if logscale:
        ax = plt.gca()
        ax.set_xscale('log')

    keys = list(plot_dict.keys())
    class_colours = iter(sns.color_palette(palette='hls', n_colors=len(keys), desat=None))
    for _class in sorted(plot_dict.keys()):
        color = next(class_colours)
        sns.distplot(plot_dict[_class]['rand_vars'], hist=plot_hist, kde=True, norm_hist=True, label=str(_class))

    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.legend(ncol=legend_ncol)

    if gridlines:
        plt.grid(which='both', axis='both', color='gray', linestyle='dashed', alpha=0.3)
    if aspect != 'auto':
        plt.gca().set_aspect(aspect=_get_matplotlib_aspect_ratio(fig, aspect_ratio=aspect))

    if show_fig:
        plt.show()

    return fig


def plot_val_cdf(plot_dict={},
                 xlabel='Random Variable',
                 ylabel='CDF',
                 title=None,
                 ghost_classes=[],
                 logscale=False,
                 plot_points=True,
                 complementary_cdf=False,
                 use_scientific_notation=False,
                 marker_size=40,
                 marker_style='.',
                 linewidth=1,
                 gridlines=True,
                 plot_style='default',
                 font_size=10,
                 figsize=(6.4, 4.8),
                 aspect='auto',
                 legend_ncol=1,
                 show_fig=False):
    '''Plots CDF plot.

    plot_dict= {'class_1': {'rand_vars': [0.1, 0.1, 0.3],
                'class_2': {'rand_vars': [0.2, 0.2, 0.3]}}

    OPTIONAL: Can also include error bars: 
    plot_dict = {'class_1': {'rand_vars': [0.1, 0.2, 0.3], 'errors': [0.001, 0.001, 0.003]}}

    N.B. ghost classes is useful for where are doing a particular plot where plotting
    e.g. 2 of the usual 4 classes that you'd plot, but want to keep the class
    names having the same colours in the plot. E.g. If usually plot classes A, B, C
    and D, but now plotting A and C but want to keep same class colours, should
    enter ghost_classes=[B, D].

    '''

    fig = plt.figure(figsize=figsize)
    plt.style.use(plot_style)
    plt.rcParams.update(get_plot_params_config(font_size=font_size))

    if logscale:
        ax = plt.gca()
        ax.set_xscale('log')

    keys = list(plot_dict.keys())
    colour_keys = copy.deepcopy(keys)
    for ghost in ghost_classes:
        colour_keys.append(ghost)
    class_colours = iter(sns.color_palette(palette='hls', n_colors=len(colour_keys), desat=None))
    for _class in sorted(colour_keys):
        colour = next(class_colours)
        if _class in keys:
            ecdf = ECDF(plot_dict[_class]['rand_vars'])
            if complementary_cdf:
                plt.plot(ecdf.x, 1-ecdf.y, linewidth=linewidth, color=colour, label=str(_class))
                if plot_points: 
                    if 'errors' in plot_dict[_class]:
                        scatter_size_factor = 0.15 # need to re-size to keep consistent with plt.scatter()
                        plot_dict[_class]['errors'].insert(0,0) # need to insert to be compatible with ecdf
                        plt.errorbar(list(ecdf.x), list(1-ecdf.y), xerr=plot_dict[_class]['errors'], fmt=marker_style, ms=marker_size*scatter_size_factor, color=colour)
                    else:
                        plt.scatter(ecdf.x, 1-ecdf.y, marker=marker_style, s=marker_size, color=colour)
            else:
                plt.plot(ecdf.x, ecdf.y, color=colour, linewidth=linewidth, label=str(_class))
                if plot_points:
                    if 'errors' in plot_dict[_class]:
                        plot_dict[_class]['errors'].insert(0,0) # need to insert to be compatible with ecdf
                        scatter_size_factor = 0.15 # need to re-size to keep consistent with plt.scatter()
                        plt.errorbar(ecdf.x, ecdf.y, xerr=plot_dict[_class]['errors'].insert(0,0), fmt=marker_style, ms=marker_size*scatter_size_factor, color=colour)
                    else:
                        plt.scatter(ecdf.x, ecdf.y, marker=marker_style, s=marker_size, color=colour)
    if not logscale:
        if use_scientific_notation:
            plt.ticklabel_format(axis="x", style="sci", scilimits=(0,0))
        else:
            plt.ticklabel_format(axis="x", style="plain")
    plt.ylim(top=1, bottom=0)

    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.legend(ncol=legend_ncol)
    if title is not None:
        ax = plt.gca()
        ax.set_title(title)

    if gridlines:
        plt.grid(which='both', axis='both', color='gray', linestyle='dashed', alpha=0.3)
    if aspect != 'auto':
        plt.gca().set_aspect(aspect=_get_matplotlib_aspect_ratio(fig, aspect_ratio=aspect))

    if show_fig:
        plt.show()

    return fig



def _get_matplotlib_aspect_ratio(fig, aspect_ratio=1):
    fig = fig
    ax = plt.gca()
    x_left, x_right = ax.get_xlim()
    y_low, y_high = ax.get_ylim()
    return abs((x_right-x_left)/(y_low-y_high))*aspect_ratio





def plot_val_stacked_bar(plot_dict={},
                         ylabel='Random Variable',
                         ylim=None,
                         bar_width=0.35,
                         plot_style='default',
                         gridlines=True,
                         aspect='auto',
                         font_size=10,
                         figsize=(6.4, 4.8),
                         legend_ncol=1,
                         show_fig=False):
    '''Plots stacked bar chart.

    E.g. plot_dict given should be of the form:

    plot_dict= {'class_1': {'x_values': ['Uni DCN', 'Private DCN', 'Cloud DCN'], 'y_values': [20, 40, 80]},
    'class_2': {'x_values': ['Uni DCN', 'Private DCN', 'Cloud DCN'], 'y_values': [80, 60, 20]}}

    ylim=[0,100]

    '''


    keys = list(plot_dict.keys())
    num_vals = len(plot_dict[keys[0]]['x_values'])
    for key in keys:
        if len(plot_dict[key]['x_values']) != num_vals or len(plot_dict[key]['y_values']) != num_vals:
            raise Exception('Must have equal number of x and y values to plot if want to stack bars.')
    x_pos = [x for x in range(num_vals)]


    fig = plt.figure(figsize=figsize)
    plt.style.use(plot_style)
    plt.rcParams.update(get_plot_params_config(font_size=font_size))

    plots = {}
    curr_bottom = None # init bottom y coords of bar to plot
    for _class in sorted(plot_dict.keys()):
        plots[_class] = plt.bar(x_pos, plot_dict[_class]['y_values'], bar_width, bottom=curr_bottom)
        # update bottom y coords for next bar
        curr_bottom = plot_dict[_class]['y_values']

    plt.ylabel(ylabel)
    plt.xticks(x_pos, (x_val for x_val in plot_dict[_class]['x_values']))
    plt.legend((plots[key][0] for key in list(plots.keys())), (_class for _class in (plot_dict.keys())), ncol=legend_ncol)

    if gridlines:
        plt.grid(which='both', axis='both', color='gray', linestyle='dashed', alpha=0.3)
    if aspect != 'auto':
        plt.gca().set_aspect(aspect=_get_matplotlib_aspect_ratio(fig, aspect_ratio=aspect))

    try:
        plt.ylim(ylim)
    except NameError:
        pass

    if show_fig:
        plt.show()

    return fig



def plot_demand_slot_colour_grid(grid_demands, 
                                 title=None, 
                                 xlim=None, 
                                 font_size=10,
                                 show_fig=False):
    plt.rcParams.update(get_plot_params_config(font_size=font_size))

    # set colours
    # class_colours = sns.color_palette(palette='hls', n_colors=None, desat=None)
    # cmap = colors.ListedColormap(class_colours
    cmap = None

    # plot grid
    fig, ax = plt.subplots()
    c = ax.pcolor(grid_demands, cmap=cmap)
    plt.xlabel('Time Slot')
    plt.ylabel('Flow Slot')

    if title is not None:
        ax.set_title(title)

    if xlim is not None:
        plt.xlim(xlim)

    if show_fig:
        plt.show()

    return fig















