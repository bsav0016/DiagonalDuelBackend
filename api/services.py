from datetime import timedelta
from django.utils import timezone
from .models import Game, Move


class GameService:
    @staticmethod
    def start_game(player1, player2, time_limit):
        if player1 == player2:
            raise ValueError("Player 1 and Player 2 cannot be the same.")

        game = Game.objects.create(player1=player1, player2=player2, time_limit=time_limit)
        return game

    @staticmethod
    def get_remaining_time(game):
        elapsed_time = timezone.now() - game.created_at
        remaining_time = game.time_limit - elapsed_time
        return max(remaining_time, timedelta(seconds=0))

    @staticmethod
    def make_move(game, player, row, column):
        if game.is_complete:
            raise ValueError("Game is already complete.")

        if (game.moves.count() % 2 == 0 and player != game.player1) or (
                game.moves.count() % 2 == 1 and player != game.player2):
            raise ValueError("It's your opponent's turn!")

        move = Move.objects.create(game=game, player=player, row=row, column=column, move_order=game.moves.count() + 1)

        winner = game.check_winner()
        if winner:
            game.winner = winner
            game.is_complete = True
            game.save()

        return move

    @staticmethod
    def build_board(game):
        all_moves = game.moves.all()
        board = [[0] * 8 for _ in range(8)]
        for move in all_moves:
            player = 1
            if move.move_order % 2 == 1:
                player = 2
            board[move.row][move.column] = player
        return board

    @staticmethod
    def check_winner(game):
        board = game.build_board()

        def check_direction(i, j, di, dj, player):
            count = 0
            for k in range(4):
                if 0 <= i + di * k < 8 and 0 <= j + dj * k < 8 and board[i + di * k][j + dj * k] == player:
                    count += 1
                else:
                    break
            return count == 4

        for i in range(8):
            for j in range(8):
                if board[i][j] == 0:
                    continue
                player = board[i][j]
                if (check_direction(i, j, 0, 1, player) or
                        check_direction(i, j, 1, 0, player) or
                        check_direction(i, j, 1, 1, player) or
                        check_direction(i, j, 1, -1, player)):
                    return player
        return None