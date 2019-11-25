""" Utilities function to manage graph files
"""


def loadCT(filename):
 
    import networkx as nx
    from os.path import basename
    g = nx.Graph()
    with open(filename) as f:
        content = f.read().splitlines()
        g = nx.Graph(
            name=str(content[0]),
            filename=basename(filename))  # set name of the graph
        tmp = content[1].split(" ")
        if tmp[0] == '':
            nb_nodes = int(tmp[1])  # number of the nodes
            nb_edges = int(tmp[2])  # number of the edges
        else:
            nb_nodes = int(tmp[0])
            nb_edges = int(tmp[1])
            # patch for compatibility : label will be removed later
        for i in range(0, nb_nodes):
            tmp = content[i + 2].split(" ")
            tmp = [x for x in tmp if x != '']
            g.add_node(i, atom=tmp[3], label=tmp[3])
        for i in range(0, nb_edges):
            tmp = content[i + g.number_of_nodes() + 2].split(" ")
            tmp = [x for x in tmp if x != '']
            g.add_edge(
                int(tmp[0]) - 1,
                int(tmp[1]) - 1,
                bond_type=tmp[3].strip(),
                label=tmp[3].strip())
    return g


def loadGXL(filename):
    from os.path import basename
    import networkx as nx
    import xml.etree.ElementTree as ET

    tree = ET.parse(filename)
    root = tree.getroot()
    index = 0
    g = nx.Graph(filename=basename(filename), name=root[0].attrib['id'])
    dic = {}  # used to retrieve incident nodes of edges
    for node in root.iter('node'):
        dic[node.attrib['id']] = index
        labels = {}
        for attr in node.iter('attr'):
            labels[attr.attrib['name']] = attr[0].text
        g.add_node(index, **labels)
        index += 1

    for edge in root.iter('edge'):
        labels = {}
        for attr in edge.iter('attr'):
            labels[attr.attrib['name']] = attr[0].text
        g.add_edge(dic[edge.attrib['from']], dic[edge.attrib['to']], **labels)
    return g


def saveGXL(graph, filename):
    import xml.etree.ElementTree as ET
    root_node = ET.Element('gxl')
    attr = dict()
    attr['id'] = graph.graph['name']
    attr['edgeids'] = 'true'
    attr['edgemode'] = 'undirected'
    graph_node = ET.SubElement(root_node, 'graph', attrib=attr)

    for v in graph:
        current_node = ET.SubElement(graph_node, 'node', attrib={'id': str(v)})
        for attr in graph.nodes[v].keys():
            cur_attr = ET.SubElement(
                current_node, 'attr', attrib={'name': attr})
            cur_value = ET.SubElement(cur_attr,
                                      graph.nodes[v][attr].__class__.__name__)
            cur_value.text = graph.nodes[v][attr]

    for v1 in graph:
        for v2 in graph[v1]:
            if (v1 < v2):  # Non oriented graphs
                cur_edge = ET.SubElement(
                    graph_node,
                    'edge',
                    attrib={
                        'from': str(v1),
                        'to': str(v2)
                    })
                for attr in graph[v1][v2].keys():
                    cur_attr = ET.SubElement(
                        cur_edge, 'attr', attrib={'name': attr})
                    cur_value = ET.SubElement(
                        cur_attr, graph[v1][v2][attr].__class__.__name__)
                    cur_value.text = str(graph[v1][v2][attr])

    tree = ET.ElementTree(root_node)
    tree.write(filename)


def loadSDF(filename):
    """load data from structured data file (.sdf file).

    Notes
    ------
    A SDF file contains a group of molecules, represented in the similar way as in MOL format.
    Check http://www.nonlinear.com/progenesis/sdf-studio/v0.9/faq/sdf-file-format-guidance.aspx, 2018 for detailed structure.
    """
    import networkx as nx
    from os.path import basename
    from tqdm import tqdm
    import sys
    data = []
    with open(filename) as f:
        content = f.read().splitlines()
        index = 0
        pbar = tqdm(total=len(content) + 1, desc='load SDF', file=sys.stdout)
        while index < len(content):
            index_old = index

            g = nx.Graph(name=content[index].strip())  # set name of the graph

            tmp = content[index + 3]
            nb_nodes = int(tmp[:3])  # number of the nodes
            nb_edges = int(tmp[3:6])  # number of the edges

            for i in range(0, nb_nodes):
                tmp = content[i + index + 4]
                g.add_node(i, atom=tmp[31:34].strip())

            for i in range(0, nb_edges):
                tmp = content[i + index + g.number_of_nodes() + 4]
                tmp = [tmp[i:i + 3] for i in range(0, len(tmp), 3)]
                g.add_edge(
                    int(tmp[0]) - 1, int(tmp[1]) - 1, bond_type=tmp[2].strip())

            data.append(g)

            index += 4 + g.number_of_nodes() + g.number_of_edges()
            while content[index].strip() != '$$$$':  # seperator
                index += 1
            index += 1

            pbar.update(index - index_old)
        pbar.update(1)
        pbar.close()

    return data


def loadMAT(filename, extra_params):
    """Load graph data from a MATLAB (up to version 7.1) .mat file.

    Notes
    ------
    A MAT file contains a struct array containing graphs, and a column vector lx containing a class label for each graph.
    Check README in downloadable file in http://mlcb.is.tuebingen.mpg.de/Mitarbeiter/Nino/WL/, 2018 for detailed structure.
    """
    from scipy.io import loadmat
    import numpy as np
    import networkx as nx
    data = []
    content = loadmat(filename)
    order = extra_params['am_sp_al_nl_el']
    # print(content)
    # print('----')
    for key, value in content.items():
        if key[0] == 'l':  # class label
            y = np.transpose(value)[0].tolist()
            # print(y)
        elif key[0] != '_':
            # if adjacency matrix is not compressed / edge label exists
            if order[1] == 0:
                for i, item in enumerate(value[0]):
                    # print(item)
                    # print('------')
                    g = nx.Graph(name=i)  # set name of the graph
                    nl = np.transpose(item[order[3]][0][0][0])  # node label
                    # print(item[order[3]])
                    # print()
                    for index, label in enumerate(nl[0]):
                        g.add_node(index, atom=str(label))
                    el = item[order[4]][0][0][0]  # edge label
                    for edge in el:
                        g.add_edge(
                            edge[0] - 1, edge[1] - 1, bond_type=str(edge[2]))
                    data.append(g)
            else:
                from scipy.sparse import csc_matrix
                for i, item in enumerate(value[0]):
                    # print(item)
                    # print('------')
                    g = nx.Graph(name=i)  # set name of the graph
                    nl = np.transpose(item[order[3]][0][0][0])  # node label
                    # print(nl)
                    # print()
                    for index, label in enumerate(nl[0]):
                        g.add_node(index, atom=str(label))
                    sam = item[order[0]]  # sparse adjacency matrix
                    index_no0 = sam.nonzero()
                    for col, row in zip(index_no0[0], index_no0[1]):
                        # print(col)
                        # print(row)
                        g.add_edge(col, row)
                    data.append(g)
                    # print(g.edges(data=True))
    return data, y


def loadTXT(dirname_dataset):
    """Load graph data from a .txt file.

    Notes
    ------
    The graph data is loaded from separate files.
    Check README in downloadable file http://tiny.cc/PK_MLJ_data, 2018 for detailed structure.
    """
    import numpy as np
    import networkx as nx
    from os import listdir
    from os.path import dirname

    # load data file names
    for name in listdir(dirname_dataset):
        if '_A' in name:
            fam = dirname_dataset + '/' + name
        elif '_graph_indicator' in name:
            fgi = dirname_dataset + '/' + name
        elif '_graph_labels' in name:
            fgl = dirname_dataset + '/' + name
        elif '_node_labels' in name:
            fnl = dirname_dataset + '/' + name
        elif '_edge_labels' in name:
            fel = dirname_dataset + '/' + name
        elif '_edge_attributes' in name:
            fea = dirname_dataset + '/' + name
        elif '_node_attributes' in name:
            fna = dirname_dataset + '/' + name
        elif '_graph_attributes' in name:
            fga = dirname_dataset + '/' + name
        # this is supposed to be the node attrs, make sure to put this as the last 'elif'
        elif '_attributes' in name:
            fna = dirname_dataset + '/' + name

    content_gi = open(fgi).read().splitlines()  # graph indicator
    content_am = open(fam).read().splitlines()  # adjacency matrix
    content_gl = open(fgl).read().splitlines()  # lass labels

    # create graphs and add nodes
    data = [nx.Graph(name=i) for i in range(0, len(content_gl))]
    if 'fnl' in locals():
        content_nl = open(fnl).read().splitlines()  # node labels
        for i, line in enumerate(content_gi):
            # transfer to int first in case of unexpected blanks
            data[int(line) - 1].add_node(i, atom=str(int(content_nl[i])))
    else:
        for i, line in enumerate(content_gi):
            data[int(line) - 1].add_node(i)

    # add edges
    for line in content_am:
        tmp = line.split(',')
        n1 = int(tmp[0]) - 1
        n2 = int(tmp[1]) - 1
        # ignore edge weight here.
        g = int(content_gi[n1]) - 1
        data[g].add_edge(n1, n2)

    # add edge labels
    if 'fel' in locals():
        content_el = open(fel).read().splitlines()
        for index, line in enumerate(content_el):
            label = line.strip()
            n = [int(i) - 1 for i in content_am[index].split(',')]
            g = int(content_gi[n[0]]) - 1
            data[g].edges[n[0], n[1]]['bond_type'] = label

    # add node attributes
    if 'fna' in locals():
        content_na = open(fna).read().splitlines()
        for i, line in enumerate(content_na):
            attrs = [i.strip() for i in line.split(',')]
            g = int(content_gi[i]) - 1
            data[g].nodes[i]['attributes'] = attrs

    # add edge attributes
    if 'fea' in locals():
        content_ea = open(fea).read().splitlines()
        for index, line in enumerate(content_ea):
            attrs = [i.strip() for i in line.split(',')]
            n = [int(i) - 1 for i in content_am[index].split(',')]
            g = int(content_gi[n[0]]) - 1
            data[g].edges[n[0], n[1]]['attributes'] = attrs

    # load y
    y = [int(i) for i in content_gl]

    return data, y


def loadDataset(filename, filename_y=None, extra_params=None):
    """load file list of the dataset.
    """
    from os.path import dirname, splitext

    dirname_dataset = dirname(filename)
    extension = splitext(filename)[1][1:]
    data = []
    y = []
    if extension == "ds":
        content = open(filename).read().splitlines()
        if filename_y is None or filename_y == '':
            for i in range(0, len(content)):
                tmp = content[i].split(' ')
                # remove the '#'s in file names
                data.append(
                    loadCT(dirname_dataset + '/' + tmp[0].replace('#', '', 1)))
                y.append(float(tmp[1]))
        else:  # y in a seperate file
            for i in range(0, len(content)):
                tmp = content[i]
                # remove the '#'s in file names
                data.append(
                    loadCT(dirname_dataset + '/' + tmp.replace('#', '', 1)))
            content_y = open(filename_y).read().splitlines()
            # assume entries in filename and filename_y have the same order.
            for item in content_y:
                tmp = item.split(' ')
                # assume the 3rd entry in a line is y (for Alkane dataset)
                y.append(float(tmp[2]))
    elif extension == "cxl":
        import xml.etree.ElementTree as ET

        tree = ET.parse(filename)
        root = tree.getroot()
        data = []
        y = []
        for graph in root.iter('print'):
            mol_filename = graph.attrib['file']
            mol_class = graph.attrib['class']
            data.append(loadGXL(dirname_dataset + '/' + mol_filename))
            y.append(mol_class)
    elif extension == "sdf":
        import numpy as np
        from tqdm import tqdm
        import sys

        data = loadSDF(filename)

        y_raw = open(filename_y).read().splitlines()
        y_raw.pop(0)
        tmp0 = []
        tmp1 = []
        for i in range(0, len(y_raw)):
            tmp = y_raw[i].split(',')
            tmp0.append(tmp[0])
            tmp1.append(tmp[1].strip())

        y = []
        for i in tqdm(range(0, len(data)), desc='ajust data', file=sys.stdout):
            try:
                y.append(tmp1[tmp0.index(data[i].name)].strip())
            except ValueError:  # if data[i].name not in tmp0
                data[i] = []
        data = list(filter(lambda a: a != [], data))
    elif extension == "mat":
        data, y = loadMAT(filename, extra_params)
    elif extension == 'txt':
        data, y = loadTXT(dirname_dataset)

    return data, y
