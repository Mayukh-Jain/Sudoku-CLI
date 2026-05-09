#!/usr/bin/env python3
"""
CLI Sudoku Game
Navigate with arrow keys or WASD, enter digits 1-9, press 0 or Space to clear.
"""

import copy
import random
import time
import sys
import os

# ── Terminal control ──────────────────────────────────────────────────────────

def _getch_unix():
    import tty, termios
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        if ch == '\x1b':
            ch2 = sys.stdin.read(1)
            if ch2 == '[':
                ch3 = sys.stdin.read(1)
                return '\x1b[' + ch3
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)

def _getch_win():
    import msvcrt
    ch = msvcrt.getwch()
    if ch in ('\x00', '\xe0'):
        ch2 = msvcrt.getwch()
        mapping = {'H': '\x1b[A', 'P': '\x1b[B', 'M': '\x1b[C', 'K': '\x1b[D'}
        return mapping.get(ch2, '')
    return ch

getch = _getch_win if sys.platform == 'win32' else _getch_unix

def clear():
    os.system('cls' if sys.platform == 'win32' else 'clear')

# ── ANSI colours ──────────────────────────────────────────────────────────────

RESET   = '\033[0m'
BOLD    = '\033[1m'
DIM     = '\033[2m'
RED     = '\033[91m'
GREEN   = '\033[92m'
YELLOW  = '\033[93m'
CYAN    = '\033[96m'
WHITE   = '\033[97m'
BG_BLUE = '\033[44m'
BG_GRAY = '\033[100m'

# ── Sudoku logic ──────────────────────────────────────────────────────────────

def is_valid(board, row, col, num):
    if num in board[row]:
        return False
    if num in [board[r][col] for r in range(9)]:
        return False
    br, bc = (row // 3) * 3, (col // 3) * 3
    for r in range(br, br + 3):
        for c in range(bc, bc + 3):
            if board[r][c] == num:
                return False
    return True

def solve(board):
    for row in range(9):
        for col in range(9):
            if board[row][col] == 0:
                nums = list(range(1, 10))
                random.shuffle(nums)
                for num in nums:
                    if is_valid(board, row, col, num):
                        board[row][col] = num
                        if solve(board):
                            return True
                        board[row][col] = 0
                return False
    return True

def generate_puzzle(difficulty):
    """Generate a solved board then remove cells based on difficulty."""
    board = [[0] * 9 for _ in range(9)]
    solve(board)
    solution = copy.deepcopy(board)

    removals = {'easy': 36, 'medium': 46, 'hard': 54}
    count = removals.get(difficulty, 46)

    cells = [(r, c) for r in range(9) for c in range(9)]
    random.shuffle(cells)
    for r, c in cells[:count]:
        board[r][c] = 0

    return board, solution

# ── Rendering ─────────────────────────────────────────────────────────────────

# Box-border colour (bright cyan, bold) vs thin-border colour (dim)
BB  = f'{BOLD}{CYAN}'   # box border style
TB  = f'{DIM}'          # thin border style

# Pre-coloured horizontal rules
# Each rule is built from coloured segments so box lines stand out clearly.
def _hline(left, mid_thin, mid_box, right, fill_thin, fill_box):
    """Build a coloured horizontal line with distinct box vs thin separators."""
    segs = [BB + left + RESET]
    for c in range(9):
        fill = BB + fill_box + RESET if c % 3 == 0 and c > 0 else TB + fill_thin + RESET
        # cell fill (3 chars wide)
        if c % 3 == 0 and c > 0:
            segs.append(BB + fill_box * 3 + RESET)
        else:
            segs.append(TB + fill_thin * 3 + RESET)
        # right separator
        if c == 8:
            segs.append(BB + right + RESET)
        elif c % 3 == 2:
            segs.append(BB + mid_box + RESET)
        else:
            segs.append(TB + mid_thin + RESET)
    return ''.join(segs)

HORIZ_TOP = _hline('╔', '─', '╦', '╗', '═', '═')
HORIZ_MID = _hline('╟', '─', '╫', '╢', '─', '─')
HORIZ_BOX = _hline('╠', '═', '╬', '╣', '═', '═')
HORIZ_BOT = _hline('╚', '─', '╩', '╝', '═', '═')

def _vsep(c):
    """Vertical separator after column c (0-indexed)."""
    if c == 8:
        return BB + '║' + RESET
    elif c % 3 == 2:
        return BB + '║' + RESET
    else:
        return TB + '│' + RESET

def render(board, fixed, errors, cursor, notes, elapsed):
    cr, cc = cursor
    lines = []

    # Header
    lines.append(f"\n  {BB}╔═════════════════════╗{RESET}")
    lines.append(f"  {BB}║   SUDOKU  CLI  🎯   ║{RESET}")
    lines.append(f"  {BB}╚═════════════════════╝{RESET}\n")

    # Column header — aligned to match cell width (3 chars each + 1 sep)
    hdr = '    '
    for c in range(9):
        hdr += f' {YELLOW}{c+1}{RESET} '
        if c < 8:
            hdr += ' '   # matches separator width
    lines.append(hdr)
    lines.append('  ' + HORIZ_TOP)

    for r in range(9):
        if r > 0:
            lines.append('  ' + (HORIZ_BOX if r % 3 == 0 else HORIZ_MID))

        row_str = BB + '║' + RESET
        for c in range(9):
            val      = board[r][c]
            is_cur   = (r == cr and c == cc)
            is_fixed = fixed[r][c]
            is_error = (r, c) in errors

            if val == 0:
                cell = '   '
            elif is_fixed:
                cell = f' {BOLD}{WHITE}{val}{RESET} '
            elif is_error:
                cell = f' {BOLD}{RED}{val}{RESET} '
            else:
                cell = f' {GREEN}{val}{RESET} '

            if is_cur:
                # Strip existing colour codes inside cell for clean highlight
                digit = str(val) if val else ' '
                cell  = f'{BG_BLUE}{BOLD} {digit} {RESET}'

            row_str += cell + _vsep(c)

        lines.append(f'{YELLOW}{r+1}{RESET} ' + row_str)

    lines.append('  ' + HORIZ_BOT)

    # Status bar
    m, s = divmod(int(elapsed), 60)
    h, m = divmod(m, 60)
    timer = f'{h:02d}:{m:02d}:{s:02d}' if h else f'{m:02d}:{s:02d}'

    err_count = len(errors)
    err_color = RED if err_count else GREEN
    lines.append(f'\n  ⏱  {CYAN}{timer}{RESET}   ✖ Errors: {err_color}{err_count}{RESET}\n')

    # Controls
    lines.append(f'  {DIM}Move : ↑ ↓ ← →  or  W A S D{RESET}')
    lines.append(f'  {DIM}Place: 1-9     Clear: 0 / Space{RESET}')
    lines.append(f'  {DIM}Hint : H       New game: N   Quit: Q{RESET}\n')

    clear()
    print('\n'.join(lines))

# ── Game loop ─────────────────────────────────────────────────────────────────

def check_errors(board, solution):
    errors = set()
    for r in range(9):
        for c in range(9):
            if board[r][c] != 0 and board[r][c] != solution[r][c]:
                errors.add((r, c))
    return errors

def is_complete(board, solution):
    return all(
        board[r][c] == solution[r][c]
        for r in range(9) for c in range(9)
    )

def choose_difficulty():
    clear()
    print(f"\n  {BOLD}{CYAN}╔═════════════════════╗{RESET}")
    print(f"  {BOLD}{CYAN}║  Choose Difficulty  ║{RESET}")
    print(f"  {BOLD}{CYAN}╚═════════════════════╝{RESET}\n")
    print(f"  {WHITE}[1]{RESET} Easy")
    print(f"  {WHITE}[2]{RESET} Medium")
    print(f"  {WHITE}[3]{RESET} Hard\n")
    while True:
        ch = getch()
        if ch == '1': return 'easy'
        if ch == '2': return 'medium'
        if ch == '3': return 'hard'

def play():
    while True:
        difficulty = choose_difficulty()
        print(f"\n  {YELLOW}Generating puzzle…{RESET}")
        board, solution = generate_puzzle(difficulty)
        fixed = [[board[r][c] != 0 for c in range(9)] for r in range(9)]
        notes = [[set() for _ in range(9)] for _ in range(9)]

        cursor = [0, 0]
        start  = time.time()
        errors = set()

        while True:
            elapsed = time.time() - start
            errors = check_errors(board, solution)
            render(board, fixed, errors, cursor, notes, elapsed)

            if is_complete(board, solution):
                elapsed = time.time() - start
                m, s = divmod(int(elapsed), 60)
                clear()
                print(f"\n\n  {BOLD}{GREEN}🎉  Puzzle Solved!  🎉{RESET}")
                print(f"  Time: {m:02d}:{s:02d}  |  Difficulty: {difficulty.capitalize()}\n")
                print(f"  Press {WHITE}N{RESET} for a new game or {WHITE}Q{RESET} to quit.\n")
                while True:
                    ch = getch().lower()
                    if ch == 'n': break
                    if ch in ('q', '\x03'): sys.exit(0)
                break

            ch = getch()

            # Movement
            if ch in ('\x1b[A', 'w', 'W') and cursor[0] > 0:
                cursor[0] -= 1
            elif ch in ('\x1b[B', 's', 'S') and cursor[0] < 8:
                cursor[0] += 1
            elif ch in ('\x1b[D', 'a', 'A') and cursor[1] > 0:
                cursor[1] -= 1
            elif ch in ('\x1b[C', 'd', 'D') and cursor[1] < 8:
                cursor[1] += 1

            # Digit input
            elif ch in '123456789':
                r, c = cursor
                if not fixed[r][c]:
                    board[r][c] = int(ch)

            # Clear cell
            elif ch in ('0', ' '):
                r, c = cursor
                if not fixed[r][c]:
                    board[r][c] = 0

            # Hint – reveal cursor cell
            elif ch in ('h', 'H'):
                r, c = cursor
                if not fixed[r][c]:
                    board[r][c] = solution[r][c]
                    fixed[r][c] = True

            # New game
            elif ch in ('n', 'N'):
                break

            # Quit
            elif ch in ('q', 'Q', '\x03'):
                clear()
                print(f"\n  {CYAN}Thanks for playing!{RESET}\n")
                sys.exit(0)

if __name__ == '__main__':
    try:
        play()
    except KeyboardInterrupt:
        clear()
        print(f"\n  {CYAN}Thanks for playing!{RESET}\n")