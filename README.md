# GPTChessmate

GPTChessmate is an open-source chess game implementation that supports human, AI (ChatGPT), and Stockfish players. The game can be played in a graphical user interface (GUI) using Pygame or in a command-line interface (CLI).

## Table of Contents

- [Usage](#usage)
- [Configuration](#configuration)
  - [OpenAI API Settings](#openai-api-settings)
  - [Player Settings](#player-settings)
  - [Stockfish Engine Path](#stockfish-engine-path)
  - [GUI Settings](#gui-settings)
- [Installation](#installation)
- [How to Use](#how-to-use)
- [Known Compatibility Issues](#known-compatibility-issues)

## Usage

GPTChessmate supports different player types for White and Black, including human players, ChatGPT, and Stockfish. The game can be played in a GUI or CLI mode, and the player types can be selected at the start of the game.

## Configuration

### OpenAI API Settings

- **API Key**: Replace `'sk-'` in `openai.api_key` with your actual OpenAI API key in line 15.
- **Base URL**: If you are using a different API base URL, set `base_url` and `openai.base_url` accordingly in line 18.

### Player Settings

The `PLAYER_SETTINGS` dictionary configures the settings for White and Black players. You can modify the model names, system prompts, and other parameters.

- **Model**: Specify the AI model to use for each player in line 98.
- **System Prompt**: Customize the prompt provided to the AI in line 99.
- **Pre/Post Content**: Modify the content displayed before and after the prompt in line 103 and 107.
- **Chain of Thought (COT)**: The COT prompt is currently not included in the system prompt. You can uncomment it in line 101 and modify it as needed in line 32. (After testing, COT cannot improve the accuracy of ChatGPT's chess game, but it can somewhat reduce illegal outputs.)

### Stockfish Engine Path

Ensure that the `STOCKFISH_PATH` variable in line 23 points to the correct path of the Stockfish executable on your system. If you don't use Stockfish for gameplay, you don't need to set a path. This program can currently only use Stockfish to get the best move for playing against humans or LLMs, and cannot use Stockfish for analysis.

### GUI Settings

- **Piece Images**: The GUI uses piece images from the `images` directory. Ensure that the images are present and correctly named.

## Installation

To run this project, you need to install the required Python packages. You can install them using:

```bash
pip install chess pandas openai pygame stockfish tabulate
```
or
```bash
pip install -r requirements.txt
```

If there are any compatibility issues, specify the version number of the package.
```
chess==1.11.1
pandas==2.2.3
openai==1.54.5
pygame==2.6.1
stockfish==3.28.0
tabulate==0.9.0
```

## How to Use

0. **Download GPTChessmate**: Download the repository from GitHub:
   ```bash
   https://github.com/jimmyshjj/GPTChessmate/archive/refs/heads/main.zip
   ```

1. **Set Up Configurations**: 
   - Set up your OpenAI API key, Stockfish engine path, and other configurations as described in the [Configuration](#configuration) section.

2. **Install Python and Requirements**:
   - Ensure Python is installed on your system.
   - Install the required Python packages as described in the [Installation](#installation) section.

3. **Run the Game**:
   - Navigate to the directory where the game files are located.
   - Run the game using the following command:
     ```bash
     python gpt_chess_gui.py
     ```
     or, if your operating system need to specify to use Python 3:
     ```bash
     python3 gpt_chess_gui.py
     ```
   - Choose whether to use GUI or not.
   - Follow the on-screen instructions to make moves and interact with the game.

4. **LLM Output Handling**:
   - The AI (LLM) may occasionally output illegal moves. Be patient and allow it to retry.
   - In later stages of the game or in specific situations (e.g., when GPT has fewer pieces), the AI may struggle to output correct moves. You can provide an additional prompt to guide the AI.

## Known Compatibility Issues

1. **Small Models**: Smaller models may struggle to output moves in the correct format, may frequently output illegal moves, or may exhibit hallucinations. It is not recommended to use small models for this game.

2. **DeepSeek Models**: DeepSeek models may not always adhere to the requirement of providing a Chain of Thought (COT) analysis.

3. **ChatGPT 4o/4o mini/o1; Gemini 1.5 pro/2.0 Flash**: These models have been tested and, while they may occasionally output illegal moves, they are generally usable. However, they may require multiple retries to produce a valid move.

## Acknowledgments

- **OpenAI/Google/Deepseek** for providing the LLM models and helping finish this program.
- **Pygame** for the GUI components.
- **Stockfish** for the chess engine.
- **Python Chess Library** for chess logic support.
- **Icons from en-croissant**: The chess piece icons used in the GUI are sourced from [en-croissant](https://github.com/franciscoBSalgueiro/en-croissant/blob/master/public/pieces/chess7.css), licensed under the GPL-3.0 license.

## License

This project is licensed under the GPL-3.0 License - see the [LICENSE](LICENSE) file for details.
