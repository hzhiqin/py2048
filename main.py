# -*- coding:utf-8 -*-
from random import randrange, choice


class Tools:
    actions = ["up", "down", "left", "right", "restart", "exit"]
    press = [ord(c) for c in "WSADGTwsadgt"]  # caps lock
    actions_dict = dict(zip(press, actions * 2))

    @staticmethod
    def transpose(field):
        return [list(row) for row in zip(*field)]

    @staticmethod
    def invert(field):
        return [row[::-1] for row in field]

    @classmethod
    def get_user_action(cls, screen):
        char = " "
        while char not in cls.actions_dict:
            char = screen.getch()  # block for input
        return cls.actions_dict[char]


class Model2048:

    def __init__(self, hi=4, wid=4, win=2048):
        self.height = hi
        self.width = wid
        self.complete_value = win
        self.score = 0
        self.field = None
        self.highest_score = 0
        self.set_board()
        with open("highest", "w+") as f:
            data = f.read()
            if data == '':
                pass
            elif data.isdigit():
                self.highest_score = int(data)
            else:
                print("loading highest score error, resetting")
                f.write("0")

    def set_board(self):
        """
        initialize field
        :return: None
        """
        if self.score > self.highest_score:
            with open("highest", "w+") as f:
                f.write(str(self.score))
            self.highest_score = self.score

        self.score = 0
        self.field = [[0] * self.width for _ in range(self.height)]
        self.spawn()
        self.spawn()

    def spawn(self):
        """
        spawn a new 2 or 4 on board
        4->10% possibility
        :return: None
        """
        new_element = 4 if randrange(100) > 90 else 2
        # select an empty pit
        (i, j) = choice([(i, j) for i in range(self.width) for j in range(self.height) if self.field[i][j] == 0])
        self.field[i][j] = new_element

    @property
    def is_win(self):
        for row in self.field:
            if any(i >= self.complete_value for i in row):
                return True
        return False

    @property
    def is_over(self):
        return not any(self.move_check(move) for move in Tools.actions)

    def move_check(self, direction):
        """
        check if shift to a direction is possible
        :param direction:
        :return: boolean
        """

        def check_left(row):

            def change(i):
                if row[i] == 0 and row[i + 1] != 0:  # move
                    return True
                if row[i] != 0 and row[i + 1] == row[i]:  # combine
                    return True
                return False

            return any(change(i) for i in range(len(row) - 1))

        check = {'left': lambda field: any(check_left(row) for row in field)}
        check['right'] = lambda field: check['left'](Tools.invert(field))
        check['up'] = lambda field: check['left'](Tools.transpose(field))
        check['down'] = lambda field: check['right'](Tools.transpose(field))

        if direction in check:
            return check[direction](self.field)
        else:
            return False

    def move(self, direction):

        moves = {'left': lambda field: [shift_left(row) for row in field]}
        moves['right'] = lambda field: Tools.invert(moves['left'](Tools.invert(field)))
        moves['up'] = lambda field: Tools.transpose(moves['left'](Tools.transpose(field)))
        moves['down'] = lambda field: Tools.transpose(moves['right'](Tools.transpose(field)))

        def shift_left(row):

            def tighten(raw_row):
                """
                get the row after shift
                :param raw_row:
                :return: new_row : new form of row after shifting
                """
                new_row = [i for i in raw_row if i != 0]  # elements in row
                new_row += [0 for _ in range(len(raw_row) - len(new_row))]
                return new_row

            def merge(a_row):
                pair = False
                new_row = []
                for i in range(len(a_row)):
                    if pair:
                        new_row.append(2 * a_row[i])
                        self.score += 2 * a_row[i]
                        pair = False
                    else:
                        if i + 1 < len(a_row) and a_row[i] == a_row[i + 1]:
                            pair = True
                            new_row.append(0)
                        else:
                            new_row.append(a_row[i])
                assert len(new_row) == len(a_row)
                return new_row

            return tighten(merge(tighten(row)))

        if direction in moves:
            if self.move_check(direction):
                self.field = moves[direction](self.field)  # replace
                self.spawn()
                return True
            else:
                return False

    def draw(self, screen):
        from collections import defaultdict

        ending_str = '           End'
        success_str = '          Target Reached!'
        guide = "         Keyboard Guide"
        helper1 = '(W)Up (S)Down (A)Left (D)Right'
        helper2 = '     (G)Restart (T)Exit'

        def display_str(string):
            screen.addstr(string + '\n')

        def draw_lines():
            line = ('+------' * self.width + '+')
            separator = defaultdict(lambda: line)
            if not hasattr(draw_lines, "counter"):
                draw_lines.counter = 0
            display_str(separator[draw_lines.counter])
            draw_lines.counter += 1

        def draw_row(num_row):
            display_str(''.join('|{: ^5} '.format(num) if num > 0 else '|      ' for num in num_row) + '|')

        screen.clear()
        display_str('SCORE: ' + str(self.score))
        if 0 != self.highest_score:
            display_str('HIGH SCORE: ' + str(self.highest_score))
        for row in self.field:
            draw_lines()
            draw_row(row)
        draw_lines()
        if self.is_over:
            display_str(ending_str)
        else:
            if self.is_win:
                display_str(success_str)
            else:
                display_str("\n")
        
        display_str(guide)
        display_str(helper1)
        display_str(helper2)


def main(stdscr):
    ground = Model2048()

    class Loop:
        def __init__(self):
            self.state = "I"
            self.state_actions = {
                'I': self.initial,
                'O': lambda: self.ending,
                'G': self.gaming
            }

        def initial(self):
            ground.set_board()
            self.state = "G"

        def ending(self):
            while True:
                action = Tools.get_user_action(stdscr)
                if action == 'restart':
                    self.state = "I"
                elif action == 'exit':
                    self.state = "Q"

        def gaming(self):
            action = Tools.get_user_action(stdscr)

            if action == 'restart':
                self.state = "I"
            if action == 'exit':
                self.state = "Q"
            if ground.move(action):  # move successful
                if ground.is_over:
                    self.state = "O"
            else:
                self.state = "G"

    loop = Loop()
    while loop.state != "Q":  # Quit
        ground.draw(stdscr)
        loop.state_actions[loop.state]()


if __name__ == "__main__":
    import curses

    curses.wrapper(main)
