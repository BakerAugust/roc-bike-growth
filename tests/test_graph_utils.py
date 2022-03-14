from roc_bike_growth.graph_utils import get_street_segment, get_intersections
import networkx as nx

def make_test_graph() -> nx.MultiDiGraph:
    '''
    Make a test graph
    '''
    G = nx.MultiDiGraph()

    G.add_nodes_from([1,2,3,4,5,6,7,8,9])
    G.add_edges_from([
        # "A-street"
        (1,2, {'name': 'A-street'}),
        (2,3, {'name': 'A-street'}),
        (2,5, {'name': 'A-street'}),
        (3,4, {'name': 'A-street'}),
        (4,5, {'name': 'A-street'}),
        (5,6, {'name': 'A-street'}),
        (6,7, {'name': 'A-street'}),
        # "B-street"
        (1,8, {'name': 'B-street'}), 
        (1,9, {'name': 'B-street'}),
        # "C-street"
        (4,10, {'name': 'C-street'}),
        (4,11, {'name': 'C-street'}),
        (11,12, {'name': 'C-street'}),
        ])
    
    return G
             

def test_get_intersections() -> None:
    '''
    '''
    G = make_test_graph()
    
    # Node 1 should show as interstsection
    assert get_intersections(G, 'A-street', 'B-street') ==  set([1])
    assert get_intersections(G, 'B-street', 'A-street') ==  set([1])
    
    # Node 4 should show as interstsection
    assert get_intersections(G, 'A-street', 'C-street') ==  set([4])
    assert get_intersections(G, 'C-street', 'A-street') ==  set([4])
    
    # There should be no intersections here
    assert get_intersections(G, 'B-street', 'C-street') ==  set() #empty set
    
    
def test_get_street_segment() -> None:
    '''
    '''
    G = make_test_graph()
    
    out = get_street_segment(G, 'A-street','B-street','C-street')
    assert out == [1,2,3,4]
    

    
    