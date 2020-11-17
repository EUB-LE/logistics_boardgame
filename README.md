# Logistics Boardgame 

This repository contains a Python representation of the boardgame logic. 

## How to use

Clone the repository, cd to the the project root and type  
```python 
from boardgame.classes import * 
g = Game() # Initiate a new game object
g.prepare_game() # Set the parameters, like target card, players, etc.
g.iterate() # Play a full game until a WIN or LOSS. Player actions are determined automatically at random. Will usually result in a LOSS by cascade.
```

The results will be logged in the `game.log` file. 

## Disclaimer 

Not all features are fully implemented yet. Features that are missing 
* Investors cannot remote control other players 
* No different "colors" of freight cubes. Does it have any impact on the game? 