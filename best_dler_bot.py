import asyncio
import json
import os
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Union

import discord
import regex
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
intents = discord.Intents.default()
intents.message_content = True


DATA_FILE = "scores.json"
TOKEN = os.getenv("DISCORD_TOKEN", "")
INTENTS = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

APPROVED_GAMES = {
    "Connections": "Connections \nPuzzle #",
    "Yeardle": "#Yeardle",
    "Tradle": "#Tradle",
}


@dataclass
class Score:
    game: str
    player: str
    id: int
    time: int
    num_guesses: int

    @classmethod
    def from_msg(cls, msg: discord.Message):
        game = which_game(msg)
        if game is None:
            raise ValueError("message is not a valid -dle game")
        player = msg.author.name
        id = int(regex.search(r"#\d\d\d", msg.content).group()[1:])
        _time = int(datetime.now().timestamp())
        num_guesses = cls._get_guesses(game, msg.content)
        return cls(game, player, id, _time, num_guesses)

    @classmethod
    def _get_guesses(cls, game: str, msg: str) -> int:
        if game == "Connections":
            guesses = 0
            for line in msg.split("\n"):
                if regex.match(r"^\p{Emoji}", line) is not None:
                    guesses += 1
            return guesses
        elif game == "Tradle":
            if regex.search(r"(\d+)/6", msg) is None:
                return 7
            return int(regex.search(r"(\d+)/6", msg).group(1))
        elif game == "Yeardle":
            line = msg.split("\n")[1]
            if regex.search(r"\p{Emoji}", line):
                guesses = line.find("\U0001F7E9") + 1
                return guesses if guesses >= 0 else 9

    def __str__(self):
        return f"{self.game} {self.player} {self.id} {self.time} {self.num_guesses}"


class Scoreboard:
    def __init__(self):
        self.scores = []
        self._load()

    def _load(self):
        if not os.path.exists(DATA_FILE):
            return
        with open(DATA_FILE, "r") as f:
            self.scores = [Score(**x) for x in json.load(f)]
        self._save()  # also validates

    def _save(self):
        self._validate()
        with open(DATA_FILE, "w") as f:
            json.dump([x.__dict__ for x in self.scores], f, indent=4)

    def _is_valid_score(self, score: Score) -> bool:
        # check if score is within the last day
        if score.time < time.time() - 24 * 60 * 60:
            return False
        # check if score is already in the Scoreboard
        for s in self.scores:
            if s.game == score.game and s.player == score.player and s.id == score.id:
                return False
        # if this is a new score, clear all old scores for that game
        for s in self.scores:
            if s.game == score.game and score.id > s.id:
                print(f"removing {s.game} #{s.id}")
                self.scores.remove(s)
        return True

    def _validate(self) -> None:
        if len(self.scores) == 0:
            return

        for game in APPROVED_GAMES.keys():
            scores = [x for x in self.scores if x.game == game]
            if len(scores) > 0:
                _id = scores[0].id
                for score in scores:
                    if score.id != _id:
                        print("multiple ids for same game on the same day")

    def add(self, score: Score) -> None:
        if not self._is_valid_score(score):
            print("invalid score")
            return
        self.scores.append(score)
        print(f"adding {score.game} #{score.id}")
        self._save()

    def get_scoreboard_message(self) -> str:
        msg = "# Current -dle game scores:\n"
        players = set([x.player for x in self.scores])
        player_stats = {player: [0, 0] for player in players}  # player: [wins, total]
        for score in self.scores:
            player_stats[score.player][1] += 1

        for game in APPROVED_GAMES.keys():
            game_scores = [x for x in self.scores if x.game == game]
            if len(game_scores) == 0:
                continue
            # sort by num_guesses
            game_scores.sort(key=lambda x: x.num_guesses)
            msg += f"## {game} #{game_scores[0].id}\n"
            msg += f"**{game_scores[0].player}: {game_scores[0].num_guesses} guesses**\n"
            player_stats[game_scores[0].player][0] += 1
            for score in game_scores[1:]:
                msg += f"{score.player}: {score.num_guesses} guesses\n"
        msg += "## Current stats:\n"
        # sort by wins
        player_stats = sorted(player_stats.items(), key=lambda x: x[1][0], reverse=True)
        msg += "Player | Wins | Total\n"
        for player, stats in player_stats:
            msg += f"{player} | {stats[0]} | {stats[1]}\n"
        return msg

    def _get_secret_message(self, winner: str) -> str:
        return ""

    def _get_daily_message(self) -> str:
        scoreboard_msg_ls = self.get_scoreboard_message().split("\n")
        winner = scoreboard_msg_ls[scoreboard_msg_ls.index("Player | Wins | Total") + 1].split("|")
        msg = "# Today's -dle game results:\n"
        msg += "## Today's winner:\n"
        msg += f"**{winner[0].strip()}** with {winner[1].strip()} wins\n"
        msg += self._get_secret_message(winner[0].strip())
        msg += "\n".join(scoreboard_msg_ls[1:])
        return msg

    async def daily_message(self, channel_id: int) -> None:
        await bot.wait_until_ready()
        channel = bot.get_channel(channel_id)
        while not bot.is_closed():
            # wait until midnight
            now = datetime.now()
            tomorrow = now.replace(day=now.day + 1, hour=0, minute=0, second=0, microsecond=0)
            await asyncio.sleep((tomorrow - now).seconds)
            await channel.send(self._get_daily_message())

    def __str__(self):
        return "\n".join([str(x) for x in self.scores])


def which_game(msg) -> Union[None, str]:
    for game, prefix in APPROVED_GAMES.items():
        if msg.content.startswith(prefix):
            return game
    return None


SCOREBOARD = Scoreboard()


@bot.command()
async def scoreboard(ctx):
    await ctx.send(SCOREBOARD.get_scoreboard_message())

@bot.command()
async def daily(ctx):
    await ctx.send(SCOREBOARD._get_daily_message())

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    print(f"{message.channel}")
    if which_game(message):
        print(f"Message from {message.author}: {message.content}")
        score = Score.from_msg(message)
        print(score)
        SCOREBOARD.add(score)
    await bot.process_commands(message)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} ({bot.user.id})")
    print("------")
    bot.loop.create_task(SCOREBOARD.daily_message(int(os.getenv("SCOREBOARD_CHANNEL_ID", ""))))

bot.run(TOKEN)
