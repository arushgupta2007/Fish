import * as z from 'zod'
import { useForm, type SubmitHandler } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "../ui/card"
import { Label } from "../ui/label"
import { Input } from "../ui/input"
import { Button } from "../ui/button"
import { FishSymbol, Loader2Icon } from "lucide-react"
import { GAME_ID_LENGTH, MAX_NAME_LENGTH } from "@/utils/constants"

type RegisterProps = {
  plyr_name_error: boolean,
  loading: boolean,
  submit(game_id: string, plyr_name: string): void
}

const inputSchema = z.object({
  game_id: z.string().length(GAME_ID_LENGTH, { error: `Game ID should have length ${GAME_ID_LENGTH}` }).regex(/^[a-z]+$/, {
    error: "Invalid Game ID"
  }),
  player_name: z.string()
                .min(1, { error: "Player Name should be non-empty" })
                .max(MAX_NAME_LENGTH, { error: "Player Name too big" })
                .regex(/^[a-zA-Z0-9]+$/, {
                  error: "Player Name must consist of only alphanumeric characters"
                })
})
type UserInput = z.infer<typeof inputSchema>

export default function Register({ plyr_name_error, loading, submit }: RegisterProps) {
  const { register, handleSubmit, formState: { errors }, } = useForm<UserInput>({
    resolver: zodResolver(inputSchema)
  })

  const onSubmit = (data: SubmitHandler<UserInput>) => {
    // @ts-ignore
    submit(data.game_id, data.player_name)
  }

  return (
    <div className="w-full h-full flex items-center justify-center p-5 sm:p-10 md:p-20 bg-gray-100">
      <Card className="md:min-w-sm">
        <CardHeader>
          <CardTitle className="text-xl">Start Playing!</CardTitle>
          <CardDescription>Enjoy the amazing game of FISH</CardDescription>
        </CardHeader>
        <form onSubmit={handleSubmit(onSubmit)}>
          <CardContent>
            <div className="flex flex-col gap-6">
              <div className="flex flex-col gap-2">
                <Label htmlFor="gameIdInp">Game ID</Label>
                <Input id="gameIdInp" type="text" placeholder="asdfghjkl" required {...register('game_id')} />
                <span className='text-xs text-gray-500'>Lowercase alphabet string of length {GAME_ID_LENGTH}</span>
                { errors.game_id && <span className="text-sm text-red-500">{ errors.game_id.message }</span> }
              </div>

              <div className="flex flex-col gap-2">
                <Label htmlFor="gameIdInp">Player Name</Label>
                <Input id="gameIdInp" type="text" placeholder="HarryPotter" required {...register('player_name')} />
                <span className='text-xs text-gray-500'>Alphanumeric string</span>
                { errors.player_name && <span className="text-sm text-red-500">{ errors.player_name.message }</span> }
                { plyr_name_error && <span className="text-sm text-red-500">Player with this name already exists</span> }
              </div>
            </div>
          </CardContent>

          <CardFooter className="mt-8">
            { loading ?
              <Button type="submit" className="w-full" disabled> <Loader2Icon className='animate-spin' /> Fish! </Button>
              : <Button type="submit" className="w-full"> <FishSymbol /> Fish! </Button> }
          </CardFooter>
        </form>
      </Card>
    </div>
  )
}
