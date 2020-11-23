from __future__ import annotations
from typing import Deque, List, TYPE_CHECKING
from boardgame.config import DO_NOTHING_ACTION_NAME, GENERATE_GOODS_ACTION_NAME, PLAYER_TYPE_DRIVER, PLAYER_TYPE_INDUSTRY, REPAIR_ACTION_NAME, RUN_ACTION_NAME, TRANSPORT_GOODS_ACTION_NAME
from collections.abc import Iterable
from boardgame.player_actions import ACTIONS, PlayerAction, do_player_action_run
if TYPE_CHECKING:
    from boardgame.classes import Game, Player

def parse_nodes_to_graph_format(nodes):
    graph_dict = {} 
    for node in nodes:
        graph_dict[node.id] = node.neighbors
    return graph_dict
    

# Code by Eryk Kopczyński https://www.python.org/doc/essays/graphs/ using Breadth First
# adapted not to use Deque but a simple list instead
def find_shortest_path(graph, start, end):
    dist = {start: [start]}
    q = [start]
    while len(q):
        at = q.pop(0)
        for next in graph[at]:
            if next not in dist:
                dist[next] = [dist[at], next]
                q.append(next)
    return [node for node in flatten_list(dist.get(end))]

# Code from: https://stackoverflow.com/questions/2158395/flatten-an-irregular-list-of-lists 
def flatten_list(l):
    for el in l:
        if isinstance(el, Iterable) and not isinstance(el, (str, bytes, int)):
            yield from flatten_list(el)
        else:
            yield el


class Agent():
    def __init__(self, game:Game) -> None:
        # Hard coded for demonstration 
        self.game = game
        self.graph = parse_nodes_to_graph_format(game.nodes)
        self.node_ids_on_lane = find_shortest_path(self.graph, game.start_node_id, game.end_node_id)
        self.action_queues = {player.id: [] for player in self.game.players}
        self.repair_targets = [] 


    def get_next_action_for_player(self, player_id:int) -> PlayerAction: 
        if len(self.action_queues[player_id]) == 0:
            player_type = self.game._get_player_by_id(player_id).type
            strategy_function = None 
            if player_type == PLAYER_TYPE_DRIVER:
                strategy_function = self._choose_driver_actions
            elif player_type == PLAYER_TYPE_INDUSTRY:
                strategy_function = self._choose_industry_actions
            else:
                strategy_function = self._choose_investor_actions
            self.action_queues[player_id] = strategy_function(self.game._get_player_by_id(player_id))
        return self.action_queues[player_id].pop(0)

    def _choose_driver_actions(self, player:Player) -> list:
        actions = []
        # get damage nodes in lane 
        damaged_nodes_in_lane = [node for node in self.game.nodes if node.damage > 0 and node.id in self.node_ids_on_lane]
        # remove target if the other driver is already doing it
          # delete the oldest repair target 
        if len(self.repair_targets) > 0:
            self.repair_targets.pop(0)
            try:
                damaged_nodes_in_lane.remove(self.repair_targets)
            except ValueError:
                # no harm done
                pass
        if len(damaged_nodes_in_lane) > 0:
            # get highest damaged node in lane
            damaged_nodes_in_lane.sort(reverse=True, key=lambda node: node.damage)
            highest_damage_node = damaged_nodes_in_lane[0]
            # register node as repair target
            self.repair_targets.append(highest_damage_node)
            path_to_node = find_shortest_path(self.graph, player.location_id, highest_damage_node.id)[1:]
            # move to highest damage node in lane and repair if arrived at that node 
            for node in path_to_node:
                actions.append(PlayerAction(self.game, player.id, ACTIONS[RUN_ACTION_NAME], parameters={'destination_id': node}))
            actions.append(PlayerAction(self.game, player.id, action=ACTIONS[REPAIR_ACTION_NAME]))    
            return actions
        # if none is damaged, move to damaged nodes out of lane:
        damaged_nodes = [node for node in self.game.nodes if node.damage > 0] 
        # remove targets if the other driver is already doing it
        if len(self.repair_targets) > 0:
            self.repair_targets.pop(0)
            try:
                damaged_nodes_in_lane.remove(self.repair_targets)
            except ValueError:
                # no harm done
                pass
        if len(damaged_nodes) > 0:
            damaged_nodes.sort(reverse=True, key=lambda node: node.damage) 
            highest_damage_node = damaged_nodes[0]
            # register node as repair target
            self.repair_targets.append(highest_damage_node)
            path_to_node = find_shortest_path(self.graph, player.location_id, highest_damage_node.id)[1:]
            for node in path_to_node:
                actions.append(PlayerAction(self.game, player.id, ACTIONS[RUN_ACTION_NAME], parameters={'destination_id': node}))
            actions.append(PlayerAction(self.game, player.id, action=ACTIONS[REPAIR_ACTION_NAME]))
            return actions
        else:
            return actions.append(PlayerAction(self.game, player.id, ACTIONS[DO_NOTHING_ACTION_NAME]))
        
         

    def _choose_industry_actions(self, player:Player) -> list:
        actions = []
        # IF number of freight units below 3, create new unit 
        number_of_freight_units_in_game = sum([node.freight for node in self.game.nodes])
        if number_of_freight_units_in_game < 3:
            actions.append(PlayerAction(self.game, player.id, ACTIONS[GENERATE_GOODS_ACTION_NAME]))
            return actions 
        # IF freight unit at current location move towards destination 
        if self.game._get_node_by_id(player.location_id).freight > 0 and not player.location_id == self.game.end_node_id: 
            path_to_destination = find_shortest_path(self.graph, player.location_id, self.game.end_node_id)[1:]
            for node in path_to_destination:
                actions.append(PlayerAction(self.game, player.id, ACTIONS[TRANSPORT_GOODS_ACTION_NAME], parameters={'destination_id': node}))
            return actions 
        # ELSE move towards closest node with freight units 
        else:
            nodes_with_freight_units = [node for node in self.game.nodes if node.freight > 0 and node.id != self.game.end_node_id]
            path_to_nodes = {}
            for node in nodes_with_freight_units:
                path_to_nodes[node.id] = find_shortest_path(self.graph, player.location_id, node.id)[1:]
            closest_node_id = min(path_to_nodes, key=path_to_nodes.get)
            for node in path_to_nodes[closest_node_id]:
                actions.append(PlayerAction(self.game, player.id, ACTIONS[RUN_ACTION_NAME], parameters={'destination_id': node}))
            return actions 
    
    def _choose_investor_actions(self, player:Player) -> list:
        return [PlayerAction(self.game, player.id, ACTIONS[DO_NOTHING_ACTION_NAME])]






