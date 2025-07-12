import './Game.css'
import useWebSocket from 'react-use-websocket'
import { ApiMessageAskSchema, ApiMessageClaimOppPassSchema, ApiMessageClaimOppSchema, ApiMessageClaimSchema, ApiMessageErrorSchema, ApiMessageGameFinishedSchema, ApiMessageGameStartSchema, ApiMessageHandSchema, ApiMessageNewConnectionSchema, ApiMessagePlayerJoinedSchema, ApiMessagePlayerLeftSchema, ApiMessageSchema, type ApiMessageAsk, type ApiMessageClaim, type ApiMessageClaimOpp, type ApiMessageClaimOppPass, type ApiMessageError, type ApiMessageGameFinished, type ApiMessageGameStart, type ApiMessageHand, type ApiMessageNewConnection, type ApiMessagePlayerJoined, type ApiMessagePlayerLeft, type Player } from '@/types/api'
import { useEffect, useRef, useState } from 'react'
import Register from '@/components/custom/register'
import { ApiEvent, CardRank, CardSuit, HalfSuits, TeamID } from '@/types/enums'
import Lobby from '@/components/custom/lobby'
import { Card, create_all_cards } from '@/types/card'
import CardComponent from '@/components/custom/card/card'
import { Button } from '@/components/ui/button'
import { Check, Club, Crown, Diamond, Heart, Laugh, Spade, X } from 'lucide-react'
import { truncateString, unique_card_id } from '@/utils/utils'
import { TRUNCATE_NAME } from '@/utils/constants'
import { Badge } from '@/components/ui/badge'
import { Dialog, DialogClose, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Label } from '@/components/ui/label'
import { Input } from '@/components/ui/input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import * as z from "zod";
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/components/ui/form'
import { toast } from 'sonner'
import { half_suit_id } from '@/utils/card'
import { Separator } from '@radix-ui/react-select'

const State = {
  REGISTER: "REGISTER",
  LOBBY: "LOBBY",
  ACTIVE_ASK: "ACTIVE_ASK",
  ACTIVE_CLAIM: "ACTIVE_CLAIM",
  FINISHED: "FINISHED"
}

const halfSuitNames = ["Lower Spades", "Higher Spades", "Lower Hearts", "Higher Hearts", "Lower Diamonds", "Higher Diamonds", "Lower Clubs", "Higher Clubs", "Special"];

const allCards = create_all_cards()

export default function Game() {
  const [state, setState] =  useState(State.REGISTER)
  const [gameID, setGameID] = useState<string | undefined>()
  const [playerName, setPlayerName] = useState<string | undefined>()

  const [registerLoading, setRegisterLoading] = useState(false)
  const [registerPlayerNameError, setRegisterPlayerNameError] = useState(false)

  const [lobbyWaiting, setLobbyWaiting] = useState(false)
  const [lobbyError, setLobbyError] = useState<string | undefined>()

  const [players, setPlayers] = useState<Record<string, Player>>()
  const [turn, setTurn] = useState<string | undefined>()

  const [hand, setHand] = useState<Record<HalfSuits, Card[]>>({})

  const [team1Score, setTeam1Score] = useState(0)
  const [team2Score, setTeam2Score] = useState(0)

  const [claimedSuits, setClaimedSuits] = useState<{ hs: HalfSuits, to: TeamID }[]>([])
  const [askRecord, setAskRecord] = useState<ApiMessageAsk[]>([])

  const [currentClaimOpp, setCurrentClaimOpp] = useState<ApiMessageClaimOpp | undefined>({
    player_id: "1",
    team: 0,
    half_suit_id: 0
  })
  const [claimOppPassed, setClaimOppPassed] = useState<Player[]>([])
  const [claimOppAllPassed, setClaimOppAllPassed] = useState(false)

  const have_half_suit = (rank: CardRank, suit: CardSuit) => {
    const card = new Card(unique_card_id(rank, suit))
    return hand.hasOwnProperty(card.half_suit_id) && hand[card.half_suit_id].length > 0
  };

  const askSchema = z.object({
    rank: z.enum(CardRank, { error: "Invalid Rank" }),
    suit: z.enum(CardSuit, { error: "Invalid Suit" }),
    to: z.string({ error: "Please select player" }),
  }).refine((data) => (data.rank != CardRank.JOKER && data.rank != CardRank.CUT) || data.suit == CardSuit.JOKER, {
    error: "Joker and Cut card must have suit Joker",
    path: ["suit"]
  }).refine((data) => have_half_suit(data.rank, data.suit), {
    error: "You must have a card of the Half Suit",
    path: ["rank"]
  }).refine((data) => players?.hasOwnProperty(data.to) && players[data.to].team != players[playerName!].team, {
    error: "Invalid Player ID",
    path: ["to"]
  })
  type Ask = z.infer<typeof askSchema>

  const askFormRef = useRef<HTMLFormElement>(null)
  const askFormCloseRef = useRef<HTMLButtonElement>(null)
  const askForm = useForm<z.infer<typeof askSchema>>({
    resolver: zodResolver(askSchema),
    defaultValues: {
      rank: CardRank.ACE,
      suit: CardSuit.SPADES,
      to: undefined,
    }
  })
  const askRank = askForm.watch("rank")

  const claimSchema = z.object({
    half_suit: z.enum(Object.fromEntries(Object.entries(HalfSuits).map(([id, v]) => [id, v.toString()])), { error: "Invalid Half Suit" }),
    card1: z.string({ error: "Please select player" }),
    card2: z.string({ error: "Please select player" }),
    card3: z.string({ error: "Please select player" }),
    card4: z.string({ error: "Please select player" }),
    card5: z.string({ error: "Please select player" }),
    card6: z.string({ error: "Please select player" }),
  }).refine((data) => !claimedSuits.map((x) => x.hs.toString()).includes(data.half_suit), {
    error: "Cannot claim finished suit",
    path: ["half_suit"]
  }).refine((data) => players?.hasOwnProperty(data.card1), {
    error: "Invalid Player ID",
    path: ["card1"]
  }).refine((data) => players?.hasOwnProperty(data.card2), {
    error: "Invalid Player ID",
    path: ["card2"]
  }).refine((data) => players?.hasOwnProperty(data.card3), {
    error: "Invalid Player ID",
    path: ["card3"]
  }).refine((data) => players?.hasOwnProperty(data.card4), {
    error: "Invalid Player ID",
    path: ["card4"]
  }).refine((data) => players?.hasOwnProperty(data.card5), {
    error: "Invalid Player ID",
    path: ["card5"]
  }).refine((data) => players?.hasOwnProperty(data.card6), {
    error: "Invalid Player ID",
    path: ["card6"]
  }).refine((data) => players?.[data.card1].team == players?.[playerName!].team &&
                      players?.[data.card1].team == players?.[data.card2].team &&
                      players?.[data.card1].team == players?.[data.card3].team &&
                      players?.[data.card1].team == players?.[data.card4].team &&
                      players?.[data.card1].team == players?.[data.card5].team &&
                      players?.[data.card1].team == players?.[data.card6].team, {
    error: "All players must be in your team",
    path: ["card6"]
  })
  type Claim = z.infer<typeof claimSchema>

  const claimFormRef = useRef<HTMLFormElement>(null)
  const claimFormCloseRef = useRef<HTMLButtonElement>(null)
  const claimForm = useForm<z.infer<typeof claimSchema>>({
    resolver: zodResolver(claimSchema),
    defaultValues: {
      half_suit: HalfSuits.SPECIAL.toString(),
      card1: undefined,
      card2: undefined,
      card3: undefined,
      card4: undefined,
      card5: undefined,
      card6: undefined,
    }
  })
  const claimHalfSuit = claimForm.watch("half_suit")

  const claimOppSchema = z.object({
    half_suit: z.enum(Object.fromEntries(Object.entries(HalfSuits).map(([id, v]) => [id, v.toString()])), { error: "Invalid Half Suit" }),
  }).refine((data) => !claimedSuits.map((x) => x.hs.toString()).includes(data.half_suit), {
    error: "Cannot claim finished suit",
    path: ["half_suit"]
  })
  type ClaimOpp = z.infer<typeof claimOppSchema>

  const claimOppFormRef = useRef<HTMLFormElement>(null)
  const claimOppFormCloseRef = useRef<HTMLButtonElement>(null)
  const claimOppForm = useForm<z.infer<typeof claimOppSchema>>({
    resolver: zodResolver(claimOppSchema),
    defaultValues: {
      half_suit: HalfSuits.SPECIAL.toString(),
    }
  })

  const claimOppUnoppSchema = z.object({
    card1: z.string({ error: "Please select player" }),
    card2: z.string({ error: "Please select player" }),
    card3: z.string({ error: "Please select player" }),
    card4: z.string({ error: "Please select player" }),
    card5: z.string({ error: "Please select player" }),
    card6: z.string({ error: "Please select player" }),
  }).refine((data) => players?.hasOwnProperty(data.card1), {
    error: "Invalid Player ID",
    path: ["card1"]
  }).refine((data) => players?.hasOwnProperty(data.card2), {
    error: "Invalid Player ID",
    path: ["card2"]
  }).refine((data) => players?.hasOwnProperty(data.card3), {
    error: "Invalid Player ID",
    path: ["card3"]
  }).refine((data) => players?.hasOwnProperty(data.card4), {
    error: "Invalid Player ID",
    path: ["card4"]
  }).refine((data) => players?.hasOwnProperty(data.card5), {
    error: "Invalid Player ID",
    path: ["card5"]
  }).refine((data) => players?.hasOwnProperty(data.card6), {
    error: "Invalid Player ID",
    path: ["card6"]
  }).refine((data) => players?.[data.card1].team != players?.[playerName!].team &&
                      players?.[data.card1].team == players?.[data.card2].team &&
                      players?.[data.card1].team == players?.[data.card3].team &&
                      players?.[data.card1].team == players?.[data.card4].team &&
                      players?.[data.card1].team == players?.[data.card5].team &&
                      players?.[data.card1].team == players?.[data.card6].team, {
    error: "All players must be in the opponent team",
    path: ["card6"]
  })
  type ClaimOppUnopp = z.infer<typeof claimOppUnoppSchema>

  const claimOppUnoppFormRef = useRef<HTMLFormElement>(null)
  const claimOppUnoppFormCloseRef = useRef<HTMLButtonElement>(null)
  const claimOppUnoppForm = useForm<z.infer<typeof claimOppUnoppSchema>>({
    resolver: zodResolver(claimOppUnoppSchema),
    defaultValues: {
      card1: undefined,
      card2: undefined,
      card3: undefined,
      card4: undefined,
      card5: undefined,
      card6: undefined,
    }
  })

  const claimCounterSchema = z.object({
    card1: z.string({ error: "Please select player" }),
    card2: z.string({ error: "Please select player" }),
    card3: z.string({ error: "Please select player" }),
    card4: z.string({ error: "Please select player" }),
    card5: z.string({ error: "Please select player" }),
    card6: z.string({ error: "Please select player" }),
  }).refine((data) => players?.hasOwnProperty(data.card1), {
    error: "Invalid Player ID",
    path: ["card1"]
  }).refine((data) => players?.hasOwnProperty(data.card2), {
    error: "Invalid Player ID",
    path: ["card2"]
  }).refine((data) => players?.hasOwnProperty(data.card3), {
    error: "Invalid Player ID",
    path: ["card3"]
  }).refine((data) => players?.hasOwnProperty(data.card4), {
    error: "Invalid Player ID",
    path: ["card4"]
  }).refine((data) => players?.hasOwnProperty(data.card5), {
    error: "Invalid Player ID",
    path: ["card5"]
  }).refine((data) => players?.hasOwnProperty(data.card6), {
    error: "Invalid Player ID",
    path: ["card6"]
  }).refine((data) => players?.[data.card1].team == players?.[playerName!].team &&
                      players?.[data.card1].team == players?.[data.card2].team &&
                      players?.[data.card1].team == players?.[data.card3].team &&
                      players?.[data.card1].team == players?.[data.card4].team &&
                      players?.[data.card1].team == players?.[data.card5].team &&
                      players?.[data.card1].team == players?.[data.card6].team, {
    error: "All players must be in the same team",
    path: ["card6"]
  })
  type ClaimCounter = z.infer<typeof claimCounterSchema>

  const claimCounterFormRef = useRef<HTMLFormElement>(null)
  const claimCounterFormCloseRef = useRef<HTMLButtonElement>(null)
  const claimCounterForm = useForm<z.infer<typeof claimCounterSchema>>({
    resolver: zodResolver(claimCounterSchema),
    defaultValues: {
      card1: undefined,
      card2: undefined,
      card3: undefined,
      card4: undefined,
      card5: undefined,
      card6: undefined,
    }
  })

  const card_to_name = (c: Card) => {
    if (c.rank == CardRank.JOKER || c.rank == CardRank.CUT) return c.rank;
    return c.rank + " of " + c.suit
  }
  const recalculateClaimCardTitles = (hs: HalfSuits, setter: Function) => {
    const new_cards = allCards.filter((c) => c.half_suit_id == hs);
    setter({
      card1: card_to_name(new_cards[0]),
      card2: card_to_name(new_cards[1]),
      card3: card_to_name(new_cards[2]),
      card4: card_to_name(new_cards[3]),
      card5: card_to_name(new_cards[4]),
      card6: card_to_name(new_cards[5])
    })
  }
  var [claimCardTitles, setClaimCardTitles] = useState({ card1: "8 of Spades", card2: "8 of Diamonds", card3: "8 of Hearts", card4: "8 of Clubs", card5: "Joker", card6: "Cut" })
  const [claimOppUnoppCardTitles, setClaimOppUnoppCardTitles] = useState({ card1: "8 of Spades", card2: "8 of Diamonds", card3: "8 of Hearts", card4: "8 of Clubs", card5: "Joker", card6: "Cut" });
  const [claimCounterCardTitles, setClaimCounterCardTitles] = useState({ card1: "8 of Spades", card2: "8 of Diamonds", card3: "8 of Hearts", card4: "8 of Clubs", card5: "Joker", card6: "Cut" });

  useEffect(() => recalculateClaimCardTitles(parseInt(claimHalfSuit), setClaimCardTitles), [claimHalfSuit])
  useEffect(() => currentClaimOpp && recalculateClaimCardTitles(currentClaimOpp.half_suit_id, setClaimOppUnoppCardTitles), [currentClaimOpp])
  useEffect(() => currentClaimOpp && recalculateClaimCardTitles(currentClaimOpp.half_suit_id, setClaimCounterCardTitles), [currentClaimOpp])

  function teamDefault(arr: any[]) {
    if (arr.length == 0) return <span className="text-sm italic text-gray-400">No players here</span>
    return arr
  }
  function suitDefault(arr: any[]) {
    if (arr.length == 0) return <span className="text-sm italic text-gray-400">No suits claimed</span>
    return arr
  }
  function askDefault(arr: any[]) {
    if (arr.length == 0) return <span className="text-sm italic text-gray-400">No questions asked</span>
    return arr
  }
  function claimOppDefault(arr: any[]) {
    if (arr.length == 0) return <span className="text-sm italic text-gray-400">No players passed</span>
    return arr
  }

  function getClaimedSuitElement(hs: HalfSuits, idx: number) {
    const helper = () => {
      if (hs == HalfSuits.SPADES_LOW) return <h1> {idx}. Lower Spades <Spade className='inline' fill="black" size={16} /></h1>
      if (hs == HalfSuits.SPADES_HIGH) return <h1> {idx}. Higher Spades <Spade className='inline' fill="black" size={16} /></h1>
      if (hs == HalfSuits.DIAMONDS_LOW) return <h1> {idx}. Lower Diamonds <Diamond className='inline' fill="red" stroke='red' size={16} /></h1>
      if (hs == HalfSuits.DIAMONDS_HIGH) return <h1> {idx}. Upper Diamonds <Diamond className='inline' fill="red" stroke='red' size={16} /></h1>
      if (hs == HalfSuits.HEARTS_LOW) return <h1> {idx}. Lower Hearts <Heart className='inline' fill="red" stroke='red' size={16} /></h1>
      if (hs == HalfSuits.HEARTS_HIGH) return <h1> {idx}. Upper Hearts <Heart className='inline' fill="red"stroke='red' size={16} /></h1>
      if (hs == HalfSuits.CLUBS_LOW) return <h1> {idx}. Lower Clubs <Club className='inline' fill="black" size={16} /></h1>
      if (hs == HalfSuits.CLUBS_HIGH) return <h1> {idx}. Upper Clubs <Club className='inline' fill="black" size={16} /></h1>
      if (hs == HalfSuits.SPECIAL) return <h1> {idx}. Joker <Laugh className='inline' size={16} /></h1>
    }

    return (
      <div className="border-1 border-gray-300 w-full p-2 flex flex-row justify-between" key={hs}>
        <div className='flex flex-row gap-2'>
          {helper()}
        </div>
      </div>
    )
  }

  function getAskElement(ask: ApiMessageAsk, idx: number) {
    const from = players![ask.from_id]
    const to = players![ask.to_id]
    const card = new Card(ask.card_id)

    var icon;
    if (card.suit == CardSuit.SPADES) icon = <Spade className='inline ml-2' fill="black" size={16} />
    if (card.suit == CardSuit.DIAMONDS) icon = <Diamond className='inline ml-2' fill="red" stroke='red' size={16} />
    if (card.suit == CardSuit.HEARTS) icon = <Heart className='inline ml-2' fill="red" stroke='red' size={16} />
    if (card.suit == CardSuit.CLUBS) icon = <Club className='inline ml-2' fill="black" size={16} />
    if (card.suit == CardSuit.JOKER) icon = <Laugh className='inline ml-2' fill="black" size={16} />

    return (
      <div className="border-1 border-gray-300 w-full p-2 flex flex-row" key={idx}>
        <div className='flex flex-row gap-2 w-full justify-between'>
          <h1>
            {idx}.
            <code className='bg-gray-300 mx-3 relative rounded px-2 py-[0.2rem] font-mono font-semibold whitespace-nowrap'>
              {from.me ? <span> {truncateString(playerName!, TRUNCATE_NAME - 6) + " "} <i>- You</i> </span> :  truncateString(from.name, TRUNCATE_NAME) }
            </code>
            <span className='whitespace-normal'>
              asked
            </span>
            <code className='bg-gray-300 mx-3 relative rounded px-2 py-[0.2rem] font-mono font-semibold whitespace-nowrap'>
              {to.me ? <span> {truncateString(playerName!, TRUNCATE_NAME - 6) + " "} <i>- You</i> </span> :  truncateString(to.name, TRUNCATE_NAME) } 
            </code>
            <span className='whitespace-normal'>
              for the
            </span>
            <code className='bg-gray-300 mx-3 relative rounded px-2 py-[0.2rem] font-mono font-semibold whitespace-nowrap'>
              {card.rank} {card.rank != CardRank.JOKER && card.rank != CardRank.CUT && <span>of</span>}
              {icon}
            </code>
          </h1>
          {ask.success ?
            <Badge variant="secondary" className='bg-green-200'><Check size={16} strokeWidth={5} stroke='green' /></Badge> 
            : <Badge variant="secondary" className='bg-red-200'><X size={16} strokeWidth={5} stroke='red' /></Badge>}
        </div> 
      </div>
    )
  }

  function plyrRow(plyr: Player) {
    return (
      <div className="border-1 border-gray-300 w-full p-2 flex flex-row justify-between" key={plyr.id}>
        <div className='flex flex-row gap-2'>
          {plyr.host && <Crown width="16px" className='inline' />}
          <h1> {plyr.me ? <span> {truncateString(playerName!, TRUNCATE_NAME - 6) + " "} <i>- You</i> </span> :  truncateString(plyr.name, TRUNCATE_NAME) } </h1>
        </div>

        <Badge variant="secondary" className='bg-blue-100'> {plyr.num_cards} </Badge>
      </div>
    )
  }

  const handleNewConnection = (api_data: ApiMessageNewConnection) => {
    setRegisterLoading(false)
    setRegisterPlayerNameError(false)

    var new_players = Object.fromEntries(api_data.players!.map(p => [p.id, p]))
    new_players[playerName!].me = true
    setPlayers(new_players)
    setState(State.LOBBY)
  }

  const handlePlayerJoined = (api_data: ApiMessagePlayerJoined) => {
    if (players == undefined) {
      console.error("Handle Player Joined: Players is undefined")
      return
    }

    if (api_data.id in players) return
    var new_players: Record<string, Player> = players
    new_players[api_data.id] = api_data
    setPlayers(new_players)
  }
  const handlePlayerLeft = (api_data: ApiMessagePlayerLeft) => {
    if (players == undefined) {
      console.error("Handle Player Left: Players is undefined")
      return
    }

    if (!(api_data.id in players)) return;
    delete players[api_data.id]

    if (api_data.new_host) {
      if (!(api_data.new_host in players)) {
        console.error("Handle Player Left: New Host not in players")
        return
      }

      players[api_data.new_host].host = true
    }
  }
  const handleHand = (api_data: ApiMessageHand) => {
    var new_hand: Record<HalfSuits, Card[]> = {}
    var cards: Card[] = api_data.hand.map((h) => new Card(h))
    for (const v of cards) {
      if (!new_hand.hasOwnProperty(v.half_suit_id)) new_hand[v.half_suit_id] = [v]
      else new_hand[v.half_suit_id].push(v)
    }

    for (const hs of Object.values(HalfSuits))
      if (new_hand.hasOwnProperty(hs))
        new_hand[hs] = new_hand[hs].sort((a,b) => a.cmp(b))

    setHand(new_hand)   
    console.log(new_hand)
  }
  const handleGameStart = (api_data: ApiMessageGameStart) => {
    setLobbyWaiting(false)    
    setLobbyError(undefined)

    var new_players = structuredClone(players!)
    for (const plyr_id in api_data.num_cards)
      new_players[plyr_id].num_cards = api_data.num_cards[plyr_id]
    setPlayers(new_players)

    setTurn(api_data.starting_player)

    setState(State.ACTIVE_ASK)
  }
  const handleAsk = (api_data: ApiMessageAsk) => {
    const card = new Card(api_data.card_id)
    if (api_data.success) {
      toast.success("New Ask!", {
        description: `${truncateString(api_data.from_id, TRUNCATE_NAME)} asked ${truncateString(api_data.to_id, TRUNCATE_NAME)} for the ${card.rank} ${card.rank != CardRank.JOKER && card.rank != CardRank.CUT ? card.suit : ""} successfully`,
        duration: 8000,
      })
      players![api_data.from_id].num_cards! += 1
      players![api_data.to_id].num_cards! -= 1
    } else {
      toast.error("New Ask!", {
        description: `${truncateString(api_data.from_id, TRUNCATE_NAME)} asked ${truncateString(api_data.to_id, TRUNCATE_NAME)} for the ${card.rank} ${card.rank != CardRank.JOKER && card.rank != CardRank.CUT ? card.suit : ""} unsuccessfully`,
        duration: 8000,
      })
    }

    if (api_data.turn != playerName && api_data.from_id == playerName)
      askFormCloseRef.current?.click()

    setTurn(api_data.turn)

    var new_ask = structuredClone(askRecord)
    new_ask.push(api_data)
    setAskRecord(new_ask)
  }
  const handleGeneralClaim = (api_data: ApiMessageClaim) => {
    setTurn(api_data.turn)

    if (api_data.point_to == players![playerName!].team) {
      toast.success("New Claim!", {
        description: `The ${halfSuitNames[api_data.half_suit_id]} suit goes to ${api_data.point_to == 0 ? "Team 1" : "Team 2"}!`,
        duration: 8000,
      })
    } else {
      toast.error("New Claim!", {
        description: `The ${halfSuitNames[api_data.half_suit_id]} suit goes to ${api_data.point_to == 0 ? "Team 1" : "Team 2"}!`,
        duration: 8000,
      })
    }

    var claimedSuits_new = structuredClone(claimedSuits)
    claimedSuits_new.push({ hs: api_data.half_suit_id, to: api_data.point_to })
    setClaimedSuits(claimedSuits_new)

    var new_players = structuredClone(players!)
    for (const id in api_data.num_cards) {
      new_players[id].num_cards = api_data.num_cards[id]
    }
    setPlayers(new_players)

    console.log("AAAA", api_data)
    if (api_data.point_to == TeamID.TEAM_1) setTeam1Score(team1Score + 1)
    else setTeam2Score(team2Score + 1)
  }
  const handleClaim = (api_data: ApiMessageClaim) => {
    handleGeneralClaim(api_data)
  }
  const handleClaimOpp = (api_data: ApiMessageClaimOpp) => {
    setCurrentClaimOpp(api_data)
    setState(State.ACTIVE_CLAIM)
    askFormCloseRef.current?.click()
    claimFormCloseRef.current?.click()
    claimOppFormCloseRef.current?.click()
  }
  const handleClaimOppUnopp = (api_data: ApiMessageClaim) => {
    setCurrentClaimOpp(undefined)
    setState(State.ACTIVE_ASK)
    setClaimOppAllPassed(false)
    setClaimOppPassed([])

    handleGeneralClaim(api_data)
  }
  const handleClaimCounter = (api_data: ApiMessageClaim) => {
    setCurrentClaimOpp(undefined)
    setState(State.ACTIVE_ASK)
    setClaimOppAllPassed(false)
    setClaimOppPassed([])

    handleGeneralClaim(api_data)
  }
  const handleClaimOppPass = (api_data: ApiMessageClaimOppPass) => {
    var new_passed = claimOppPassed
    if (!players || !players.hasOwnProperty(api_data.player_id)) {
      console.error("No player found")
      return
    }

    toast.info("New Pass", {
      description: `${truncateString(api_data.player_id, TRUNCATE_NAME)} has passed!`,
      duration: 8000,
    })

    new_passed.push(players![api_data.player_id])
    setClaimOppPassed(new_passed)

    setClaimOppAllPassed(true)
  }
  const handleGameFinished = (api_data: ApiMessageGameFinished) => {
    if (api_data.winning_team == players![playerName!].team) {
      toast.success("Game Finished!", {
        description: `Team ${api_data.winning_team + 1} won ${api_data.final_scores.team1} - ${api_data.final_scores.team2}`,
        duration: 8000,
      })
    } else {
      toast.error("Game Finished!", {
        description: `Team ${api_data.winning_team + 1} won ${api_data.final_scores.team1} - ${api_data.final_scores.team2}`,
        duration: 8000,
      })
    }

    askFormCloseRef.current?.click()
    claimFormCloseRef.current?.click()
    claimOppFormCloseRef.current?.click()
    claimOppUnoppFormCloseRef.current?.click()

    setState(State.FINISHED)
  }
  const handleError = (api_data: ApiMessageError) => {
    if (!api_data.type) {
      console.error(`Random error ooccured: ${api_data.error}`)
      return
    }
    switch (api_data.type) {
      case ApiEvent.NEW_CONNECTION: {
        setRegisterPlayerNameError(true);
        setRegisterLoading(false);
        break;
      }

      case ApiEvent.GAME_START: {
        setLobbyError(api_data.error);
        setLobbyWaiting(false);
        break;
      }
    }
  }

  const socket_url = import.meta.env.VITE_WS_URL || "/ws"
  const socket = useWebSocket(socket_url, {
    onOpen: () => console.log('opened'),
    onMessage: (ev) => {
      console.log(ev)
      try {
        const data = JSON.parse(ev.data)
        const api_msg = ApiMessageSchema.safeParse(data)
        if (!api_msg.success) {
          console.error(`Invalid API Message: ${api_msg.error}`)
          return
        }
        switch (api_msg.data.type) {
          case ApiEvent.NEW_CONNECTION: {
            const api_data = ApiMessageNewConnectionSchema.safeParse(api_msg.data.data)
            if (!api_data.success) console.error(`Invalid New Connection Message: ${api_data.error}`)
            else handleNewConnection(api_data.data)
            break;
          }

          case ApiEvent.PLAYER_JOINED: {
            const api_data = ApiMessagePlayerJoinedSchema.safeParse(api_msg.data.data)
            if (!api_data.success) console.error(`Invalid Player Joined Message: ${api_data.error}`)
            else handlePlayerJoined(api_data.data)
            break;
          }

          case ApiEvent.PLAYER_LEFT: {
            const api_data = ApiMessagePlayerLeftSchema.safeParse(api_msg.data.data)
            if (!api_data.success) console.error(`Invalid Player Left Message: ${api_data.error}`)
            else handlePlayerLeft(api_data.data)
            break;
          }

          case ApiEvent.HAND: {
            const api_data = ApiMessageHandSchema.safeParse(api_msg.data.data)
            if (!api_data.success) console.error(`Invalid Hand Message: ${api_data.error}`)
            else handleHand(api_data.data)
            break;
          }

          case ApiEvent.GAME_START: {
            const api_data = ApiMessageGameStartSchema.safeParse(api_msg.data.data)
            if (!api_data.success) console.error(`Invalid Game Start Message: ${api_data.error}`)
            else handleGameStart(api_data.data)
            break;
          }

          case ApiEvent.ASK_REQUEST: {
            const api_data = ApiMessageAskSchema.safeParse(api_msg.data.data)
            if (!api_data.success) console.error(`Invalid Ask Message: ${api_data.error}`)
            else handleAsk(api_data.data)
            break;
          }

          case ApiEvent.CLAIM: {
            const api_data = ApiMessageClaimSchema.safeParse(api_msg.data.data)
            if (!api_data.success) console.error(`Invalid Claim Message: ${api_data.error}`)
            else handleClaim(api_data.data)
            break;
          }

          case ApiEvent.CLAIM_OPP: {
            const api_data = ApiMessageClaimOppSchema.safeParse(api_msg.data.data)
            if (!api_data.success) console.error(`Invalid Claim Opp Message: ${api_data.error}`)
            else handleClaimOpp(api_data.data)
            break;
          }

          case ApiEvent.CLAIM_OPP_UNOPP: {
            const api_data = ApiMessageClaimSchema.safeParse(api_msg.data.data)
            if (!api_data.success) console.error(`Invalid Claim Opp Message: ${api_data.error}`)
            else handleClaimOppUnopp(api_data.data)
            break;
          }

          case ApiEvent.CLAIM_COUNTER: {
            const api_data = ApiMessageClaimSchema.safeParse(api_msg.data.data)
            if (!api_data.success) console.error(`Invalid Claim Counter Message: ${api_data.error}`)
            else handleClaimCounter(api_data.data)
            break;
          }

          case ApiEvent.CLAIM_OPP_PASS: {
            const api_data = ApiMessageClaimOppPassSchema.safeParse(api_msg.data.data)
            if (!api_data.success) console.error(`Invalid Claim Opp Pass Message: ${api_data.error}`)
            else handleClaimOppPass(api_data.data)
            break;
          }

          case ApiEvent.GAME_FINISHED: {
            const api_data = ApiMessageGameFinishedSchema.safeParse(api_msg.data.data)
            if (!api_data.success) console.error(`Invalid Game Finished Message: ${api_data.error}`)
            else handleGameFinished(api_data.data)
            break;
          }

          case ApiEvent.ERROR: {
            const api_data = ApiMessageErrorSchema.safeParse(api_msg.data.data)
            if (!api_data.success) console.error(`Invalid Error Message: ${api_data.error}`)
            else handleError(api_data.data)
            break;
          }
        }
      } catch (e) {
        console.error(`Error Occured in receiving message: ${e}`)
      }
    },
    shouldReconnect: (_) => true,
  });

  const register = (game_id: string, player_name: string) => {
    setRegisterLoading(true)
    setGameID(game_id)
    setPlayerName(player_name)

    socket.sendJsonMessage({ type: ApiEvent.NEW_CONNECTION, data: { game_id, player_id: player_name } })
  }

  const start = () => {
    setLobbyWaiting(true)
    socket.sendJsonMessage({ type: ApiEvent.GAME_START })
  }

  const ask = (data: Ask) => {
    socket.sendJsonMessage({ type: ApiEvent.ASK_REQUEST, data: { to_id: data.to, card_id: unique_card_id(data.rank, data.suit) } })
  }
  const claim = (data: Claim) => {
    const new_cards = allCards.filter((c) => c.half_suit_id == parseInt(claimHalfSuit));
    socket.sendJsonMessage({
      type: ApiEvent.CLAIM,
      data: {
        half_suit_id: parseInt(claimHalfSuit),
        assignment: {
          [new_cards[0].id]: data.card1,
          [new_cards[1].id]: data.card2,
          [new_cards[2].id]: data.card3,
          [new_cards[3].id]: data.card4,
          [new_cards[4].id]: data.card5,
          [new_cards[5].id]: data.card6,
        }
      },
    })
  }
  const claimOpp = (data: ClaimOpp) => {
    claimOppFormCloseRef.current?.click()
    socket.sendJsonMessage({ type: ApiEvent.CLAIM_OPP, data: { half_suit_id: parseInt(data.half_suit) } })
  }
  const claimOppUnopp = (data: ClaimOppUnopp) => {
    claimOppUnoppFormCloseRef.current?.click()
    const hs = currentClaimOpp!.half_suit_id
    const new_cards = allCards.filter((c) => c.half_suit_id == hs);
    socket.sendJsonMessage({
      type: ApiEvent.CLAIM_OPP_UNOPP,
      data: {
        half_suit_id: hs,
        assignment: {
          [new_cards[0].id]: data.card1,
          [new_cards[1].id]: data.card2,
          [new_cards[2].id]: data.card3,
          [new_cards[3].id]: data.card4,
          [new_cards[4].id]: data.card5,
          [new_cards[5].id]: data.card6,
        }
      },
    })
  }
  const pass = () => {
    socket.sendJsonMessage({ type: ApiEvent.CLAIM_OPP_PASS })
  }
  const claimCounter = (data: ClaimCounter) => {
    claimOppUnoppFormCloseRef.current?.click()
    const hs = currentClaimOpp!.half_suit_id
    const new_cards = allCards.filter((c) => c.half_suit_id == hs);
    socket.sendJsonMessage({
      type: ApiEvent.CLAIM_COUNTER,
      data: {
        half_suit_id: hs,
        assignment: {
          [new_cards[0].id]: data.card1,
          [new_cards[1].id]: data.card2,
          [new_cards[2].id]: data.card3,
          [new_cards[3].id]: data.card4,
          [new_cards[4].id]: data.card5,
          [new_cards[5].id]: data.card6,
        }
      },
    })
  }

  return (
    <div className="w-[100vw] h-[100vh]">
      { state != State.REGISTER ? <></> :
        <Register loading={registerLoading} plyr_name_error={registerPlayerNameError} submit={register} />
      }
      { state != State.LOBBY ? <></> :
        <Lobby game_id={gameID || ""} players={players || {}} isHost={players![playerName!].host || false} loading={lobbyWaiting} onStart={start} error={lobbyError} />
      }
      { state != State.ACTIVE_ASK && state != State.ACTIVE_CLAIM && state != State.FINISHED ? <></> :
        <div className="w-full max-w-[100vw] min-h-full p-5 sm:p-10 md:p-20 bg-gray-100">
          <div className="flex flex-col w-full gap-20">
            { state == State.ACTIVE_CLAIM && currentClaimOpp && 
              <div className='flex flex-col w-full text-center'>
                <h1 className="text-lg text-red-600 sm:text-xl md:text-2xl lg:text-3xl font-bold inline mb-10">
                  Urgent! 
                  <code className="bg-gray-300 mx-3 relative rounded px-3 py-[0.2rem] font-mono font-semibold">
                    { players![currentClaimOpp.player_id].host && <Crown className='inline'/> } { currentClaimOpp.player_id == playerName ? <span> {truncateString(currentClaimOpp.player_id, TRUNCATE_NAME - 6) + " "} <i>- You</i> </span> : truncateString(currentClaimOpp.player_id ||"Unknown", TRUNCATE_NAME) } 
                  </code>
                  wants to claim the { halfSuitNames[currentClaimOpp.half_suit_id] } suit for { 1 - currentClaimOpp.team == 0 ? "Team 1" : "Team 2" }
                </h1>
                <div className="flex flex-col gap-2 w-full mx-auto px-2 sm:max-w-xl relative">
                  <div className='flex flex-row justify-between'>
                    <h1 className="font-semibold">Passed <i>{ claimOppAllPassed ? " - All passed" : " - Waiting for players..." }</i> </h1>
                    { currentClaimOpp.team != players![playerName!].team &&
                      <div className='flex gap-2'>
                        <Button size="sm" onClick={pass} disabled={claimOppPassed.map((x) => x.id).includes(playerName || "")}>Pass</Button>
                        <Dialog>
                          <Form {...claimCounterForm}>
                            <form ref={claimCounterFormRef} onSubmit={claimCounterForm.handleSubmit(claimCounter)}>
                              <DialogTrigger asChild>
                                <Button size="sm" disabled={claimOppPassed.map((x) => x.id).includes(playerName || "")}>Counter</Button>
                              </DialogTrigger>
                              <DialogContent className="sm:max-w-[425px]">
                                <DialogHeader>
                                  <DialogTitle>Counter Claim</DialogTitle>
                                  <DialogDescription>
                                    Claim {halfSuitNames[currentClaimOpp.half_suit_id]}
                                  </DialogDescription>
                                </DialogHeader>
                                <FormField
                                  control={claimCounterForm.control}
                                  name="card1"
                                  render={({ field }) => (
                                    <FormItem>
                                      <FormLabel className='mr-5'>{claimCounterCardTitles.card1 || "Card 1"}: </FormLabel>
                                      <Select onValueChange={field.onChange} defaultValue={field.value}>
                                        <FormControl>
                                          <SelectTrigger className="w-[180px]">
                                            <SelectValue placeholder="Player" />
                                          </SelectTrigger>
                                        </FormControl>
                                        <SelectContent>
                                          {Object.entries(players!).filter(([_, val]) => playerName && val.team == players?.[playerName].team).map(([_, val]) => {
                                            return <SelectItem value={val.id} key={val.id}>{val.id}</SelectItem>
                                          })}
                                        </SelectContent>
                                      </Select>
                                      <FormMessage />
                                    </FormItem>
                                )} />
                                <FormField
                                  control={claimCounterForm.control}
                                  name="card2"
                                  render={({ field }) => (
                                    <FormItem>
                                      <FormLabel className='mr-5'>{claimCounterCardTitles.card2 || "Card 2"}: </FormLabel>
                                      <Select onValueChange={field.onChange} defaultValue={field.value}>
                                        <FormControl>
                                          <SelectTrigger className="w-[180px]">
                                            <SelectValue placeholder="Player" />
                                          </SelectTrigger>
                                        </FormControl>
                                        <SelectContent>
                                          {Object.entries(players!).filter(([_, val]) => playerName && val.team == players?.[playerName].team).map(([_, val]) => {
                                            return <SelectItem value={val.id} key={val.id}>{val.id}</SelectItem>
                                          })}
                                        </SelectContent>
                                      </Select>
                                      <FormMessage />
                                    </FormItem>
                                )} />
                                <FormField
                                  control={claimCounterForm.control}
                                  name="card3"
                                  render={({ field }) => (
                                    <FormItem>
                                      <FormLabel className='mr-5'>{claimCounterCardTitles.card3 || "Card 3"}: </FormLabel>
                                      <Select onValueChange={field.onChange} defaultValue={field.value}>
                                        <FormControl>
                                          <SelectTrigger className="w-[180px]">
                                            <SelectValue placeholder="Player" />
                                          </SelectTrigger>
                                        </FormControl>
                                        <SelectContent>
                                          {Object.entries(players!).filter(([_, val]) => playerName && val.team == players?.[playerName].team).map(([_, val]) => {
                                            return <SelectItem value={val.id} key={val.id}>{val.id}</SelectItem>
                                          })}
                                        </SelectContent>
                                      </Select>
                                      <FormMessage />
                                    </FormItem>
                                )} />
                                <FormField
                                  control={claimCounterForm.control}
                                  name="card4"
                                  render={({ field }) => (
                                    <FormItem>
                                      <FormLabel className='mr-5'>{claimCounterCardTitles.card4 || "Card 4"}: </FormLabel>
                                      <Select onValueChange={field.onChange} defaultValue={field.value}>
                                        <FormControl>
                                          <SelectTrigger className="w-[180px]">
                                            <SelectValue placeholder="Player" />
                                          </SelectTrigger>
                                        </FormControl>
                                        <SelectContent>
                                          {Object.entries(players!).filter(([_, val]) => playerName && val.team == players?.[playerName].team).map(([_, val]) => {
                                            return <SelectItem value={val.id} key={val.id}>{val.id}</SelectItem>
                                          })}
                                        </SelectContent>
                                      </Select>
                                      <FormMessage />
                                    </FormItem>
                                )} />
                                <FormField
                                  control={claimCounterForm.control}
                                  name="card5"
                                  render={({ field }) => (
                                    <FormItem>
                                      <FormLabel className='mr-5'>{claimCounterCardTitles.card5 || "Card 5"}: </FormLabel>
                                      <Select onValueChange={field.onChange} defaultValue={field.value}>
                                        <FormControl>
                                          <SelectTrigger className="w-[180px]">
                                            <SelectValue placeholder="Player" />
                                          </SelectTrigger>
                                        </FormControl>
                                        <SelectContent>
                                          {Object.entries(players!).filter(([_, val]) => playerName && val.team == players?.[playerName].team).map(([_, val]) => {
                                            return <SelectItem value={val.id} key={val.id}>{val.id}</SelectItem>
                                          })}
                                        </SelectContent>
                                      </Select>
                                      <FormMessage />
                                    </FormItem>
                                )} />
                                <FormField
                                  control={claimCounterForm.control}
                                  name="card6"
                                  render={({ field }) => (
                                    <FormItem>
                                      <FormLabel className='mr-5'>{claimCounterCardTitles.card6 || "Card 6"}: </FormLabel>
                                      <Select onValueChange={field.onChange} defaultValue={field.value}>
                                        <FormControl>
                                          <SelectTrigger className="w-[180px]">
                                            <SelectValue placeholder="Player" />
                                          </SelectTrigger>
                                        </FormControl>
                                        <SelectContent>
                                          {Object.entries(players!).filter(([_, val]) => playerName && val.team == players?.[playerName].team).map(([_, val]) => {
                                            return <SelectItem value={val.id} key={val.id}>{val.id}</SelectItem>
                                          })}
                                        </SelectContent>
                                      </Select>
                                      <FormMessage />
                                    </FormItem>
                                )} />
                                <DialogFooter>
                                  <DialogClose asChild>
                                    <Button variant="outline" ref={claimCounterFormCloseRef}>Cancel</Button>
                                  </DialogClose>
                                  <Button onClick={() => {
                                    if (claimCounterFormRef.current) {
                                      claimCounterFormRef.current.dispatchEvent(new Event('submit', { bubbles: true }));
                                    }
                                  }}>
                                    Claim
                                  </Button>
                                </DialogFooter>
                              </DialogContent>
                            </form>
                          </Form>
                        </Dialog>
                      </div>
                    }
                  </div>
                  <div className="border-1 border-gray-200"></div>
                  <div className="flex flex-col text-sm sm:text-base">
                    {claimOppDefault(claimOppPassed.map((plyr) => {
                      return (
                        <div className="border-1 border-gray-300 w-full p-2 flex flex-row justify-between" key={plyr.id}>
                          <div className='flex flex-row gap-2'>
                            {plyr.host && <Crown width="16px" className='inline' />}
                            <h1> {plyr.me ? <span> {truncateString(playerName!, TRUNCATE_NAME - 6) + " "} <i>- You</i> </span> :  truncateString(plyr.name, TRUNCATE_NAME) } </h1>
                          </div>
                        </div>
                      )
                    }))}
                  </div>
                  <div className="border-1 border-gray-200"></div>
                  <Dialog>
                    <Form {...claimOppUnoppForm}>
                      <form ref={claimOppUnoppFormRef} onSubmit={claimOppUnoppForm.handleSubmit(claimOppUnopp)}>
                        <DialogTrigger asChild>
                          { claimOppAllPassed && currentClaimOpp && currentClaimOpp.player_id == playerName && <Button size="lg" disabled={state == State.ACTIVE_ASK || !claimOppAllPassed}> Make Claim </Button> }
                        </DialogTrigger>
                        <DialogContent className="sm:max-w-[425px]">
                          <DialogHeader>
                            <DialogTitle>Claim for Opponent</DialogTitle>
                            <DialogDescription>
                              Claim {halfSuitNames[currentClaimOpp.half_suit_id]}
                            </DialogDescription>
                          </DialogHeader>
                          <FormField
                            control={claimOppUnoppForm.control}
                            name="card1"
                            render={({ field }) => (
                              <FormItem>
                                <FormLabel className='mr-5'>{claimOppUnoppCardTitles.card1 || "Card 1"}: </FormLabel>
                                <Select onValueChange={field.onChange} defaultValue={field.value}>
                                  <FormControl>
                                    <SelectTrigger className="w-[180px]">
                                      <SelectValue placeholder="Player" />
                                    </SelectTrigger>
                                  </FormControl>
                                  <SelectContent>
                                    {Object.entries(players!).filter(([_, val]) => playerName && val.team != players?.[playerName].team).map(([_, val]) => {
                                      return <SelectItem value={val.id} key={val.id}>{val.id}</SelectItem>
                                    })}
                                  </SelectContent>
                                </Select>
                                <FormMessage />
                              </FormItem>
                          )} />
                          <FormField
                            control={claimOppUnoppForm.control}
                            name="card2"
                            render={({ field }) => (
                              <FormItem>
                                <FormLabel className='mr-5'>{claimOppUnoppCardTitles.card2 || "Card 2"}: </FormLabel>
                                <Select onValueChange={field.onChange} defaultValue={field.value}>
                                  <FormControl>
                                    <SelectTrigger className="w-[180px]">
                                      <SelectValue placeholder="Player" />
                                    </SelectTrigger>
                                  </FormControl>
                                  <SelectContent>
                                    {Object.entries(players!).filter(([_, val]) => playerName && val.team != players?.[playerName].team).map(([_, val]) => {
                                      return <SelectItem value={val.id} key={val.id}>{val.id}</SelectItem>
                                    })}
                                  </SelectContent>
                                </Select>
                                <FormMessage />
                              </FormItem>
                          )} />
                          <FormField
                            control={claimOppUnoppForm.control}
                            name="card3"
                            render={({ field }) => (
                              <FormItem>
                                <FormLabel className='mr-5'>{claimOppUnoppCardTitles.card3 || "Card 3"}: </FormLabel>
                                <Select onValueChange={field.onChange} defaultValue={field.value}>
                                  <FormControl>
                                    <SelectTrigger className="w-[180px]">
                                      <SelectValue placeholder="Player" />
                                    </SelectTrigger>
                                  </FormControl>
                                  <SelectContent>
                                    {Object.entries(players!).filter(([_, val]) => playerName && val.team != players?.[playerName].team).map(([_, val]) => {
                                      return <SelectItem value={val.id} key={val.id}>{val.id}</SelectItem>
                                    })}
                                  </SelectContent>
                                </Select>
                                <FormMessage />
                              </FormItem>
                          )} />
                          <FormField
                            control={claimOppUnoppForm.control}
                            name="card4"
                            render={({ field }) => (
                              <FormItem>
                                <FormLabel className='mr-5'>{claimOppUnoppCardTitles.card4 || "Card 4"}: </FormLabel>
                                <Select onValueChange={field.onChange} defaultValue={field.value}>
                                  <FormControl>
                                    <SelectTrigger className="w-[180px]">
                                      <SelectValue placeholder="Player" />
                                    </SelectTrigger>
                                  </FormControl>
                                  <SelectContent>
                                    {Object.entries(players!).filter(([_, val]) => playerName && val.team != players?.[playerName].team).map(([_, val]) => {
                                      return <SelectItem value={val.id} key={val.id}>{val.id}</SelectItem>
                                    })}
                                  </SelectContent>
                                </Select>
                                <FormMessage />
                              </FormItem>
                          )} />
                          <FormField
                            control={claimOppUnoppForm.control}
                            name="card5"
                            render={({ field }) => (
                              <FormItem>
                                <FormLabel className='mr-5'>{claimOppUnoppCardTitles.card5 || "Card 5"}: </FormLabel>
                                <Select onValueChange={field.onChange} defaultValue={field.value}>
                                  <FormControl>
                                    <SelectTrigger className="w-[180px]">
                                      <SelectValue placeholder="Player" />
                                    </SelectTrigger>
                                  </FormControl>
                                  <SelectContent>
                                    {Object.entries(players!).filter(([_, val]) => playerName && val.team != players?.[playerName].team).map(([_, val]) => {
                                      return <SelectItem value={val.id} key={val.id}>{val.id}</SelectItem>
                                    })}
                                  </SelectContent>
                                </Select>
                                <FormMessage />
                              </FormItem>
                          )} />
                          <FormField
                            control={claimOppUnoppForm.control}
                            name="card6"
                            render={({ field }) => (
                              <FormItem>
                                <FormLabel className='mr-5'>{claimOppUnoppCardTitles.card6 || "Card 6"}: </FormLabel>
                                <Select onValueChange={field.onChange} defaultValue={field.value}>
                                  <FormControl>
                                    <SelectTrigger className="w-[180px]">
                                      <SelectValue placeholder="Player" />
                                    </SelectTrigger>
                                  </FormControl>
                                  <SelectContent>
                                    {Object.entries(players!).filter(([_, val]) => playerName && val.team != players?.[playerName].team).map(([_, val]) => {
                                      return <SelectItem value={val.id} key={val.id}>{val.id}</SelectItem>
                                    })}
                                  </SelectContent>
                                </Select>
                                <FormMessage />
                              </FormItem>
                          )} />
                          <DialogFooter>
                            <DialogClose asChild>
                              <Button variant="outline" ref={claimOppUnoppFormCloseRef}>Cancel</Button>
                            </DialogClose>
                            <Button onClick={() => {
                              if (claimOppUnoppFormRef.current) {
                                claimOppUnoppFormRef.current.dispatchEvent(new Event('submit', { bubbles: true }));
                              }
                            }}>
                              Claim
                            </Button>
                          </DialogFooter>
                        </DialogContent>
                      </form>
                    </Form>
                  </Dialog>
                </div>
              </div>
            }
            <div className='flex flex-col w-full text-center'>
              <h1 className="text-lg sm:text-xl md:text-2xl lg:text-3xl font-bold inline mb-10">
                Its 
                <code className="bg-gray-300 ml-3 relative rounded px-3 py-[0.2rem] font-mono font-semibold">
                  { players![turn!].host && <Crown className='inline'/> } { turn! == playerName ? <span> {truncateString(playerName!, TRUNCATE_NAME - 6) + " "} <i>- You</i> </span> : truncateString(turn ||"Unknown", TRUNCATE_NAME) } 
                </code>'s
                turn 
              </h1>
              <div className='flex flex-col gap-4 sm:flex-row w-full justify-center sm:gap-10'>
                <Dialog>
                  <Form {...askForm}>
                    <form ref={askFormRef} onSubmit={askForm.handleSubmit(ask)}>
                      <DialogTrigger asChild>
                        <Button size="lg" disabled={turn != playerName || state != State.ACTIVE_ASK}> Ask </Button> 
                      </DialogTrigger>
                      <DialogContent className="sm:max-w-[425px]">
                        <DialogHeader>
                          <DialogTitle>Ask Question</DialogTitle>
                          <DialogDescription>
                            Select which card you want to ask to which player.
                          </DialogDescription>
                        </DialogHeader>
                        <FormField
                          control={askForm.control}
                          name="rank"
                          render={({ field }) => (
                            <FormItem>
                              <FormLabel className='mr-5'>Rank: </FormLabel>
                              <Select onValueChange={field.onChange} defaultValue={field.value}>
                                <FormControl>
                                  <SelectTrigger className="w-[180px]">
                                    <SelectValue placeholder="Rank" />
                                  </SelectTrigger>
                                </FormControl>
                                <SelectContent>
                                  {Object.entries(CardRank).map(([id, val]) => {
                                    return <SelectItem value={val} key={val}>{id[0].toUpperCase() + id.slice(1).toLowerCase()}</SelectItem>
                                  })}
                                </SelectContent>
                              </Select>
                              <FormMessage />
                            </FormItem>
                        )} />
                        <FormField
                          control={askForm.control}
                          name="suit"
                          render={({ field }) => (
                            <FormItem>
                              <FormLabel className='mr-5'>Suit: </FormLabel>
                              <Select onValueChange={field.onChange} defaultValue={field.value}>
                                <FormControl>
                                  <SelectTrigger className="w-[180px]">
                                    <SelectValue placeholder="Suit" />
                                  </SelectTrigger>
                                </FormControl>
                                <SelectContent>
                                  {Object.entries(CardSuit).filter(([_, val]) => {
                                    if (askRank == CardRank.JOKER || askRank == CardRank.CUT) return val == CardSuit.JOKER
                                    return true
                                  }).map(([_, val]) => {
                                    return <SelectItem value={val} key={val}>{val}</SelectItem>
                                  })}
                                </SelectContent>
                              </Select>
                              <FormMessage />
                            </FormItem>
                        )} />
                        <FormField
                          control={askForm.control}
                          name="to"
                          render={({ field }) => (
                            <FormItem>
                              <FormLabel className='mr-5'>Player: </FormLabel>
                              <Select onValueChange={field.onChange} defaultValue={field.value} required>
                                <FormControl>
                                  <SelectTrigger className="w-[180px]">
                                    <SelectValue placeholder="Player" />
                                  </SelectTrigger>
                                </FormControl>
                                <SelectContent>
                                  {Object.entries(players || {}).filter(([_, plyr]) => plyr.team != players![playerName!].team && plyr.num_cards! > 0).map(([_, plyr]) => {
                                    return <SelectItem value={plyr.id} key={plyr.id}>{plyr.id}</SelectItem>
                                  })}
                                </SelectContent>
                              </Select>
                              <FormMessage />
                            </FormItem>
                        )} />
                        <DialogFooter>
                          <DialogClose asChild>
                            <Button variant="outline" ref={askFormCloseRef}>Cancel</Button>
                          </DialogClose>
                          <Button onClick={() => {
                            if (askFormRef.current) {
                              askFormRef.current.dispatchEvent(new Event('submit', { bubbles: true }));
                            }
                          }}>
                            Ask
                          </Button>
                        </DialogFooter>
                      </DialogContent>
                    </form>
                  </Form>
                </Dialog>
                <Dialog>
                  <Form {...claimForm}>
                    <form ref={claimFormRef} onSubmit={claimForm.handleSubmit(claim)}>
                      <DialogTrigger asChild>
                        <Button size="lg" disabled={state != State.ACTIVE_ASK}> Claim </Button> 
                      </DialogTrigger>
                      <DialogContent className="sm:max-w-[425px]">
                        <DialogHeader>
                          <DialogTitle>Claim</DialogTitle>
                          <DialogDescription>
                            Claim a Half Suit
                          </DialogDescription>
                        </DialogHeader>
                        <FormField
                          control={claimForm.control}
                          name="half_suit"
                          render={({ field }) => (
                            <FormItem>
                              <FormLabel className='mr-5'>Half Suit: </FormLabel>
                              <Select onValueChange={field.onChange} defaultValue={field.value}>
                                <FormControl>
                                  <SelectTrigger className="w-[180px]">
                                    <SelectValue placeholder="Half Suit" />
                                  </SelectTrigger>
                                </FormControl>
                                <SelectContent>
                                  {Object.entries(HalfSuits).filter(([_, x]) => !claimedSuits.map(y => y.hs).includes(x)).map(([_, val]) => {
                                    return <SelectItem value={val.toString()} key={val}>{halfSuitNames[val]}</SelectItem>
                                  })}
                                </SelectContent>
                              </Select>
                              <FormMessage />
                            </FormItem>
                        )} />
                        <FormField
                          control={claimForm.control}
                          name="card1"
                          render={({ field }) => (
                            <FormItem>
                              <FormLabel className='mr-5'>{claimCardTitles.card1 || "Card 1"}: </FormLabel>
                              <Select onValueChange={field.onChange} defaultValue={field.value}>
                                <FormControl>
                                  <SelectTrigger className="w-[180px]">
                                    <SelectValue placeholder="Player" />
                                  </SelectTrigger>
                                </FormControl>
                                <SelectContent>
                                  {Object.entries(players!).filter(([_, val]) => playerName && val.team == players?.[playerName].team).map(([_, val]) => {
                                    return <SelectItem value={val.id} key={val.id}>{val.id}</SelectItem>
                                  })}
                                </SelectContent>
                              </Select>
                              <FormMessage />
                            </FormItem>
                        )} />
                        <FormField
                          control={claimForm.control}
                          name="card2"
                          render={({ field }) => (
                            <FormItem>
                              <FormLabel className='mr-5'>{claimCardTitles.card2 || "Card 2"}: </FormLabel>
                              <Select onValueChange={field.onChange} defaultValue={field.value}>
                                <FormControl>
                                  <SelectTrigger className="w-[180px]">
                                    <SelectValue placeholder="Player" />
                                  </SelectTrigger>
                                </FormControl>
                                <SelectContent>
                                  {Object.entries(players!).filter(([_, val]) => playerName && val.team == players?.[playerName].team).map(([_, val]) => {
                                    return <SelectItem value={val.id} key={val.id}>{val.id}</SelectItem>
                                  })}
                                </SelectContent>
                              </Select>
                              <FormMessage />
                            </FormItem>
                        )} />
                        <FormField
                          control={claimForm.control}
                          name="card3"
                          render={({ field }) => (
                            <FormItem>
                              <FormLabel className='mr-5'>{claimCardTitles.card3 || "Card 3"}: </FormLabel>
                              <Select onValueChange={field.onChange} defaultValue={field.value}>
                                <FormControl>
                                  <SelectTrigger className="w-[180px]">
                                    <SelectValue placeholder="Player" />
                                  </SelectTrigger>
                                </FormControl>
                                <SelectContent>
                                  {Object.entries(players!).filter(([_, val]) => playerName && val.team == players?.[playerName].team).map(([_, val]) => {
                                    return <SelectItem value={val.id} key={val.id}>{val.id}</SelectItem>
                                  })}
                                </SelectContent>
                              </Select>
                              <FormMessage />
                            </FormItem>
                        )} />
                        <FormField
                          control={claimForm.control}
                          name="card4"
                          render={({ field }) => (
                            <FormItem>
                              <FormLabel className='mr-5'>{claimCardTitles.card4 || "Card 4"}: </FormLabel>
                              <Select onValueChange={field.onChange} defaultValue={field.value}>
                                <FormControl>
                                  <SelectTrigger className="w-[180px]">
                                    <SelectValue placeholder="Player" />
                                  </SelectTrigger>
                                </FormControl>
                                <SelectContent>
                                  {Object.entries(players!).filter(([_, val]) => playerName && val.team == players?.[playerName].team).map(([_, val]) => {
                                    return <SelectItem value={val.id} key={val.id}>{val.id}</SelectItem>
                                  })}
                                </SelectContent>
                              </Select>
                              <FormMessage />
                            </FormItem>
                        )} />
                        <FormField
                          control={claimForm.control}
                          name="card5"
                          render={({ field }) => (
                            <FormItem>
                              <FormLabel className='mr-5'>{claimCardTitles.card5 || "Card 5"}: </FormLabel>
                              <Select onValueChange={field.onChange} defaultValue={field.value}>
                                <FormControl>
                                  <SelectTrigger className="w-[180px]">
                                    <SelectValue placeholder="Player" />
                                  </SelectTrigger>
                                </FormControl>
                                <SelectContent>
                                  {Object.entries(players!).filter(([_, val]) => playerName && val.team == players?.[playerName].team).map(([_, val]) => {
                                    return <SelectItem value={val.id} key={val.id}>{val.id}</SelectItem>
                                  })}
                                </SelectContent>
                              </Select>
                              <FormMessage />
                            </FormItem>
                        )} />
                        <FormField
                          control={claimForm.control}
                          name="card6"
                          render={({ field }) => (
                            <FormItem>
                              <FormLabel className='mr-5'>{claimCardTitles.card6 || "Card 6"}: </FormLabel>
                              <Select onValueChange={field.onChange} defaultValue={field.value}>
                                <FormControl>
                                  <SelectTrigger className="w-[180px]">
                                    <SelectValue placeholder="Player" />
                                  </SelectTrigger>
                                </FormControl>
                                <SelectContent>
                                  {Object.entries(players!).filter(([_, val]) => playerName && val.team == players?.[playerName].team).map(([_, val]) => {
                                    return <SelectItem value={val.id} key={val.id}>{val.id}</SelectItem>
                                  })}
                                </SelectContent>
                              </Select>
                              <FormMessage />
                            </FormItem>
                        )} />
                        <DialogFooter>
                          <DialogClose asChild>
                            <Button variant="outline" ref={claimFormCloseRef}>Cancel</Button>
                          </DialogClose>
                          <Button onClick={() => {
                            if (claimFormRef.current) {
                              claimFormRef.current.dispatchEvent(new Event('submit', { bubbles: true }));
                            }
                          }}>
                            Claim
                          </Button>
                        </DialogFooter>
                      </DialogContent>
                    </form>
                  </Form>
                </Dialog>
                <Dialog>
                  <Form {...claimOppForm}>
                    <form ref={claimOppFormRef} onSubmit={claimOppForm.handleSubmit(claimOpp)}>
                      <DialogTrigger asChild>
                        <Button size="lg" disabled={state != State.ACTIVE_ASK}> Claim for Opponent </Button> 
                      </DialogTrigger>
                      <DialogContent className="sm:max-w-[425px]">
                        <DialogHeader>
                          <DialogTitle>Claim for Opponent</DialogTitle>
                          <DialogDescription>
                            Claim a Half Suit
                          </DialogDescription>
                        </DialogHeader>
                        <FormField
                          control={claimOppForm.control}
                          name="half_suit"
                          render={({ field }) => (
                            <FormItem>
                              <FormLabel className='mr-5'>Half Suit: </FormLabel>
                              <Select onValueChange={field.onChange} defaultValue={field.value}>
                                <FormControl>
                                  <SelectTrigger className="w-[180px]">
                                    <SelectValue placeholder="Half Suit" />
                                  </SelectTrigger>
                                </FormControl>
                                <SelectContent>
                                  {Object.entries(HalfSuits).filter(([_, x]) => !claimedSuits.map(y => y.hs).includes(x)).map(([_, val]) => {
                                    return <SelectItem value={val.toString()} key={val}>{halfSuitNames[val]}</SelectItem>
                                  })}
                                </SelectContent>
                              </Select>
                              <FormMessage />
                            </FormItem>
                        )} />
                        <DialogFooter>
                          <DialogClose asChild>
                            <Button variant="outline" ref={claimOppFormCloseRef}>Cancel</Button>
                          </DialogClose>
                          <Button onClick={() => {
                            if (claimOppFormRef.current) {
                              claimOppFormRef.current.dispatchEvent(new Event('submit', { bubbles: true }));
                            }
                          }}>
                            Claim
                          </Button>
                        </DialogFooter>
                      </DialogContent>
                    </form>
                  </Form>
                </Dialog>
              </div>
            </div>

            <div className='flex flex-col w-full gap-10'>
              <h1 className='text-lg sm:text-xl md:text-2xl lg:text-3xl font-bold'>Your Cards:</h1>
              <div id="cards" className='w-full'>
                {Object.entries(hand).map(([hs, cs]) => {
                  return (
                    <div id={hs.toString()} key={hs.toString()} className='relative card-suit' data-cnt-hs={cs.length}>
                      {cs.map((c, idx) => {
                        return <CardComponent key={c.id} card={c} cnt_hs={cs.length} idx_hs={idx} />
                      })}
                    </div>
                  )
                })}
              </div>
            </div>

            <div className='gap-20 lg:gap-10 grid grid-cols-1 xl:grid-cols-2 2xl:grid-cols-3'>
              <div className='flex-1 flex flex-col gap-10'>
                <h1 className='text-lg sm:text-xl md:text-2xl lg:text-3xl font-bold'>Ask History:</h1>
                <div className="flex flex-col gap-2 w-full px-2">
                  <div className="flex flex-col text-sm sm:text-base">
                    {askDefault(askRecord.map((ask, i) => getAskElement(ask, i + 1)))}
                  </div>
                </div>
              </div>

              <div className='flex-1 flex flex-col gap-10'>
                <h1 className='text-lg sm:text-xl md:text-2xl lg:text-3xl font-bold'>Claims:</h1>
                <div className="flex flex-col relative w-full sm:flex-row xl:w-auto gap-4 xl:max-w-2xl">
                  <div className="flex flex-col gap-2 w-full px-2">
                    <div className='flex flex-row justify-between'>
                      <h1 className="font-semibold">Team 1</h1>
                    </div>
                    <div className="flex flex-col text-sm sm:text-base">
                      {suitDefault(claimedSuits.filter((hs) => hs.to == TeamID.TEAM_1).map((hs, i) => getClaimedSuitElement(hs.hs, i + 1)))}
                    </div>
                  </div>
                  <div className="sm:absolute sm:left-[50%] sm:top-0 sm:bottom-0 border-1 border-gray-200"></div>
                  <div className="flex flex-col gap-2 w-full px-2">
                    <div className='flex flex-row justify-between'>
                      <h1 className="font-semibold">Team 2</h1>
                    </div>
                    <div className="flex flex-col text-sm sm:text-base">
                      {suitDefault(claimedSuits.filter((hs) => hs.to == TeamID.TEAM_2).map((hs, i) => getClaimedSuitElement(hs.hs, i + 1)))}
                    </div>
                  </div>
                </div>
              </div>

              <div className='flex-1 flex flex-col gap-10'>
                <h1 className='text-lg sm:text-xl md:text-2xl lg:text-3xl font-bold'>Team Info:</h1>
                <div className="flex flex-col relative w-full sm:flex-row xl:w-auto gap-4 xl:max-w-2xl">
                  <div className="flex flex-col gap-2 w-full px-2">
                    <div className='flex flex-row justify-between'>
                      <h1 className="font-semibold">Team 1</h1>
                      <Badge variant="secondary" className='bg-fuchsia-100'><span className='text-sm'>{team1Score}</span></Badge>
                    </div>
                    <div className="flex flex-col text-sm sm:text-base">
                      {teamDefault(Object.entries(players!).filter(([_, plyr]) => plyr.team == TeamID.TEAM_1).map((([_, plyr]) => {
                        return plyrRow(plyr)
                      })))}
                    </div>
                  </div>
                  <div className="sm:absolute sm:left-[50%] sm:top-0 sm:bottom-0 border-1 border-gray-200"></div>
                  <div className="flex flex-col gap-2 w-full px-2">
                    <div className='flex flex-row justify-between'>
                      <h1 className="font-semibold">Team 2</h1>
                      <Badge variant="secondary" className='bg-orange-100'><span className='text-sm'>{team2Score}</span></Badge>
                    </div>
                    <div className="flex flex-col text-sm sm:text-base">
                      {teamDefault(Object.entries(players!).filter(([_, plyr]) => plyr.team == TeamID.TEAM_2).map((([_, plyr]) => {
                        return plyrRow(plyr)
                      })))}
                    </div>
                  </div>
                </div>
              </div>

            </div>
          </div>
        </div>
      }
    </div>
  )
}
