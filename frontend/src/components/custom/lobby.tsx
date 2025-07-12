import type { Player } from "@/types/api"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "../ui/card"
import { Button } from "../ui/button"
import { Crown, FishSymbol, Loader2Icon } from "lucide-react"
import { TeamID } from "@/types/enums"
import { truncateString } from "@/utils/utils"
import { TRUNCATE_NAME } from "@/utils/constants"

type LobbyProps = {
  game_id: string,
  loading: boolean,
  players: Record<string, Player>,
  isHost: boolean,
  error: string | undefined,
  onStart(): void
}

function teamDefault(arr: any[]) {
  if (arr.length == 0) return <span className="text-sm italic text-gray-400">No players yet...</span>
  return arr
}

// TODO: GAME ID
export default function Lobby({ game_id, loading, players, isHost, onStart, error }: LobbyProps) {
  const plyrRow = (plyr: Player) => {
    return (
      <div className="border-1 border-gray-300 w-full p-2 flex flex-row gap-2" key={plyr.id}>
        {plyr.host && <Crown width="16px" />}
        <h1> {plyr.me ? truncateString(plyr.name, TRUNCATE_NAME - 6) + " - You" :  truncateString(plyr.name, TRUNCATE_NAME) } </h1>
      </div>
    )
  }

  return (
    <div className="w-full h-full flex items-center justify-center p-5 sm:p-10 md:p-20 bg-gray-100">
      <Card className="min-w-2xs sm:min-w-lg">
        <CardHeader>
          <CardTitle className="text-xl">Lobby - {game_id}</CardTitle>
          <CardDescription>Once all the players join, the host will start the game...</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col relative sm:flex-row gap-4">
            <div className="flex flex-col gap-2 w-full px-2">
              <h1 className="font-semibold">Team 1</h1>
              <div className="flex flex-col">
                {teamDefault(Object.entries(players).filter(([_, plyr]) => plyr.team == TeamID.TEAM_1).map((([_, plyr]) => {
                  return plyrRow(plyr)
                })))}
              </div>
            </div>
            <div className="sm:absolute sm:left-[50%] sm:top-0 sm:bottom-0 border-1 border-gray-200"></div>
            <div className="flex flex-col gap-2 w-full px-2">
              <h1 className="font-semibold">Team 2</h1>
              <div className="flex flex-col">
                {teamDefault(Object.entries(players).filter(([_, plyr]) => plyr.team == TeamID.TEAM_2).map((([_, plyr]) => {
                  return plyrRow(plyr)
                })))}
              </div>
            </div>
          </div>
        </CardContent>

        {isHost && 
          <CardFooter className="mt-4">
            <div className="w-full flex flex-col gap-4">
            { error && <span className="text-sm text-red-500">{error}</span> }
            { loading ?
              <Button type="submit" className="w-full" disabled> <Loader2Icon className='animate-spin' /> Start Game! </Button>
              : <Button type="submit" className="w-full" onClick={onStart}> <FishSymbol /> Start Game! </Button> }
            </div>
          </CardFooter>
        }
      </Card>
    </div>
  )
}

