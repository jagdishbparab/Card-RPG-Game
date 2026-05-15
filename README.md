Make sure you have Python installed. You only need the pygame library to run this game.
Run the game:The game relies on elemental_ui.py as the main engine.

How to Play
The game loops through two distinct phases until a player's HP reaches 0:

1. Draft Phase
12 cards are generated in the center of the screen (Guaranteed 2 of each element + 4 randoms for fair RNG).

You and the AI take turns picking 1 card at a time until both players have exactly 6 cards in their hand.

2. Cast Phase
Select exactly 2 cards from your hand to combine and attack.

Once you lock in your choice, click the Confirm Attack button.

Watch the elements collide! The reaction determines your damage and any special status effects.

When you only have 2 cards left, the game will automatically combine them for a final attack and deal a fresh Draft Pool.

File Structure
elemental_logic.py: The Brain. Handles the Reaction Matrix, Predictive AI, Game State, and math.

elemental_ui.py: The Engine. Handles Pygame rendering, event clicks, the game loop, and particle effects.

(Optional Image Assets): The game automatically detects and loads battlefield.jpg, pyro.png, hydro.png, cryo.png, and electro.png if they are placed in the same folder. If missing, it gracefully falls back to clean colored geometric UI.

                    “The best games aren’t built—they’re alchemized, one reaction at a time.”
