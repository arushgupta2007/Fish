from .fish.game.game import Game
from .fish.models.enums import HalfSuits
from .fish.utils.rank_suite import id_to_rank_suit

if __name__ == "__main__":
    hs_map = {"sl": HalfSuits.SPADES_LOW, "sh": HalfSuits.SPADES_HIGH, "hl": HalfSuits.HEARTS_LOW, "hh": HalfSuits.HEARTS_HIGH, "dl": HalfSuits.DIAMONDS_LOW, "dh": HalfSuits.DIAMONDS_HIGH, "cl": HalfSuits.CLUBS_LOW, "ch": HalfSuits.CLUBS_HIGH, "jj": HalfSuits.SPECIAL}


    game = Game()

    while True:
        cmd = input("> ")
        cmds = cmd.split(" ")
        action = cmds[0]

        try:
            if action == "p":
                print(f"Team 1: {game.teams[0].score}, Team 2: {game.teams[1].score}")

                hss = {c[0]: "Claimed" if c[1].claimed else "Unclaimed" for c in game.half_suits.items()}
                print(f"{hss}")
                for plyr_id in game.players:
                    print(f"\t{plyr_id}: {list(map(lambda c: c.id, game.players[plyr_id].hand))}")

                print(f"Turn: {game.player_turn}")

            if action == "j":
                id = cmds[1]
                game.join_player(id, id)
                print(f"{id} has joined the game. Team: {game.players[id].team}")
            if action == "w":
                id = cmds[1]
                game.team_swap_player(id)
                print(f"{id} has swapped teams. Team: {game.players[id].team}")
            if action == "s":
                turn = game.start_game()
                for plyr_id in game.players:
                    print(f"\t{plyr_id}: {list(map(lambda c: c.id, game.players[plyr_id].hand))}")

                print(f"Turn: {turn}")
            if action == "a":
                ask = game.player_turn
                resp = cmds[1]
                card_id = cmds[2]

                rs = id_to_rank_suit(card_id)
                if rs is None:
                    raise Exception("Invalid card")
                card = game.get_card(*rs)
                res = game.ask(ask or "", resp, card)
                if res.success:
                    print(f"Successful ask! {ask} got {card} from {resp}")
                else:
                    print(f"Unsuccessful ask! Turn: {resp}")
            if action == "c":
                cid = cmds[1]
                hs = hs_map[cmds[2]]
                assignment = { c.split(":")[0]:c.split(":")[1] for c in cmds[3].split(",") }
                res, turn, done = game.claim(cid, hs, assignment)
                if res.success:
                    print("Successful claim!")
                else:
                    print("Wrong claim!")
                print(f"{hs} suit is done!")
                if done:
                    print(f"Game Finished! Team 1: {game.teams[0].score}  Team 2: {game.teams[1].score}")
                else:
                    print(f"Turn: {turn}")
            if action == "co":
                cid = cmds[1]
                hs = hs_map[cmds[2]]
                res = game.claim_opp(cid, hs)
                print(f"{cid} want to claim for opponent, the suit {hs}")
            if action == "ccp":
                pid = cmds[1]
                res = game.claim_counter_pass(pid)
                print(f"{pid} has passed on counter claim")
                if res:
                    print(f"Everyone on the team has passed. Now {game.claims[-1].claimant} must claim the suit")
            if action == "cc":
                cid = cmds[1]
                assignment = { c.split(":")[0]:c.split(":")[1] for c in cmds[2].split(",") }
                res, turn, done = game.claim_counter(cid, assignment)
                if res.success:
                    print("Successful counter claim!")
                else:
                    print("Wrong counter claim!")
                print(f"{res.half_suit} suit is done!")
                if done:
                    print(f"Game Finished! Team 1: {game.teams[0].score}  Team 2: {game.teams[1].score}")
                else:
                    print(f"Turn: {turn}")
            if action == "cou":
                assignment = { c.split(":")[0]:c.split(":")[1] for c in cmds[1].split(",") }
                res, turn, done = game.claim_opp_unopposed(assignment)
                if res.success:
                    print("Successful counter claim!")
                else:
                    print("Wrong counter claim!")
                print(f"{res.half_suit} suit is done!")
                if done:
                    print(f"Game Finished! Team 1: {game.teams[0].score}  Team 2: {game.teams[1].score}")
                else:
                    print(f"Turn: {turn}")

        except Exception as e:
            print(f"Error!!!: {e}")

