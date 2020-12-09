# Logistics Boardgame 

This repository contains the code to a python representation of the cooperative boardgame "SCHLEUSEN SPIEL". For demonstration purposes, we developed a simple game agent that utilizes greedy heuristics to choose player actions and can play the game without human supervision. A subsequent simulation study analyzes the impact of a set of game parameters on the performance of the simple agent. 

This repository contains 
* boardgame: Package that provides the backend logic for the board game and the agent. 
* tests: Testing directory
* presentation.ipynb: Jupyter notebook presentation and evaluation using a simple agent to chose player actions. 

## How to use

Clone the repository, cd to the the project root and type  
```python 
from boardgame.classes import * 
from boardgame.agent import Agent
g = Game() # Initiate a new game object and set custom parameters if desired.
a = Agent(g) # Initiate the agent to control the player actions. 
g.set_agent(a) # Registre the agent with the game. 
result = g.play_game()  # Play a full game until a WIN or LOSS. Ther result dictionary contains more details. 
```
The results will be logged into `game.log` in the current directory. 

## How it works 
The package boardgame contains all python logic. 
* classes.py: contains all classes directly used in the game logic 
* player_actions.py: defines the methods that manipulate the board state according to the player action 
* config: custom configuration for constants
* agent: agent definition and heuristics. 

For a deeper insight on how the logic is set up, start at the method `Game.play_game()`. It references the game loop. 

