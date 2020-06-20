# -*- coding: UTF-8 -*-
import threading, queue, socket, random, time, json


from dots_and_boxes.core.player import AIPlayer

from dots_and_boxes.core.model import *
from queue import PriorityQueue as PQ
from random import choice

lock = threading.Lock()
class MCTS(AIPlayer):
    def __init__(self, color, name, game_controller):
        super(MCTS, self).__init__(color, name, game_controller)
        self._game_controller = game_controller
        # self.ser_ip = ser_ip
        # self.ser_port = ser_port
        self.move_queue = None
        # self.socket = None
        self.turn = 0

        self.timeout = 10
        self.algorithm = "AI-MCTS"

    def start_new_game(self):
        self.move_queue = PQ()
        self.turn = 0


    def game_is_over(self, is_win):
        # 获得比赛结果
        print("You win!" if is_win else "You lose.")

    def last_move(self, piece, board, history, next_player_color):
        self._board = board
        self._history = history
        self._last_piece = piece
        self.turn = 0
        if len(history) <= 1:
            self.turn = len(history)
        else:
            for i in range(1, len(history)):
                if history[i].color != history[i-1].color:
                    self.turn = self.turn + 1
            if next_player_color != history[-1].color:
                    self.turn = self.turn + 1

        if (next_player_color == self.color):
            # self.move()
            self.__thread = threading.Thread(target=self.move)
            self.__thread.start()
            time.sleep(0.1)


    def move(self):
        # 若队列不为空，则先判断队列中的元素是否符合要求
        if not self.move_queue.empty():
            move = self.move_queue.get()[-1]
            p = Piece(self.color, move)
            if self._board.get_repeat(p):
                self._set_piece(move)
                super(MCTS, self).move(move)
                return

        R, B = {}, {}
        pieces = self._board.pieces
        # Box belong stats
        # 左上角为起始零点，先行后列，从0编号，编号即为左移位数
        R['box'], B['box'] = 0, 0
        for i in range(5):
            for j in range(5):
                if pieces[i*2+1][j*2+1] != 0:
                    c = (pieces[i*2+1][j*2+1])[0]
                    if c == Color.red:
                        R['box'] |= (1 << (i * 5 + j))
                    elif c == Color.blue:
                        B['box'] |= (1 << (i * 5 + j))
        # Edge belong stats
        # 左上角为起始零点，先行后列，从0编号，编号即为左移位数
        R['H'], R['V'], B['H'], B['V'] = 0, 0, 0, 0
        for i in range(6):
            for j in range(5):
                if pieces[i*2][j*2+1] != 0:
                    c = pieces[i*2][j*2+1].color
                    if c == Color.red:
                        R['H'] |= (1 << (i * 5 + j))
                    elif c == Color.blue:
                        B['H'] |= (1 << (i * 5 + j))
        for i in range(5):
            for j in range(6):
                if pieces[i*2+1][j*2] != 0:
                    c = pieces[i*2+1][j*2].color
                    if c == Color.red:
                        R['V'] |= (1 << (i * 6 + j))
                    elif c == Color.blue:
                        B['V'] |= (1 << (i * 6 + j))
        # As the reason mentioned above, may need a switch.
        if self.color == Color.red:
            R, B = B, R
            s1 = self._game_controller.red_player.score
            s0 = self._game_controller.blue_player.score
            now = 0
        else:
            s0 = self._game_controller.red_player.score
            s1 = self._game_controller.blue_player.score
            now = 1

        # 一共60种落子法，将全部落子法放在moves里
        moves = []
        for i in range(2):
            for n in range(30):
                moves.append(self._num2move(((1 << n) | (i << 31))))

        flag = 0
        lock.acquire()
        while True:

            if flag == 0:
                i = 1
                for m in moves:
                    # 如果全部落子后没有封闭的格子，则退出循坏
                    if i == len(moves)-1:
                        break
                    p = Piece(self.color, m)
                    if self._board.get_repeat(p):
                        # 设置棋子
                        self._board.set_piece(p)
                        x, y = p.coordinate
                        # print((x,y))
                        # 判断周围是否存在封闭的格子
                        if (self._check_box((x-1, y)) or self._check_box((x+1, y)) or self._check_box((x, y-1)) or self._check_box((x, y+1))):
                            self.move_queue.queue.clear()
                            self.move_queue.put((1,m))
                            self._board.unset_piece(p)
                            # print("aaaaa====", m)
                            # moves.remove(m)
                            # 如果有符合条件的则调出循坏
                            flag = 1

                            break
                        else:
                            self._board.unset_piece(p)
                            flag = 0
                            i = i + 1

            # 没有可以成为封闭的格子
            for random_m in moves:
                p = Piece(self.color, random_m)
                if self._board.get_repeat(p):
                    # 随机选择一个棋子
                    self.move_queue.put((2, random_m))
                    break
            break

        lock.release()

        rank,value = self.move_queue.get()
        self._set_piece(value)
        # print("rank and value is ", rank, value)

        super(MCTS, self).move(value)

        # if len(moves) > 1:
        #     for m in moves:
        #         p = Piece(self.color, m)
        #         # 不重复
        #         if self._board.get_repeat(p):
        #             # 设置棋子
        #             self._board.set_piece(p)
        #             x, y = p.coordinate
        #             # print((x,y))
        #             # 判断周围是否存在封闭的格子
        #             if (self._check_box((x-1, y)) or self._check_box((x+1, y)) or self._check_box((x, y-1)) or self._check_box((x, y+1))):
        #                 self.move_queue.put((1,m))
        #                 moves.remove(m)
        #                 break
        #             else:
        #                  self._board.unset_piece(p)
        #                  # self.move_queue.put((2,m))
        #                  # break
        # if self.move_queue.empty:
        #     random_m = choice(moves)
        #     p = Piece(self.color, random_m)
        #     if self._board.get_repeat(p):
        #         self.move_queue.put((2, random_m))
        #         moves.remove(random_m)

        # self.move_queue.put((2,moves[0]))

    def _set_piece(self, move):
        p = Piece(self.color, move)
        if self._board.get_repeat(p):
            self._board.set_piece(p)



    def _num2move(self, value):
        y, x = -1, -1
        if (value & (1 << 31)) != 0:
            type = "h"
        else:
            type = "v"
        for i in range(5)[::1]:
            for j in range(6)[::1]:
                if (value & 1) == 1:
                    if type == "h":
                        y, x = j, i
                    else:
                        y, x = i, j
                    break
                value >>= 1
            if y != -1:
                break

        if type == "h":
            y = str(6 - y)
            x = "abcde"[x]
        else:
            y = str(5 - y)
            x = "abcdef"[x]
        return (x, y, type)

    def _check_box(self, box_coordinate):  # 判断格子是否封闭
        x = box_coordinate[0]
        y = box_coordinate[1]

        if (x < 0 or x > 10 or y < 0 or y > 10):  # 判断坐标是否越界，如果越界直接返回否
            return False
        if (self._board.pieces[x][y] == -1):  # 判断坐标是否为点，如果是点直接返回否
            return False

        if (self._board.pieces[x-1][y] == 0
            or self._board.pieces[x+1][y] == 0
            or self._board.pieces[x][y-1] == 0
            or self._board.pieces[x][y+1] == 0):
            return False

        return True


