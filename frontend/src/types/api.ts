import { MAX_ID_LENGTH, MAX_NAME_LENGTH } from "@/utils/constants";
import * as z from "zod"
import { ApiEvent, TeamID } from "./enums";

export const TeamSchema = z.enum(TeamID)

export const PlayerSchema = z.object({
  id: z.string().min(1).max(MAX_ID_LENGTH),
  name: z.string().min(1).max(MAX_NAME_LENGTH),
  team: TeamSchema,
  host: z.boolean().optional(),
  num_cards: z.int().min(0).max(54).optional(),
  me: z.boolean().optional()
})
export type Player = z.infer<typeof PlayerSchema>

export const ApiMessageSchema = z.looseObject({
  type: z.enum(ApiEvent),
})
export type ApiMessage = z.infer<typeof ApiMessageSchema>

export const ApiMessageNewConnectionSchema = z.object({
  players: z.array(PlayerSchema).optional(),
})
export type ApiMessageNewConnection = z.infer<typeof ApiMessageNewConnectionSchema>

export const ApiMessagePlayerJoinedSchema = PlayerSchema
export type ApiMessagePlayerJoined = z.infer<typeof ApiMessagePlayerJoinedSchema>

export const ApiMessagePlayerLeftSchema = z.object({
  id: z.string().min(1).max(MAX_ID_LENGTH),
  new_host: z.string().optional()
})
export type ApiMessagePlayerLeft = z.infer<typeof ApiMessagePlayerLeftSchema>

export const ApiMessageHandSchema = z.object({
  hand: z.array(z.string())
})
export type ApiMessageHand = z.infer<typeof ApiMessageHandSchema>

export const ApiMessageGameStartSchema = z.object({
  starting_player: z.string(),
  num_cards: z.record(z.string(), z.int())
})
export type ApiMessageGameStart = z.infer<typeof ApiMessageGameStartSchema>

export const ApiMessageAskSchema = z.object({
  from_id: z.string(),
  to_id: z.string(),
  card_id: z.string(),
  success: z.boolean(),
  turn: z.string()
})
export type ApiMessageAsk = z.infer<typeof ApiMessageAskSchema>

export const ApiMessageClaimSchema = z.object({
  player_id: z.string(),
  half_suit_id: z.int().min(0).max(8),
  assignment: z.record(z.string(), z.string()),
  success: z.boolean(),
  point_to: TeamSchema,
  turn: z.string(),
  num_cards: z.record(z.string(), z.int())
})
export type ApiMessageClaim = z.infer<typeof ApiMessageClaimSchema>

export const ApiMessageClaimOppSchema = z.object({
  player_id: z.string(),
  team: z.enum(TeamID),
  half_suit_id: z.int().min(0).max(8),
})
export type ApiMessageClaimOpp = z.infer<typeof ApiMessageClaimOppSchema>

export const ApiMessageClaimOppPassSchema = z.object({
  player_id: z.string(),
  all_passed: z.boolean()
})
export type ApiMessageClaimOppPass = z.infer<typeof ApiMessageClaimOppPassSchema>

export const ApiMessageGameFinishedSchema = z.object({
  winning_team: z.enum(TeamID),
  final_scores: z.object({
    team1: z.int(),
    team2: z.int(),
  })
})
export type ApiMessageGameFinished = z.infer<typeof ApiMessageGameFinishedSchema>

export const ApiMessageErrorSchema = z.object({
  type: z.enum(ApiEvent).optional(),
  error: z.string()
})
export type ApiMessageError = z.infer<typeof ApiMessageErrorSchema>
