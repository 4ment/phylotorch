import numpy as np
import torch
import torch.jit


class BranchLengthTransform(object):
    def __init__(self, bounds, indexing):
        self.bounds = bounds
        self.indexing = indexing

    def __call__(self, node_heights):
        return heights_to_branch_lengths(node_heights, self.bounds, self.indexing)


def heights_to_branch_lengths(node_heights, bounds, indexing):
    taxa_count = int((bounds.shape[0] + 1) / 2)
    indices_sorted = indexing[np.argsort(indexing[:, 1])].transpose()
    return torch.cat((node_heights[indices_sorted[0, :taxa_count] - taxa_count] - bounds[:taxa_count],
                      node_heights[indices_sorted[0, taxa_count:] - taxa_count] - node_heights[
                          indices_sorted[1, taxa_count:] - taxa_count]))


def transform_ratios(ratios_root_height, bounds, indexing):
    ### # type: (Tensor, Tensor, Tuple[Tuple[int, int], ...]) -> Tensor
    """
    Transform node ratios/root height to internal node heights.
    :param root_height: root height
    :param ratios: node ratios of internal nodes
    :param bounds: lower bound of each node
    :param indexing: pairs of parent/child indices, must be preorder or inorder
    :return: internal node heights
    """
    taxa_count = ratios_root_height.shape[0] + 1
    heights = ratios_root_height.clone()
    for parent_id, id in indexing:
        if id >= taxa_count:
            heights[id - taxa_count] = bounds[id] + ratios_root_height[id - taxa_count] * (
                    heights[parent_id - taxa_count] - bounds[id])
    return heights


def setup_indexes(tree):
    for node in tree.postorder_node_iter():
        node.index = -1
        node.annotations.add_bound_attribute("index")

    s = len(tree.taxon_namespace)
    taxa_dict = {taxon.label: idx for idx, taxon in enumerate(tree.taxon_namespace)}

    for node in tree.postorder_node_iter():
        if not node.is_leaf():
            node.index = s
            s += 1
        else:
            node.index = taxa_dict[node.taxon.label]


def setup_dates(tree, heterochronous=False):
    # parse dates
    if heterochronous:
        dates = {}
        for node in tree.leaf_node_iter():
            dates[str(node.taxon)] = float(str(node.taxon).split('_')[-1][:-1])

        max_date = max(dates.values())
        min_date = min(dates.values())
        print(min_date, max_date)

        # time starts at 0
        if min_date == 0:
            for node in tree.leaf_node_iter():
                node.date = dates[str(node.taxon)]
                node.original_date = dates[str(node.taxon)]
            oldest = max_date
        # time is a year
        else:
            for node in tree.leaf_node_iter():
                node.date = max_date - dates[str(node.taxon)]
                node.original_date = dates[str(node.taxon)]
            oldest = max_date - min_date
    else:
        for node in tree.postorder_node_iter():
            node.date = 0.0
            node.original_date = 0.0
        oldest = None

    return oldest


class Node:
    def __init__(self, name, height=0.0):
        self.name = name
        self.height = height
        self.parent = None
        self.children = []

    def __iter__(self):
        if len(self.children) > 0:
            for c in self.children[0]:
                yield c
            for c in self.children[1]:
                yield c
        yield self


def random_tree_from_heights(sampling, heights):
    nodes = [Node('taxon{}'.format(idx), height=s) for idx, s in enumerate(sampling)]

    for i, height in enumerate(heights):
        indexes = []
        for idx, node in enumerate(nodes):
            if node.height < height:
                indexes.append(idx)
        idx1 = idx2 = np.random.randint(0, len(indexes))
        while idx1 == idx2:
            idx2 = np.random.randint(0, len(indexes))
        new_node = Node('node{}'.format(len(nodes)), height=height)
        idx1, idx2 = sorted([idx1, idx2])
        new_node.children = (nodes[indexes[idx1]], nodes[indexes[idx2]])
        nodes[idx1].parent = nodes[idx2].parent = new_node
        nodes[idx1] = new_node
        del nodes[idx2]
    return nodes[0]
