import threading
import chess
import pandas as pd
import openai
import re
import pygame
import sys
import os
import tkinter as tk
from tkinter import simpledialog
from datetime import datetime
from stockfish import Stockfish

# 设置 OpenAI API 密钥
openai.api_key = 'sk-'

# 设置 OpenAI API 基础 URL（可选）
base_url = 'https://api.openai.com/v1/'
if base_url:
    openai.base_url = base_url

# Stockfish 引擎的路径（请根据实际情况修改路径）
STOCKFISH_PATH = r"D:\软件\stockfish\stockfish-windows-x86-64-avx2.exe"

# 棋子符号映射，用于显示棋盘
PIECE_SYMBOLS = {
    "P": "♙", "N": "♘", "B": "♗", "R": "♖", "Q": "♕", "K": "♔",  # 白棋
    "p": "♟", "n": "♞", "b": "♝", "r": "♜", "q": "♛", "k": "♚"   # 黑棋
}

# 配置每方的设置，包括模型、提示信息等
COT = (
    "As a Chess Grandmaster, you must approach each move with meticulous attention to detail, carefully and thoroughly finishing the following *Chain of Thought for Analyzing Chess Moves* to ensure the best possible decision on every turn:\n\n"
    "0. Analyze the Current Situation:\n"
    "   - What is the overall state of the game (opening, middle game, endgame)?\n"
    "   - How have the previous moves shaped the current position?\n"
    "   - Are there any immediate tactical or strategic threats from either side?\n"
    "   - What is the psychological state of the game (e.g., is one player under time pressure)?\n\n"
    "1. Evaluate the Board:\n"
    "   - What is the current position on the board, and how is the material balance?\n"
    "   - What are my strategic goals in this position?\n"
    "   - What might be the opponent’s plans or objectives?\n\n"
    "2. Identify Threats and Opportunities:\n"
    "   - Are any of my pieces under attack or vulnerable to capture?\n"
    "   - Can I effectively attack or threaten any of my opponent’s pieces?\n"
    "   - Are there tactical motifs present, such as forks, pins, skewers, or discovered attacks, that I can exploit?\n\n"
    "3. Check for Opening Patterns and Known Games:\n"
    "   - Does the current position match any common opening lines or well-known chess games?\n"
    "   - Am I following established strategies for this opening, or have I deviated?\n"
    "   - Are there documented countermeasures or adjustments I should apply against the opponent’s opening?\n"
    "   - If the position has deviated from standard theory, how can I stabilize and regain control?\n\n"
    "4. Generate Candidate Moves:\n"
    "   - Have you reviewed the board diagram carefully?\n"
    "     - Which pieces on the board are yours, and which of them can legally move in this position?\n"
    "   - What are all the legal moves I can play in this position?\n"
    "     - For each candidate move:\n"
    "       1. Piece Identification and Position Check: Identify the piece being moved and confirm its starting coordinates.\n"
    "       2. Movement Rule Verification: Verify that the proposed movement adheres to the specific legal rules for that piece (e.g., pawns move forward but capture diagonally, bishops move diagonally, knights jump, etc.).\n"
    "       3. Destination Square Analysis: Confirm that the destination square is valid by:\n"
    "          - Ensuring it is within the boundaries of the board.\n"
    "          - Checking if the square is unoccupied or, if occupied, ensuring that the occupying piece belongs to the opponent and is capturable.\n"
    "       4. Special Rule Checks:\n"
    "          - If moving a pawn, confirm whether promotion, en passant, or capture rules apply.\n"
    "          - For castling, confirm that neither the king nor the rook involved has moved, that all squares between them are unoccupied, and that the king does not pass through or end on a square under attack.\n"
    "       5. King Safety Check: Ensure the move does not place or leave your king in check. For moves involving the king, confirm that the destination square is not attacked by any opponent’s pieces.\n\n"
    "5. Analyze Candidate Moves:\n"
    "   - For each move:\n"
    "     1. What are the opponent’s most likely responses or strongest counterplay options?\n"
    "     2. How might the opponent’s response create threats or change the position?\n"
    "     3. What countermeasures can I prepare for their best responses?\n"
    "     4. After the opponent’s expected responses:\n"
    "        - Will my king remain safe, or is there any risk of exposure?\n"
    "        - Does the move improve the activity, coordination, or positioning of my pieces?\n"
    "        - Does it enhance my control of key squares, open files, or critical areas of the board?\n"
    "        - How will the material and positional balance shift?\n\n"
    "6. Develop and Refine Strategies:\n"
    "   - What are my short-term and long-term strategic plans following this move?\n"
    "   - How does this move set up future tactical opportunities or defensive measures?\n"
    "   - Anticipate the opponent’s strategy and adjust my plans accordingly.\n"
    "   - Identify potential weaknesses in my position and plan how to address them.\n\n"
    "7. Assess Long-Term Plans:\n"
    "   - Does this move align with my broader strategic goals?\n"
    "   - Will it contribute to a favorable middle-game or endgame position?\n\n"
    "8. Final Verification:\n"
    "   - Reassess the legality of the move:\n"
    "     - Confirm compliance with all movement and capture rules for the piece.\n"
    "     - Recheck that the move does not place or leave the king in check, even after the opponent’s most likely responses.\n"
    "   - Have I addressed all immediate and long-term threats that could arise?\n"
    "   - Could this move lead to traps, delayed disadvantages, or unforeseen vulnerabilities?\n"
    "   - Does this move ultimately strengthen my position while aligning with my strategic objectives?\n\n"
    "9. Synthesize and Decide:\n"
    "   - Combine insights from all the above steps to determine the most appropriate and effective move.\n"
    "   - Ensure that the chosen move optimally balances immediate tactical needs with long-term strategic objectives.\n"
)

PLAYER_SETTINGS = {
    "white": {
        "model": "chatgpt-4o-latest",
        "system_prompt":  (
            "You are an experienced white chess player.\n"
            #f"{COT}"
        ),
        "pre_content": "You are about to make a move as White.",
        "provide_game_history": True,
        "provide_game_diagram": True,
        "provide_chat_history": True,
        "post_content": (
            "Please provide your best move in standard algebraic notation (e.g., e4, Nf3, Bb5), and write it on a separate line surrounded by triple hashes (###), like this:\n###\ne4\n###"
        ),
    },
    "black": {
        "model": "chatgpt-4o-latest",
        "system_prompt": (
            "You are an experienced black chess player.\n"
            #f"{COT}"
        ),
        "pre_content": "You are about to make a move as Black.",
        "provide_game_history": True,
        "provide_game_diagram": True,
        "provide_chat_history": True,
        "post_content": (
            "Please provide your best move in standard algebraic notation (e.g., e4, Nf3, Bb5), and write it on a separate line surrounded by triple hashes (###), like this:\n###\ne4\n###"
        ),
    }
}

# 用于存储聊天记录
CHAT_HISTORY = {
    "white": [],
    "black": []
}

# 全局变量，用于判断是否启用GUI
ENABLE_GUI = False
PIECE_IMAGES = {}
SCREEN = None
CLOCK = None
FPS = 60
SQUARE_SIZE = 80  # 棋盘格大小

# 新增：用于跟踪棋盘是否被翻转
board_flipped = False

# 定义颜色
WHITE_COLOR = (255, 255, 255)
BLACK_COLOR = (0, 0, 0)
LIGHT_SQUARE_COLOR = (240, 217, 181)  # 浅棕色
DARK_SQUARE_COLOR = (181, 136, 99)    # 深棕色
BUTTON_COLOR = (70, 70, 70)
BUTTON_HOVER_COLOR = (100, 100, 100)
BUTTON_TEXT_COLOR = (255, 255, 255)
BACKGROUND_COLOR = (50, 50, 50)
TEXT_COLOR = (255, 255, 255)

# 新增配色方案
BG_COLOR = (30, 30, 30)
PANEL_COLOR = (40, 40, 40)
HIGHLIGHT_COLOR = (100, 100, 100)

# 全局变量，存储玩家类型和时间戳
white_player_type = None
black_player_type = None
timestamp = None  # 全局时间戳

# 添加全局变量 is_paused，用于控制游戏是否暂停
is_paused = False

# 全局变量，用于additional_prompt
additional_prompt = None

# 定义自定义异常
class RestartGameException(Exception):
    """自定义异常，用于重新启动游戏"""
    pass

# 定义按钮类
class Button:
    def __init__(self, rect, color, text, text_color=BUTTON_TEXT_COLOR, font_size=24):
        self.rect = pygame.Rect(rect)
        self.color = color
        self.text = text
        self.text_color = text_color
        self.font = pygame.font.SysFont("Arial", font_size)
        self.text_surface = self.font.render(text, True, self.text_color)
        self.text_rect = self.text_surface.get_rect(center=self.rect.center)
        self.hovered = False

    def draw(self, surface):
        pygame.draw.rect(surface, self.color if not self.hovered else BUTTON_HOVER_COLOR, self.rect, border_radius=10)
        surface.blit(self.text_surface, self.text_rect)

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)

    def update_text(self, new_text):
        """更新按钮的文本"""
        self.text = new_text
        self.text_surface = self.font.render(self.text, True, self.text_color)
        self.text_rect = self.text_surface.get_rect(center=self.rect.center)

    def check_hover(self, mouse_pos):
        self.hovered = self.rect.collidepoint(mouse_pos)

def initialize_gui():
    global PIECE_IMAGES, SCREEN, CLOCK, SQUARE_SIZE, restart_button, pause_button, stop_button, flip_button, status_bar
    pygame.init()
    WIDTH, HEIGHT = 1100, 720  # 增加宽度以容纳游戏历史记录
    SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption('Chess Game')
    CLOCK = pygame.time.Clock()

    # 加载棋子图像
    pieces = ['P', 'N', 'B', 'R', 'Q', 'K',
              'p', 'n', 'b', 'r', 'q', 'k']
    for piece in pieces:
        color = 'white' if piece.isupper() else 'black'
        piece_symbol = piece.upper()
        image_filename = f"{piece_symbol}_{color}.png"
        image_path = os.path.join('images', image_filename)
        try:
            image = pygame.image.load(image_path).convert_alpha()
            PIECE_IMAGES[piece] = pygame.transform.smoothscale(image, (SQUARE_SIZE, SQUARE_SIZE))
        except pygame.error as e:
            print(f"无法加载图像 {image_filename}: {e}")
            pygame.quit()
            sys.exit(1)
    
    # 创建按钮
    button_width = 140
    button_height = 50
    button_x = 820  # 调整按钮的 x 坐标以适应新宽度
    button_y_start = 400
    button_spacing = 70
    restart_button = Button(
        rect=(button_x, button_y_start, button_width, button_height),
        color=BUTTON_COLOR,
        text="Restart",
        font_size=26
    )
    pause_button = Button(
        rect=(button_x, button_y_start + button_spacing, button_width, button_height),
        color=BUTTON_COLOR,
        text="Pause",
        font_size=26
    )
    stop_button = Button(
        rect=(button_x, button_y_start + 2 * button_spacing, button_width, button_height),
        color=BUTTON_COLOR,
        text="Stop",
        font_size=26
    )
    flip_button = Button(
        rect=(button_x, button_y_start + 3 * button_spacing, button_width, button_height),
        color=BUTTON_COLOR,
        text="Flip Board",
        font_size=26
    )

def generate_game_record(board):
    """生成对局记录，格式为每步的标准代数记谱法（SAN）"""
    moves = board.move_stack
    move_list = []
    temp_board = chess.Board()
    for i, move in enumerate(moves):
        san_move = temp_board.san(move)
        if i % 2 == 0:
            move_list.append(f"{i // 2 + 1}. {san_move}")
        else:
            move_list[-1] += f" {san_move}"
        temp_board.push(move)
    return "\n".join(move_list)

def generate_board_diagram(board):
    """生成棋盘的 Markdown 表格表示，使用棋子符号"""
    board_matrix = []
    for rank in range(8, 0, -1):
        row = []
        for file in 'abcdefgh':
            square = chess.parse_square(f"{file}{rank}")
            piece = board.piece_at(square)
            symbol = piece.symbol() if piece else "."
            row.append(symbol)
        board_matrix.append(row)
    df = pd.DataFrame(board_matrix, index=range(8, 0, -1), columns=list('abcdefgh'))
    return df.to_markdown()

def generate_prompt_text(settings, board, attempt, tried_moves, player_color, additional_prompt, max_attempts):
    """生成 AI 或人类玩家的提示文本"""
    game_record = generate_game_record(board) if settings["provide_game_history"] else ""
    board_diagram = generate_board_diagram(board) if settings["provide_game_diagram"] else ""

    prompt_text = f"{settings['pre_content']}\n\n"

    if settings["provide_game_history"]:
        prompt_text += "Game History:\n"
        prompt_text += f"{game_record}\n\n" if game_record else "None, this is the first move.\n\n"

    if settings["provide_game_diagram"]:
        prompt_text += "Chessboard Diagram:\n"
        prompt_text += f"*Uppercase for White and lowercase for Black. You are {player_color}.*\n"
        prompt_text += f"{board_diagram}\n\n"

    if attempt > 1:
        prompt_text += f"Your previous move was illegal. Attempt {attempt}/{max_attempts}.\n"
        if attempt >= max_attempts/2:
            prompt_text += (
                "Please carefully reanalyze the proposed chess move step by step. **First, analyze why the previous move was deemed illegal. What specific rule or condition did it violate?** After clarifying this, proceed to determine a legal move. **Have you reviewed the board diagram carefully? Can you confirm which pieces on the board are yours? Which of your pieces are currently available and able to move?** Identify which piece you intend to move and confirm its current position with coordinates. **What is the piece and its exact location?** Then, ensure that its movement adheres to the legal rules for that piece. **Does the move comply with the movement rules of the identified piece?** Next, verify that the destination square is valid by specifying its coordinates and confirming whether it is unoccupied or appropriately capturable. **What is the destination square, and is it free or can it be captured?** Additionally, confirm that the move does not place or leave the player’s king in check. **Does this move affect the king’s safety in any way?** Please address all these questions thoroughly to ensure the move is valid.\n"
            )
            if additional_prompt:
                prompt_text += f"{additional_prompt}\n"
        else:
            prompt_text += "Please reconsider your move step by step based on the feedback.\n"
        if not settings["provide_chat_history"]:
            if CHAT_HISTORY[player_color]:
                last_user_message = CHAT_HISTORY[player_color][-2]['content'] if len(CHAT_HISTORY[player_color]) >= 2 else ""
                last_assistant_reply = CHAT_HISTORY[player_color][-1]['content'] if len(CHAT_HISTORY[player_color]) >= 1 else ""
                prompt_text += f"Previous interaction:\nUser: {last_user_message}\nAssistant: {last_assistant_reply}\n\n"

        if tried_moves:
            prompt_text += f"You have already tried: {', '.join(tried_moves)}\n"

    prompt_text += f"{settings['post_content']}\n"

    return prompt_text, game_record, board_diagram

def send_openai_request(settings, messages):
    """发送请求到 OpenAI API 并返回响应"""
    max_retries = 5
    retries = 0

    while True:
        try:
            response = openai.chat.completions.create(
                model=settings["model"],
                messages=messages,
                temperature=0.7,
            )
            # 检查回复是否为空或 None
            if response is None:
                raise ValueError("响应为 None")
            content = response.choices[0].message.content.strip()
            if not content:
                raise ValueError("响应为空")
            return response

        except openai.APIConnectionError as e:
            print("无法连接到服务器")
            print(e)
        except openai.RateLimitError as e:
            print("收到 429 状态码，已达到 API 速率限制，请稍后重试")
            print(e)
        except openai.APIError as e:
            print("API 请求出错")
            print(e)
        except (ValueError, AttributeError, IndexError) as e:
            print(f"错误：{e}")

        retries += 1
        if retries >= max_retries:
            print("已达到最大重试次数。")
            input("按 Enter 键继续重试...")
            retries = 0  # 重置重试计数
        else:
            print(f"发生错误，正在重试...({retries}/{max_retries})")

def extract_move_from_reply(reply, player_color):
    """从 AI 的回复中提取走法"""
    match = re.search(r'###\n([A-Za-z0-9 ]+)\n###', reply, re.DOTALL)
    if match:
        move_str = match.group(1).strip()
        return move_str
    else:
        print(f"{player_color.capitalize()} 没有提供正确格式的走法。")
        return None

def prompt_output(board, player_color, attempt=1, tried_moves=[], current_player_type='Human', stockfish=None, log_files=None, additional_prompt=None, gui_enabled=True, max_attempts=10):
    """生成并处理 AI、人类或 Stockfish 的走法"""
    settings = PLAYER_SETTINGS[player_color]
    current_player = "White" if board.turn else "Black"

    global is_paused, board_flipped  # 引入全局变量 is_paused 和 board_flipped

    if current_player_type == 'Human':
        print(f"\n===== {current_player} 的回合 =====")
        if gui_enabled:
            move_input = human_player_move_gui(board)
            if move_input is None:
                raise RestartGameException()
        else:
            move_input = human_player_move_cli(board)
        return move_input.strip(), False  # is_uci=False

    elif current_player_type == 'ChatGPT':
        prompt_text, _, _ = generate_prompt_text(
            settings, board, attempt, tried_moves, player_color, additional_prompt, max_attempts
        )

        # 构建与 OpenAI 的对话消息
        messages = [{"role": "system", "content": settings["system_prompt"]}]
        chat_count = len(CHAT_HISTORY[player_color])
        if settings["provide_chat_history"]:
            chat_history = CHAT_HISTORY[player_color][-20:] if chat_count > 20 else CHAT_HISTORY[player_color]
            messages.extend(chat_history)
        messages.append({"role": "user", "content": prompt_text})

        # 输出到终端
        print(f"\n===== {current_player} 的回合 (尝试 {attempt}/{max_attempts}) =====")
        print("发送到 OpenAI 的消息:")
        for message in messages:
            print(f"{message['role'].capitalize()}: {message['content']}")

        # 将 prompt 写入日志文件
        if log_files and log_files[player_color]:
            with open(log_files[player_color], 'a', encoding='utf-8') as f:
                f.write(f"\n===== Prompt (Attempt {attempt}/{max_attempts}) =====\n")
                f.write(str(messages) + '\n')

        # 使用线程来发送请求到 OpenAI API
        response = None

        def get_response():
            nonlocal response
            response = send_openai_request(settings, messages)

        thread = threading.Thread(target=get_response, daemon=True)
        thread.start()

        # 在等待响应期间，保持 GUI 响应
        while thread.is_alive():
            thread.join(timeout=0.1)
            # 处理 Pygame 事件
            if gui_enabled:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        x, y = event.pos
                        if restart_button.is_clicked((x, y)):
                            restart_game(board)
                        elif pause_button.is_clicked((x, y)):
                            is_paused = not is_paused
                            pause_button.update_text("Resume" if is_paused else "Pause")
                        elif stop_button.is_clicked((x, y)):
                            save_game(board, game_over_message='stopped')
                            pygame.quit()
                            sys.exit()
                        elif flip_button.is_clicked((x, y)):  # 检测Flip按钮点击
                            board_flipped = not board_flipped
                            print("棋盘已翻转。")
                    elif event.type == pygame.MOUSEBUTTONUP:
                        pass
                    elif event.type == pygame.MOUSEMOTION:
                        pass
                    elif event.type == pygame.MOUSEWHEEL:
                        handle_mouse_wheel(event)
                # 如果游戏暂停，则暂停线程
                if is_paused:
                    thread.join(timeout=0)  # 不再等待线程
                    while is_paused:
                        # 绘制棋盘并处理事件
                        draw_board(board)
                        pygame.display.flip()
                        CLOCK.tick(FPS)
                        for event in pygame.event.get():
                            if event.type == pygame.QUIT:
                                pygame.quit()
                                sys.exit()
                            elif event.type == pygame.MOUSEBUTTONDOWN:
                                x, y = event.pos
                                if pause_button.is_clicked((x, y)):
                                    is_paused = not is_paused
                                    pause_button.update_text("Resume" if is_paused else "Pause")
                                elif restart_button.is_clicked((x, y)):
                                    restart_game(board)
                                elif stop_button.is_clicked((x, y)):
                                    save_game(board, game_over_message='stopped')
                                    pygame.quit()
                                    sys.exit()
                                elif flip_button.is_clicked((x, y)):
                                    board_flipped = not board_flipped
                                    print("棋盘已翻转。")
                            elif event.type == pygame.MOUSEWHEEL:
                                handle_mouse_wheel(event)
                    # 重新启动线程
                    if not thread.is_alive():
                        thread = threading.Thread(target=get_response, daemon=True)
                        thread.start()
                else:
                    # 绘制棋盘
                    draw_board(board)
                    pygame.display.flip()
                    CLOCK.tick(FPS)

        if response is None:
            return None, False

        # 获取并显示 ChatGPT 的回复
        reply = response.choices[0].message.content.strip()
        print(f"\n{current_player} 的回复：")
        print(reply)

        # 将回复写入日志文件
        if log_files and log_files[player_color]:
            with open(log_files[player_color], 'a', encoding='utf-8') as f:
                f.write(f"\n===== Response =====\n")
                f.write(str(response) + '\n')

        # 更新聊天记录
        if settings["provide_chat_history"]:
            CHAT_HISTORY[player_color].append({"role": "user", "content": prompt_text})
            CHAT_HISTORY[player_color].append({"role": "assistant", "content": reply})

        # 从回复中提取走法
        move_str = extract_move_from_reply(reply, current_player)
        return move_str, False  # is_uci=False

    elif current_player_type == 'Stockfish':
        if stockfish is None:
            raise ValueError("Stockfish 引擎未初始化。")
        print(f"\n===== {current_player} 的回合 =====")

        # 使用线程来获取 Stockfish 的最佳走法
        move_str = None

        def get_stockfish_move():
            nonlocal move_str
            stockfish.set_fen_position(board.fen())
            move_str = stockfish.get_best_move()

        thread = threading.Thread(target=get_stockfish_move, daemon=True)
        thread.start()

        # 在等待 Stockfish 计算时，保持 GUI 响应
        while thread.is_alive():
            thread.join(timeout=0.1)
            if gui_enabled:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                    elif event.type == pygame.MOUSEBUTTONDOWN:
                        x, y = event.pos
                        if restart_button.is_clicked((x, y)):
                            restart_game(board)
                        elif pause_button.is_clicked((x, y)):
                            is_paused = not is_paused
                            pause_button.update_text("Resume" if is_paused else "Pause")
                        elif stop_button.is_clicked((x, y)):
                            save_game(board, game_over_message='stopped')
                            pygame.quit()
                            sys.exit()
                        elif flip_button.is_clicked((x, y)):  # 检测Flip按钮点击
                            board_flipped = not board_flipped
                            print("棋盘已翻转。")
                    elif event.type == pygame.MOUSEWHEEL:
                        handle_mouse_wheel(event)

                # 如果游戏暂停，则暂停线程
                if is_paused:
                    thread.join(timeout=0)  # 不再等待线程
                    while is_paused:
                        # 绘制棋盘并处理事件
                        draw_board(board)
                        pygame.display.flip()
                        CLOCK.tick(FPS)
                        for event in pygame.event.get():
                            if event.type == pygame.QUIT:
                                pygame.quit()
                                sys.exit()
                            elif event.type == pygame.MOUSEBUTTONDOWN:
                                x, y = event.pos
                                if pause_button.is_clicked((x, y)):
                                    is_paused = not is_paused
                                    pause_button.update_text("Resume" if is_paused else "Pause")
                                elif restart_button.is_clicked((x, y)):
                                    restart_game(board)
                                elif stop_button.is_clicked((x, y)):
                                    save_game(board, game_over_message='stopped')
                                    pygame.quit()
                                    sys.exit()
                                elif flip_button.is_clicked((x, y)):
                                    board_flipped = not board_flipped
                                    print("棋盘已翻转。")
                            elif event.type == pygame.MOUSEWHEEL:
                                handle_mouse_wheel(event)
                    # 重新启动线程
                    if not thread.is_alive():
                        thread = threading.Thread(target=get_stockfish_move, daemon=True)
                        thread.start()
                else:
                    draw_board(board)
                    pygame.display.flip()
                    CLOCK.tick(FPS)

        if move_str is None:
            print("无法从 Stockfish 获取走法。")
            return None, True  # is_uci=True

        print(f"Stockfish ({current_player}) 走: {move_str}")
        return move_str, True  # is_uci=True

    else:
        raise ValueError(f"未知的玩家类型：{current_player_type}")

def check_game_over(board):
    """检查游戏是否结束，并返回相应的消息"""
    if board.is_checkmate():
        winner = "White" if not board.turn else "Black"
        return f"{winner} wins by checkmate!"
    elif board.is_stalemate():
        return "The game ends in a stalemate."
    elif board.is_insufficient_material():
        return "Draw due to insufficient material."
    elif board.can_claim_threefold_repetition():
        return "Draw due to threefold repetition."
    elif board.can_claim_fifty_moves():
        return "Draw due to the fifty-move rule."
    else:
        return None

def human_player_move_cli(board):
    """处理人类玩家的命令行输入，返回标准代数记谱法的走法"""
    while True:
        move_input = input("请输入你的走法（例如 e2e4 或 Nf3）： ").strip()
        try:
            if re.match(r'^[a-h][1-8][a-h][1-8][qrbn]?$', move_input):
                move = chess.Move.from_uci(move_input)
            else:
                move = board.parse_san(move_input)
            if move in board.legal_moves:
                return board.san(move)
            else:
                print("非法走法，请重新输入。")
        except ValueError:
            print("输入格式错误，请重新输入。")

def human_player_move_gui(board):
    """处理人类玩家的鼠标事件，返回标准代数记谱法的走法（使用GUI）"""
    move_made = False
    dragging = False
    drag_piece = None
    from_square = None
    mouse_x, mouse_y = 0, 0

    global is_paused, board_flipped  # 引入全局变量 is_paused 和 board_flipped

    while not move_made:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                if restart_button.is_clicked((x, y)):
                    restart_game(board)
                elif pause_button.is_clicked((x, y)):
                    is_paused = not is_paused
                    pause_button.update_text("Resume" if is_paused else "Pause")
                elif stop_button.is_clicked((x, y)):
                    save_game(board, game_over_message='stopped')
                    pygame.quit()
                    sys.exit()
                elif flip_button.is_clicked((x, y)):  # 检测Flip按钮点击
                    board_flipped = not board_flipped
                    print("棋盘已翻转。")
                else:
                    if not is_paused:
                        if x >= board_x and x < board_x + SQUARE_SIZE*8 and y >= board_y and y < board_y + SQUARE_SIZE*8:
                            adjusted_x = x - board_x
                            adjusted_y = y - board_y
                            if board_flipped:
                                col = 7 - (adjusted_x // SQUARE_SIZE)
                                row = 7 - (adjusted_y // SQUARE_SIZE)
                            else:
                                col = adjusted_x // SQUARE_SIZE
                                row = adjusted_y // SQUARE_SIZE
                            from_square = chess.square(col, 7 - row)
                            piece = board.piece_at(from_square)
                            if piece and (
                                (piece.color == chess.WHITE and board.turn) or
                                (piece.color == chess.BLACK and not board.turn)
                            ):
                                dragging = True
                                drag_piece = piece
                                mouse_x, mouse_y = event.pos
            elif event.type == pygame.MOUSEMOTION and dragging and not is_paused:
                mouse_x, mouse_y = event.pos
            elif event.type == pygame.MOUSEBUTTONUP and dragging and not is_paused:
                x, y = event.pos
                if x >= board_x and x < board_x + SQUARE_SIZE*8 and y >= board_y and y < board_y + SQUARE_SIZE*8:
                    adjusted_x = x - board_x
                    adjusted_y = y - board_y
                    if board_flipped:
                        col = 7 - (adjusted_x // SQUARE_SIZE)
                        row = 7 - (adjusted_y // SQUARE_SIZE)
                    else:
                        col = adjusted_x // SQUARE_SIZE
                        row = adjusted_y // SQUARE_SIZE
                    to_square = chess.square(col, 7 - row)
                    move = chess.Move(from_square, to_square)
                    if chess.Move(from_square, to_square, promotion=chess.QUEEN) in board.legal_moves:
                        # 处理兵的升变
                        promotion = 'q'  # 为简化，直接升变为皇后
                        move = chess.Move(from_square, to_square, promotion=chess.QUEEN)
                    if move in board.legal_moves:
                        san_move = board.san(move)
                        move_made = True
                        return san_move
                    else:
                        print("非法走法，请重新选择。")
                else:
                    print("移动超出范围。")
                dragging = False
                drag_piece = None
            elif event.type == pygame.MOUSEWHEEL:
                handle_mouse_wheel(event)

        draw_board(board, dragging, drag_piece, mouse_x, mouse_y, from_square)
        pygame.display.flip()
        CLOCK.tick(FPS)
    return None

# 定义一个变量来跟踪游戏历史滚动位置
history_scroll = 0

def handle_mouse_wheel(event):
    """处理鼠标滚轮事件"""
    global history_scroll
    # 滚轮事件用于滚动游戏历史记录
    history_scroll += event.y * 20  # 每次滚动20像素
    # 限制滚动范围
    history_scroll = max(min(history_scroll, 0), -max(0, history_content_height - history_view_height))

def draw_board(board, dragging=False, drag_piece=None, mouse_x=0, mouse_y=0, from_square=None, game_over_message=None):
    """绘制棋盘和棋子（仅在启用GUI时调用）"""
    SCREEN.fill(BG_COLOR)
    # 绘制棋盘背景
    board_rect = pygame.Rect(board_x, board_y, SQUARE_SIZE*8, SQUARE_SIZE*8)
    pygame.draw.rect(SCREEN, PANEL_COLOR, board_rect)

    # 绘制棋盘格子
    for rank in range(8):
        for file in range(8):
            # 根据board_flipped状态调整绘制顺序
            if board_flipped:
                display_rank = 7 - rank
                display_file = 7 - file
            else:
                display_rank = rank
                display_file = file
            color = LIGHT_SQUARE_COLOR if (display_rank + display_file) % 2 == 0 else DARK_SQUARE_COLOR
            rect = pygame.Rect(board_x + display_file*SQUARE_SIZE, board_y + display_rank*SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE)
            pygame.draw.rect(SCREEN, color, rect)
            square = chess.square(file, 7 - rank)
            piece = board.piece_at(square)
            if piece:
                if dragging and square == from_square:
                    continue
                SCREEN.blit(PIECE_IMAGES[piece.symbol()], rect)
    if dragging and drag_piece:
        img = PIECE_IMAGES[drag_piece.symbol()]
        img_rect = img.get_rect(center=(mouse_x, mouse_y))
        SCREEN.blit(img, img_rect)

    # 绘制边框
    pygame.draw.rect(SCREEN, HIGHLIGHT_COLOR, board_rect, 2)

    # 绘制按钮区域背景
    sidebar_rect = pygame.Rect(800, 0, 300, SCREEN.get_height())
    pygame.draw.rect(SCREEN, PANEL_COLOR, sidebar_rect)

    # 绘制按钮
    mouse_pos = pygame.mouse.get_pos()
    for button in [restart_button, pause_button, stop_button, flip_button]:
        button.check_hover(mouse_pos)
        button.draw(SCREEN)

    # 绘制游戏历史记录
    draw_game_history(board)

    # 绘制状态栏
    status_bar_rect = pygame.Rect(0, SCREEN.get_height() - 40, SCREEN.get_width(), 40)
    pygame.draw.rect(SCREEN, PANEL_COLOR, status_bar_rect)
    font = pygame.font.SysFont("Arial", 24)
    if game_over_message:
        status_text = game_over_message
    else:
        current_player = "White" if board.turn else "Black"
        status_text = f"{current_player}'s turn"
    text_surface = font.render(status_text, True, TEXT_COLOR)
    text_rect = text_surface.get_rect(center=status_bar_rect.center)
    SCREEN.blit(text_surface, text_rect)

    if game_over_message:
        font = pygame.font.SysFont("Arial", 60)
        text_surface = font.render(game_over_message, True, TEXT_COLOR)
        text_rect = text_surface.get_rect(center=(SCREEN.get_width() // 2, SCREEN.get_height() // 2))
        overlay = pygame.Surface((text_rect.width + 40, text_rect.height + 40))
        overlay.set_alpha(180)
        overlay.fill(BLACK_COLOR)
        overlay_rect = overlay.get_rect(center=text_rect.center)
        SCREEN.blit(overlay, overlay_rect)
        SCREEN.blit(text_surface, text_rect)

# 定义棋盘的位置（调整y坐标，避免被状态栏遮挡）
board_x = 50
board_y = 30

# 定义游戏历史记录视图区域高度
history_view_height = 350
history_content_height = 0  # 游戏历史内容的总高度

def draw_game_history(board):
    """在屏幕右侧绘制游戏历史记录，并处理文本换行和滚动。"""
    global history_content_height
    game_history = generate_game_record(board)
    x = 820  # 游戏历史记录的起始 x 坐标
    y = 50   # 游戏历史记录的起始 y 坐标

    # 定义字体
    font = pygame.font.SysFont("Consolas", 20)
    max_width = SCREEN.get_width() - x - 30  # 留出一些边距

    # 创建一个新的表面来绘制游戏历史
    history_surface = pygame.Surface((max_width, 1000), pygame.SRCALPHA)
    history_surface.fill((0, 0, 0, 0))  # 全透明背景

    # 将游戏历史分割为多行
    lines = game_history.split('\n')
    content_y = 0
    for line in lines:
        # 检查文本宽度，处理换行
        words = line.split(' ')
        rendered_line = ''
        for word in words:
            test_line = rendered_line + word + ' '
            text_surface = font.render(test_line, True, TEXT_COLOR)
            if text_surface.get_width() > max_width:
                # 绘制当前行，并开始新行
                text_surface = font.render(rendered_line, True, TEXT_COLOR)
                history_surface.blit(text_surface, (0, content_y))
                content_y += 25
                rendered_line = word + ' '
            else:
                rendered_line = test_line
        # 绘制剩余的文本
        if rendered_line:
            text_surface = font.render(rendered_line, True, TEXT_COLOR)
            history_surface.blit(text_surface, (0, content_y))
            content_y += 25

    history_content_height = content_y  # 更新内容总高度

    # 定义显示区域的矩形
    clip_rect = pygame.Rect(0, -history_scroll, max_width, history_view_height)
    # 将历史记录表面绘制到屏幕上，应用剪辑
    SCREEN.blit(history_surface, (x + 10, y), area=clip_rect)

    # 绘制滚动条（可选）
    if history_content_height > history_view_height:
        scrollbar_height = history_view_height * history_view_height / history_content_height
        scrollbar_y = y + (-history_scroll) * history_view_height / history_content_height
        scrollbar_rect = pygame.Rect(x + max_width + 15, scrollbar_y, 10, scrollbar_height)
        pygame.draw.rect(SCREEN, HIGHLIGHT_COLOR, scrollbar_rect)

def select_player_types_gui():
    """使用GUI界面让用户选择白方和黑方的玩家类型"""
    global white_player_type, black_player_type

    player_types = ['Human', 'ChatGPT', 'Stockfish']
    font = pygame.font.SysFont("Arial", 30)
    big_font = pygame.font.SysFont("Arial", 50)

    button_width = 200
    button_height = 50
    white_buttons = []
    black_buttons = []

    screen_center_x = SCREEN.get_width() // 2

    for i, player_type in enumerate(player_types):
        white_rect = pygame.Rect(screen_center_x - 250, 200 + i * (button_height + 20), button_width, button_height)
        white_buttons.append((white_rect, player_type))
        black_rect = pygame.Rect(screen_center_x + 50, 200 + i * (button_height + 20), button_width, button_height)
        black_buttons.append((black_rect, player_type))

    start_button_rect = pygame.Rect(screen_center_x - 100, 450, 200, 60)
    selecting = True

    while selecting:
        SCREEN.fill(BG_COLOR)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                x, y = event.pos
                for rect, player_type in white_buttons:
                    if rect.collidepoint(x, y):
                        white_player_type = player_type
                for rect, player_type in black_buttons:
                    if rect.collidepoint(x, y):
                        black_player_type = player_type
                if white_player_type and black_player_type and start_button_rect.collidepoint(x, y):
                    selecting = False

        title_text = big_font.render("Select Player Types", True, TEXT_COLOR)
        title_rect = title_text.get_rect(center=(screen_center_x, 80))
        SCREEN.blit(title_text, title_rect)

        white_title = font.render("White", True, TEXT_COLOR)
        white_title_rect = white_title.get_rect(center=(screen_center_x - 150, 160))
        SCREEN.blit(white_title, white_title_rect)

        black_title = font.render("Black", True, TEXT_COLOR)
        black_title_rect = black_title.get_rect(center=(screen_center_x + 150, 160))
        SCREEN.blit(black_title, black_title_rect)

        mouse_pos = pygame.mouse.get_pos()
        for rect, player_type in white_buttons:
            is_selected = white_player_type == player_type
            color = BUTTON_HOVER_COLOR if rect.collidepoint(mouse_pos) else BUTTON_COLOR
            pygame.draw.rect(SCREEN, color if not is_selected else HIGHLIGHT_COLOR, rect, border_radius=10)
            text_surface = font.render(player_type, True, TEXT_COLOR)
            text_rect = text_surface.get_rect(center=rect.center)
            SCREEN.blit(text_surface, text_rect)

        for rect, player_type in black_buttons:
            is_selected = black_player_type == player_type
            color = BUTTON_HOVER_COLOR if rect.collidepoint(mouse_pos) else BUTTON_COLOR
            pygame.draw.rect(SCREEN, color if not is_selected else HIGHLIGHT_COLOR, rect, border_radius=10)
            text_surface = font.render(player_type, True, TEXT_COLOR)
            text_rect = text_surface.get_rect(center=rect.center)
            SCREEN.blit(text_surface, text_rect)

        if white_player_type and black_player_type:
            color = BUTTON_HOVER_COLOR if start_button_rect.collidepoint(mouse_pos) else BUTTON_COLOR
            pygame.draw.rect(SCREEN, color, start_button_rect, border_radius=10)
            start_text = font.render("Start Game", True, TEXT_COLOR)
            start_text_rect = start_text.get_rect(center=start_button_rect.center)
            SCREEN.blit(start_text, start_text_rect)

        pygame.display.flip()
        CLOCK.tick(FPS)

def restart_game(board):
    """保存当前游戏记录并重启游戏"""
    print("正在重新开始游戏...")
    # 使用全局的 timestamp
    global timestamp
    # 保存当前棋局，game_over_message 为 'restart'
    save_game(board, game_over_message='restart')
    # 在保存后，生成新的 timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    pygame.quit()
    raise RestartGameException()

def save_game(board, game_over_message):
    """保存当前棋局到文件"""
    white_player_name = white_player_type
    black_player_name = black_player_type
    # 将 game_over_message 中的空格和特殊字符替换为下划线
    sanitized_message = re.sub(r'\s+', '_', game_over_message)
    sanitized_message = re.sub(r'[^\w\-]', '', sanitized_message)
    game_record_file = f'{white_player_name}_vs_{black_player_name}_{sanitized_message}_{timestamp}.txt'
    final_board_diagram = generate_board_diagram(board)
    game_record = generate_game_record(board)
    with open(game_record_file, 'w', encoding='utf-8') as f:
        if game_over_message == 'restart':
            f.write("当前棋局（重新开始前）：\n")
        else:
            f.write("最终棋局：\n")
        f.write(final_board_diagram + '\n')
        f.write("\n对局记录：\n")
        f.write(game_record + '\n')
    print(f"游戏记录已保存到 {game_record_file}")

def get_additional_prompt():
    """使用 tkinter simpledialog 获取附加提示"""
    global additional_prompt
    
    # 创建隐藏的 root 窗口
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    
    # 将对话框放在pygame窗口前面
    root.attributes('-topmost', True)
    
    # 弹出输入对话框
    result = simpledialog.askstring(
        "Additional Prompt", 
        "\tChatGPT did not provide legal moves within the move limit,\t\n\tso you can input an additional prompt to guide ChatGPT:\t",
        parent=root
    )
    
    # 清理 tk 窗口
    root.destroy()
    
    # 更新全局变量
    additional_prompt = result if result else ""

    return additional_prompt

def main():
    """主函数，负责游戏流程控制"""
    global ENABLE_GUI, SQUARE_SIZE, white_player_type, black_player_type, timestamp, is_paused, board_flipped, additional_prompt
    first_game = True

    while True:
        try:
            if first_game:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                log_files = {
                    'white': f'white_{timestamp}.txt',
                    'black': f'black_{timestamp}.txt'
                }
                player_types_dict = {
                    '1': 'Human',
                    '2': 'ChatGPT',
                    '3': 'Stockfish',
                }
                while True:
                    gui_choice = input("是否启用GUI？(y/n): ").strip().lower()
                    if gui_choice in ['y', 'yes']:
                        ENABLE_GUI = True
                        break
                    elif gui_choice in ['n', 'no']:
                        ENABLE_GUI = False
                        break
                    else:
                        print("无效输入，请输入 'y' 或 'n'。")

                if ENABLE_GUI:
                    initialize_gui()
                    select_player_types_gui()
                else:
                    print("GUI已禁用，游戏将在命令行中进行。")
                    print("\n请选择白方的玩家类型：")
                    for key, value in player_types_dict.items():
                        print(f"{key}) {value}")
                    white_choice = input("请输入选项编号：").strip()
                    while white_choice not in player_types_dict.keys():
                        white_choice = input("无效选择，请重新输入：").strip()
                    white_player_type = player_types_dict[white_choice]
                    print("请选择黑方的玩家类型：")
                    for key, value in player_types_dict.items():
                        print(f"{key}) {value}")
                    black_choice = input("请输入选项编号：").strip()
                    while black_choice not in player_types_dict.keys():
                        black_choice = input("无效选择，请重新输入：").strip()
                    black_player_type = player_types_dict[black_choice]

                stockfish = None
                if 'Stockfish' in (white_player_type, black_player_type):
                    stockfish = Stockfish(
                        path=STOCKFISH_PATH,
                        parameters={"Hash": 32, "Threads": 2, "Minimum Thinking Time": 500}
                    )
                    stockfish.set_depth(20)
                board = chess.Board()
                game_over = False
                first_game = False

            else:
                # 重启游戏时，生成新的时间戳
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                log_files = {
                    'white': f'white_{timestamp}.txt',
                    'black': f'black_{timestamp}.txt'
                }
                if ENABLE_GUI:
                    initialize_gui()
                    select_player_types_gui()
                else:
                    # 命令行模式下重新选择玩家类型（可选）
                    pass

                stockfish = None
                if 'Stockfish' in (white_player_type, black_player_type):
                    stockfish = Stockfish(
                        path=STOCKFISH_PATH,
                        parameters={"Hash": 32, "Threads": 2, "Minimum Thinking Time": 300}
                    )
                    stockfish.set_depth(20)
                board = chess.Board()
                game_over = False
                is_paused = False  # 重置暂停状态

            while not game_over:
                player_color = 'white' if board.turn else 'black'
                attempt = 1
                max_attempts = 10
                tried_moves = []
                additional_prompt = None
                current_player_type = white_player_type if board.turn else black_player_type
                move_made = False

                while not move_made:
                    move_str, is_uci = prompt_output(
                        board,
                        player_color,
                        attempt,
                        tried_moves,
                        current_player_type,
                        stockfish,
                        log_files,
                        additional_prompt,
                        ENABLE_GUI,
                        max_attempts
                    )
                    if move_str:
                        try:
                            if is_uci:
                                move = chess.Move.from_uci(move_str)
                                if move in board.legal_moves:
                                    board.push(move)
                                    move_made = True
                                else:
                                    raise ValueError(f"非法走法：{move_str}")
                            else:
                                move = board.parse_san(move_str)
                                board.push(move)
                                move_made = True
                            print(f"\n{player_color.capitalize()} 走: {move_str}\n")
                        except ValueError as e:
                            print(f"错误：{e}")
                            tried_moves.append(move_str)
                    else:
                        tried_moves.append("No valid move provided")

                    if move_made:
                        break

                    attempt += 1
                    if attempt > max_attempts:
                        print(f"{player_color.capitalize()} 已连续 {max_attempts} 次未能提供合法走法。")
                        if current_player_type == 'ChatGPT':
                            if ENABLE_GUI:
                                # 创建获取输入的线程
                                
                                additional_prompt = None
                                input_thread = threading.Thread(target=get_additional_prompt, daemon=True)
                                input_thread.start()
                                
                                # 等待输入的同时保持GUI响应
                                while input_thread.is_alive():
                                    for event in pygame.event.get():
                                        if event.type == pygame.QUIT:
                                            pygame.quit()
                                            sys.exit()
                                        elif event.type == pygame.MOUSEBUTTONDOWN:
                                            x, y = event.pos
                                            if restart_button.is_clicked((x, y)):
                                                restart_game(board)
                                            elif pause_button.is_clicked((x, y)):
                                                is_paused = not is_paused
                                                pause_button.update_text("Resume" if is_paused else "Pause")
                                            elif stop_button.is_clicked((x, y)):
                                                save_game(board, game_over_message='stopped')
                                                pygame.quit()
                                                sys.exit()
                                            elif flip_button.is_clicked((x, y)):
                                                board_flipped = not board_flipped
                                                print("棋盘已翻转。")
                                        elif event.type == pygame.MOUSEWHEEL:
                                            handle_mouse_wheel(event)
                                    
                                    # 绘制棋盘
                                    draw_board(board)                                    
                                    pygame.display.flip()
                                    CLOCK.tick(FPS)
                                
                                print(f"已发送附加提示给 {player_color.capitalize()}。继续尝试提供合法走法。")
                            else:
                                # 命令行模式下直接获取输入
                                additional_prompt = input("请输入附加的提示信息以继续游戏：").strip()
                                print(f"已发送附加提示给 {player_color.capitalize()}。继续尝试提供合法走法。")
                        else:
                            print(f"游戏终止。")
                            game_over = True
                            break

                if not move_made:
                    break

                game_over_message = check_game_over(board)
                if game_over_message:
                    print(game_over_message)
                    game_over = True

                if ENABLE_GUI:
                    draw_board(board)
                    pygame.display.flip()
                    CLOCK.tick(FPS)

            if game_over:
                print("\n游戏结束。")
                # 游戏正常结束后，保存棋局
                save_game(board, game_over_message=game_over_message or 'Game Over')
                if ENABLE_GUI:
                    while True:
                        for event in pygame.event.get():
                            if event.type == pygame.QUIT:
                                pygame.quit()
                                sys.exit()
                            elif event.type == pygame.MOUSEBUTTONDOWN:
                                x, y = event.pos
                                if restart_button.is_clicked((x, y)):
                                    # 游戏结束后重启，生成新的时间戳
                                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                                    pygame.quit()
                                    raise RestartGameException()
                                elif stop_button.is_clicked((x, y)):
                                    pygame.quit()
                                    sys.exit()
                                elif flip_button.is_clicked((x, y)):
                                    board_flipped = not board_flipped
                                    print("棋盘已翻转。")
                            elif event.type == pygame.MOUSEWHEEL:
                                handle_mouse_wheel(event)
                        draw_board(board, game_over_message=game_over_message)
                        pygame.display.flip()
                        CLOCK.tick(FPS)
                else:
                    input("按 Enter 键退出...")
                    break

        except RestartGameException:
            print("游戏正在重新启动...")
            continue
        except KeyboardInterrupt:
            print("\n游戏被用户中断。")
            if ENABLE_GUI:
                pygame.quit()
            sys.exit()

if __name__ == "__main__":
    main()
