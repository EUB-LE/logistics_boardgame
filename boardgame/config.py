PLAYER_TYPE_DRIVER = "DRIVER"
PLAYER_TYPE_INDUSTRY = "INDUSTRY"
PLAYER_TYPE_INVESTOR = "INVESTOR"

RUN_ACTION_NAME = "RUN"
FLY_ACTION_NAME = "FLY"
SPECIAL_FLY_ACTION_NAME = "SPECIAL_FLY"
SHARE_RESOURCES_ACTION_NAME = "SHARE_RESOURCES"
GENERATE_GOODS_ACTION_NAME = "GENERATE_GOODS"
COORDINATE_DRIVERS_ACTION_NAME = "COORDINATE_DRIVERS"
TRANSPORT_GOODS_ACTION_NAME = "TRANSPORT_GOODS"
REPAIR_ACTION_NAME = "REPAIR"
DO_NOTHING_ACTION_NAME = "NOTHING"

ALLOWED_ACTIONS = [DO_NOTHING_ACTION_NAME, RUN_ACTION_NAME, FLY_ACTION_NAME, SPECIAL_FLY_ACTION_NAME]
ALLOWED_ACTIONS_DRIVER = ALLOWED_ACTIONS + [SHARE_RESOURCES_ACTION_NAME, REPAIR_ACTION_NAME]
ALLOWED_ACTIONS_INDUSTRY = ALLOWED_ACTIONS + [GENERATE_GOODS_ACTION_NAME, TRANSPORT_GOODS_ACTION_NAME]
ALLOWED_ACTIONS_INVESTOR = ALLOWED_ACTIONS + [SHARE_RESOURCES_ACTION_NAME, COORDINATE_DRIVERS_ACTION_NAME]

TARGET_START_NODE = 19
TARGET_END_NODE = 21 
TARGET_AMOUNT = 3


CASCADE_DEFEAT_LEVEL = 6
CASCADE_DAMAGE_THRESHOLD = 3