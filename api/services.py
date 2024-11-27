from datetime import datetime, timezone
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
from .models import Move


class GameService:
    @staticmethod
    def make_move(game, player, row, column):
        if game.is_complete:
            raise ValueError("Game is already complete.")
        if not (player == game.get_turn()):
            raise ValueError("It's not your turn!")

        move = Move.objects.create(game_ref=game, player=player, row=row, column=column, move_order=game.moves.count() + 1)
        board = GameService.build_board(game)
        if player == game.player1:
            piece = 1
        else:
            piece = 2

        board[row][column] = piece
        winner = GameService.check_winner(game)
        if winner:
            game.winner = winner
            game.is_complete = True

        game.updated_at = datetime.now(timezone.utc)
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
    def is_valid(board, row, col):
        if board[row][col] != 0:
            return False
        elif row == 0 or col == 0:
            return True
        elif board[row-1][col] == 0 and board[row-1][col-1] == 0 and board[row][col-1] == 0:
            return False
        else:
            return True

    @staticmethod
    def check_winner(game):
        board = GameService.build_board(game)

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

class CleanupService:
    def clean_expired_blacklisted_tokens(self):
        now = timezone.now()
        BlacklistedToken.objects.filter(expires_at__lt=now).delete()