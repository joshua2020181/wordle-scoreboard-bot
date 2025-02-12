# wordle-scoreboard-bot

Simple discord bot that compiles the results of popular Wordle-like games, such as [Tradle](https://games.oec.world/en/tradle/), [Yeardle](https://histordle.com/yeardle/), or [Connections](https://www.nytimes.com/games/connections) and has a daily leaderboard. Just press "share results" after playing one of the supported games and send it to the designated channel for this bot. It will send out a daily scoreboard message at midnight, and also has the `scoreboard` command to send the current scoreboard.

## Example messages from Wordle-like games:
```
#Tradle #1071 1/6
🟩🟩🟩🟩🟩
https://oec.world/en/games/tradle
```

```
#Yeardle #1055.0416666667
⬛⬛🟫🟥🟥🟫🟥🟥
🔼🔼🔼🔽🔽🔽🔽🔽
https://histordle.com/yeardle/
```

## Example scoreboard:
```md
# Today's -dle game results:
## Today's winner:
**user1** with 2 wins
## Connections #199
**user1: 5 guesses**
user2: 6 guesses
user3: 6 guesses
## Yeardle #645
**user3: 2 guesses**
user2: 6 guesses
## Tradle #660
**user1: 4 guesses**
user2: 5 guesses
user3: 5 guesses
## Current stats:
Player | Wins | Total
user1 | 2 | 2
user2 | 1 | 3
user3 | 0 | 3
```

