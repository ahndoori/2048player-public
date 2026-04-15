import numpy as np
import copy
from dotenv import load_dotenv

class algorithm:
    def __init__(self):
        self.move_map = {0: 'up', 1: 'down', 2: 'left', 3: 'right'}

    def get_best_move(self, board):
        best_score, best_move = -float('inf'), None
        for m_idx in range(4):
            new_board, moved = self.simulate_move(board, m_idx)
            if moved:
                score = self.expectimax(new_board, 3, False)
                if score > best_score:
                    best_score, best_move = score, self.move_map[m_idx]
        return best_move

    def expectimax(self, board, depth, is_max):
        if depth == 0: return self.evaluate(board)
        if is_max:
            res = -float('inf')
            for m in range(4):
                nb, moved = self.simulate_move(board, m)
                if moved: res = max(res, self.expectimax(nb, depth-1, False))
            return res if res != -float('inf') else self.evaluate(board)
        else:
            res, empty = 0, [(r, c) for r in range(4) for c in range(4) if board[r][c] == 0]
            if not empty: return self.evaluate(board)
            for r, c in empty:
                for v, p in [(2, 0.9), (4, 0.1)]:
                    board[r][c] = v
                    res += p * self.expectimax(board, depth-1, True)
                    board[r][c] = 0
            return res / len(empty)

    def evaluate(self, board):
        weights = np.array([ # Snake 가중치 배치
            [1000, 500, 250, 125], 
            [10, 25, 50, 100], 
            [5, 3, 2, 1], 
            [0, 0, 0, 0]
        ])
        return np.sum(board * weights) + (np.count_nonzero(board == 0) * 150)

    def simulate_move(self, board, direction):
        nb = copy.deepcopy(board)
        # rot90의 k값 (0: left, 1: up, 2: right, 3: down 순으로 회전)
        rot_map = {0: 1, 1: 3, 2: 0, 3: 2}
        rot = rot_map[direction]
        rotated = np.rot90(nb, rot)
        final, moved = self._merge(rotated)
        return np.rot90(final, -rot), moved

    def _merge(self, board):
        new_b = np.zeros((4, 4), dtype=int)
        moved = False
        for i in range(4):
            row = [x for x in board[i] if x != 0]
            m_row = []
            skip = False
            for j in range(len(row)):
                if skip:
                    skip = False
                    continue
                if j+1 < len(row) and row[j] == row[j+1]:
                    m_row.append(row[j] * 2)
                    skip = True
                    moved = True
                else:
                    m_row.append(row[j])
            new_b[i, :len(m_row)] = m_row

        if not moved and not np.array_equal(board, new_b):
            moved = True
        return new_b, moved