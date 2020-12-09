from __future__ import annotations
from boardgame.config import ALLOWED_ACTIONS, COORDINATE_DRIVERS_ACTION_NAME, DO_NOTHING_ACTION_NAME, FLY_ACTION_NAME, GENERATE_GOODS_ACTION_NAME, PLAYER_TYPE_DRIVER, PLAYER_TYPE_INDUSTRY, PLAYER_TYPE_INVESTOR, REPAIR_ACTION_NAME, RUN_ACTION_NAME, SHARE_RESOURCES_ACTION_NAME, SPECIAL_FLY_ACTION_NAME, TRANSPORT_GOODS_ACTION_NAME
from typing import Any, Callable, TYPE_CHECKING
if TYPE_CHECKING:
    from boardgame.classes import Game, Player
import logging

# logging configuration 
try:
    logging.basicConfig(filename='game.log', encoding='utf-8', level=logging.DEBUG, filemode='w')
except ValueError:
    # produces a value error that does not seem to have any effect, so ignoring it. Possible a bug in python version 3.7.x
    pass

def do_player_action_nothing(game:Game, player_id:int) -> None:
    """Spend an action point without doing anything (skip). 

    Args:
        game (Game): [description]
        player_id (int): [description]
    """
    pass

def do_player_action_run(game:Game, player_id:int, destination_id:int) -> None:
    """Move (run) to a neighboring node. 

    Args:
        game (Game): [description]
        player_id (int): Id of the moving player.
        destination_id (int): Id of the destination node. 

    Raises:
        InvalidActionException: If the action is not feasible with the given parameters. 
    """
    player = game._get_player_by_id(player_id)
    player_current_node_id = player.location_id
    if destination_id not in game._get_node_by_id(player_current_node_id).neighbors:
        raise InvalidActionException(player)
    player.location_id = destination_id
    
def do_player_action_fly(game:Game, player_id:int, destination_id:int) -> None:
    """Fly to a orange node.

    Args:
        game (Game): [description]
        player_id (int): [description]
        destination_id (int): [description]

    Raises:
        InvalidActionException: If the action is not feasible with the given parameters. 
    """
    player = game._get_player_by_id(player_id)
    player_current_node_id = player.location_id
    valid_destination_ids = [node.id for node in game.nodes if node.node_type in ['orange']]
    if destination_id not in valid_destination_ids:
        raise InvalidActionException(player)
    if player.funds < 2:
        raise InvalidActionException(player)
    player.location_id = destination_id
    player.funds -= 2
    
def do_player_action_special_flight(game:Game, player_id:int, destination_id:int) -> None:
    """Special fly to a purple node.

    Args:
        game (Game): [description]
        player_id (int): [description]
        destination_id (int): [description]

    Raises:
        InvalidActionException: If the action is not feasible with the given parameters.
    """
    player = game._get_player_by_id(player_id)
    valid_destination_ids = [node.id for node in game.nodes if node.node_type in ['purple']]
    if destination_id not in valid_destination_ids:
        raise InvalidActionException(player)
    game.location_id = destination_id

def do_player_action_share_resources(game:Game, player_id:int, target_player_id:int) -> None:
    """Transfer 1 fund to a player that is at the same node. 

    Args:
        game (Game): [description]
        player_id (int): [description]
        target_player_id (int): [description]

    Raises:
        InvalidActionException: If the action is not feasible with the given parameters.
    """
    player = game._get_player_by_id(player_id)
    target_player = game._get_player_by_id(target_player_id)
    if player.funds < 1: 
        raise InvalidActionException(player)
    if target_player.location_id != player.location_id:
        raise InvalidActionException(player) 
    player.funds -= 1
    target_player.funds += 1
    
def do_player_action_repair(game:Game, player_id:int) -> None:
    """Remove 1 damage point from the node the player is currently located. 

    Args:
        game (Game): [description]
        player_id (int): [description]

    Raises:
        InvalidActionException: If the action is not feasible with the given parameters.
    """
    player = player = game._get_player_by_id(player_id)
    node = game._get_node_by_id(player.location_id)
    if player.funds < 1: 
        raise InvalidActionException(player)
    if node.damage < 1: 
        raise InvalidActionException(player) 
    player.funds += 1
    node.damage -=1
    
def do_player_action_generate_goods(game:Game, player_id:int) -> None:
    """Generate 1 freight unit at the node the player is currently located at. 

    Args:
        game (Game): [description]
        player_id (int): [description]

    Raises:
        InvalidActionException: If the action is not feasible with the given parameters.
    """
    player = game._get_player_by_id(player_id)
    node = game._get_node_by_id(game.start_node_id)
    if player.funds < 2: 
        raise InvalidActionException(player) 
    if node.freight >= 3: 
        raise InvalidActionException(player) 
    player.funds -= 2
    node.freight += 1
    
def do_player_action_transport_goods(game:Game, player_id:int, destination_id:int) -> None:
    """Transport 1 freight unit from the current location to the destination location. 

    Args:
        game (Game): [description]
        player_id (int): [description]
        destination_id (int): [description]

    Raises:
        InvalidActionException: If the action is not feasible with the given parameters.
    """
    player = game._get_player_by_id(player_id)
    node = game._get_node_by_id(player.location_id)
    target_node = game._get_node_by_id(destination_id)
    action_cost = 1
    if node.damage == 2: 
        action_cost = 2
    if node.freight < 1:
        raise InvalidActionException(player)
    if node.damage >= 3:
        raise InvalidActionException(player)
    if action_cost > player.actions_left: 
        raise InvalidActionException(player)
    player.actions_left -= (action_cost - 1) # add one because every action automatically cost one action point
    node.freight -= 1
    target_node.freight += 1
    ACTIONS[RUN_ACTION_NAME](game, player_id, destination_id)
 
def do_player_action_coordinate_drivers(game:Game, player_id:int, target_player_id:int, destination_id:int) -> None:
    """Use an action point to move one of the driver players when it is not their turn. 

    Args:
        game (Game): [description]
        player_id (int): [description]
        target_player_id (int): [description]
        destination_id (int): [description]

    Raises:
        InvalidActionException: If the action is not feasible with the given parameters.
    """
    player = game._get_player_by_id(player_id)
    target_player = game._get_player_by_id(target_player_id)
    try:
        game.do_player_action_run(target_player_id, destination_id)
    except InvalidActionException as e:
        raise InvalidActionException(player)

def get_valid_player_actions(game:Game, player_id:int) -> list[PlayerAction]:
    """Returns all valid player actions for a given player at the current state of the game. This implementation is brittle and should not be used except for demonstration purpose. 

    Args:
        game (Game): [description]
        player_id (int): [description]

    Returns:
        list[PlayerAction]: List of possible actions for the player. 
    """
    valid_actions = [] 
    player = game._get_player_by_id(player_id)
    player_node = game._get_node_by_id(player.location_id)
    # PASS
    # passing introduced as 'doing nothing'
    valid_actions.append(PlayerAction(game, player_id, ACTIONS[DO_NOTHING_ACTION_NAME]))
    # RUN 
    # running to neighboring nodes is always valid 
    neighbor_node_ids = player_node.neighbors
    for neighbor_node_id in neighbor_node_ids:
        valid_actions.append(PlayerAction(game, player_id, ACTIONS[RUN_ACTION_NAME], parameters={
            "destination_id": neighbor_node_id}
            ))
    # FLY
    # flying is valid to all orange nodes that are not the players current location
    orange_node_ids = [node.id for node in game.nodes if node.node_type in ['orange']]
    if player.location_id in orange_node_ids:
        orange_node_ids.remove(player.location_id) 
    # flying costs 2 funds 
    if player.funds - 2 >= 0: 
        for orange_node_id in orange_node_ids:
            valid_actions.append(PlayerAction(game, player_id, ACTIONS[FLY_ACTION_NAME], parameters={
                "destination_id":orange_node_id}
                ))
    # SPECIAL FLY 
    # special flying is valid to all purple nodes that are not the players current location
    purple_node_ids = [node.id for node in game.nodes if node.node_type in ['purple']]
    if player.location_id in purple_node_ids:
        purple_node_ids.remove(player.location_id)
    for purple_node_id in purple_node_ids:
        valid_actions.append(PlayerAction(game, player_id, ACTIONS[SPECIAL_FLY_ACTION_NAME], parameters={
           "destination_id": purple_node_id
        }))
    # TYPE DEPENDENT ACTIONS: DRIVER ACTIONS 
    if player.type is PLAYER_TYPE_DRIVER:
        # SHARE RESOuRCES 
        # 1 fund can be shared with a player at the same location 
        if player.funds - 1 >= 0:
            same_node_player_ids = [other_player.id for other_player in game.players if other_player.location_id == player.location_id]
            same_node_player_ids.remove(player_id)
            for same_node_player_id in same_node_player_ids:
                valid_actions.append(PlayerAction(game, player_id, ACTIONS[SHARE_RESOURCES_ACTION_NAME], parameters={
                    "target_player_id" : same_node_player_id
                })) 
        # REPAIR 
        # repair is valid if the current node has damage and 1 fund is available
        if player.funds - 1 >= 0 and player_node.damage > 0:
            valid_actions.append(PlayerAction(game, player_id, ACTIONS[REPAIR_ACTION_NAME]))
    # TYPE DEPENDEND ACTIONS: INDUSTRY ACTIONS
    if player.type is PLAYER_TYPE_INDUSTRY:
        # GENERATE GOODS
        # generate goods costs 2 funds and is valid if the current node has less than 2 freight
        if player.funds - 2 >= 0 and player_node.freight < 3:
            valid_actions.append(PlayerAction(game, player_id, ACTIONS[GENERATE_GOODS_ACTION_NAME]))
        # TRANSPORT GOODS 
        # transport goods is valid if starting node has less than 2 (3) damage and costs 1 (2) AP 
        if player_node.freight > 0 and (player_node.damage < 2 or (player_node.damage == 2 and player.actions_left - 2 >= 0)):
            for node_id in player_node.neighbors:
                valid_actions.append(PlayerAction(game, player_id, ACTIONS[TRANSPORT_GOODS_ACTION_NAME], parameters={
                    "destination_id":node_id}
                    ))
    # TYPE DEPENDEND ACTIONS: INVESTOR ACTIONS 
    if player.type is PLAYER_TYPE_INVESTOR:
        # SHARE RESOURCES
        # 1 fund can be shared with a player at the same location 
        if player.funds - 1 >= 0:
            same_node_player_ids = [other_player.id for other_player in game.players if other_player.location_id == player.location_id]
            same_node_player_ids.remove(player_id)
            for same_node_player_id in same_node_player_ids:
                valid_actions.append(PlayerAction(game, player_id, ACTIONS[SHARE_RESOURCES_ACTION_NAME], parameters={
                    "target_player_id": same_node_player_id}
                    ))
        # COORDINATE DRIVERS
        # TODO: rewrite
        # coordinate drivers is only valid for player type driver and valid move actions 
        #driver_player_ids = [player.id for player in game.players if player.type == PLAYER_TYPE_DRIVER]
        #for driver_player_id in driver_player_ids:
        #    valid_driver_move_actions = [player_action for player_action in get_valid_player_actions(game, driver_player_id) if player_action.action.__name__ in ALLOWED_ACTIONS]
        #    for valid_driver_action in valid_driver_move_actions:
        #        valid_actions.append(PlayerAction(game, player_id, valid_driver_action.action, valid_driver_action.parameters))

    return valid_actions

ACTIONS ={
    RUN_ACTION_NAME: do_player_action_run,
    FLY_ACTION_NAME: do_player_action_fly,
    SPECIAL_FLY_ACTION_NAME: do_player_action_special_flight,
    GENERATE_GOODS_ACTION_NAME: do_player_action_generate_goods,
    COORDINATE_DRIVERS_ACTION_NAME: do_player_action_coordinate_drivers,
    TRANSPORT_GOODS_ACTION_NAME: do_player_action_transport_goods,
    REPAIR_ACTION_NAME: do_player_action_repair,
    SHARE_RESOURCES_ACTION_NAME: do_player_action_share_resources, 
    DO_NOTHING_ACTION_NAME: do_player_action_nothing
}

class PlayerAction():
    """Represents a player action. 
    """
    def __init__(self, game:Game, player_id:int, action:Callable, parameters:dict[str,Any]=None) -> None:
        """Cosntructor of baordgame.player_actions.PlayerAction

        Args:
            game (Game): Reference to the game object. 
            player_id (int): Id of the player this action belongs to. 
            action (Callable): Method reference to the action. 
            parameters (dict[str,Any], optional): Parameters of the action. Defaults to None.
        """
        self.game = game
        self.player_id = player_id
        self.action = action
        self.parameters = parameters

    def run(self) -> None:
        """Executes the player action with the given parameters and logs to log file. 
        """
        self.action(self.game, self.player_id, **self.parameters) if self.parameters else self.action(self.game, self.player_id)
        player = self.game._get_player_by_id(self.player_id)
        logging.info(f"{player.name} {self.action.__name__} (parameters: {self.parameters})")
        logging.info(f"Player Status: {player.__dict__}" )
        logging.info(f"Node Status: {self.game._get_node_by_id(player.location_id).__dict__}")

class InvalidActionException(Exception):
    def __init__(self, player:Player, message:str=""):
        self.player = player
        self.message = message 
