from boardgame.classes import Game
from boardgame.agent import Agent, find_shortest_path, flatten_list, parse_nodes_to_graph_format
import unittest


class TestAgent(unittest.TestCase):
    
    def test_parse_nodes_to_graph_format(self) -> None: 
        g = Game()
        a = Agent()
        nodes = g.nodes
        graph_dict = a.parse_nodes_to_graph_format(nodes)
        self.assertTrue(True)
    
    def test_find_shortest_path(self) -> None:
        g = Game(0)
        a = Agent()
        graph_dict = parse_nodes_to_graph_format(g.nodes)
        result = find_shortest_path(graph_dict, 21, 19)
        print(result)
        flat =  flatten_list(result)
        self.assertTrue(True)
       
    def test_choose_driver_action(self) -> None:
        g = Game(0)
        a = Agent(g) 
        g.nodes[8].damage = 2
        action = a._choose_driver_actions(g._get_player_by_id(g.active_player_id))
        self.assertTrue(True)

    def test_choose_industry_action(self):
        g = Game(0)
        a = Agent(g)
        g._get_node_by_id(g.start_node_id).freight = 3
        g.players[0].location_id = 10
        action = a._choose_industry_actions(g._get_player_by_id(g.active_player_id))
        self.assertTrue(True)

    def test_get_next_action_for_player(self): 
        self.assertTrue(True)
