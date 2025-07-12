import type { Card } from "@/types/card"
import './card.css'
import S2 from '@/assets/cards/2S.svg?react'
import D2 from '@/assets/cards/2D.svg?react'
import H2 from '@/assets/cards/2H.svg?react'
import C2 from '@/assets/cards/2C.svg?react'
import S3 from '@/assets/cards/3S.svg?react'
import D3 from '@/assets/cards/3D.svg?react'
import H3 from '@/assets/cards/3H.svg?react'
import C3 from '@/assets/cards/3C.svg?react'
import S4 from '@/assets/cards/4S.svg?react'
import D4 from '@/assets/cards/4D.svg?react'
import H4 from '@/assets/cards/4H.svg?react'
import C4 from '@/assets/cards/4C.svg?react'
import S5 from '@/assets/cards/5S.svg?react'
import D5 from '@/assets/cards/5D.svg?react'
import H5 from '@/assets/cards/5H.svg?react'
import C5 from '@/assets/cards/5C.svg?react'
import S6 from '@/assets/cards/6S.svg?react'
import D6 from '@/assets/cards/6D.svg?react'
import H6 from '@/assets/cards/6H.svg?react'
import C6 from '@/assets/cards/6C.svg?react'
import S7 from '@/assets/cards/7S.svg?react'
import D7 from '@/assets/cards/7D.svg?react'
import H7 from '@/assets/cards/7H.svg?react'
import C7 from '@/assets/cards/7C.svg?react'
import S8 from '@/assets/cards/8S.svg?react'
import D8 from '@/assets/cards/8D.svg?react'
import H8 from '@/assets/cards/8H.svg?react'
import C8 from '@/assets/cards/8C.svg?react'
import S9 from '@/assets/cards/9S.svg?react'
import D9 from '@/assets/cards/9D.svg?react'
import H9 from '@/assets/cards/9H.svg?react'
import C9 from '@/assets/cards/9C.svg?react'
import S10 from '@/assets/cards/10S.svg?react'
import D10 from '@/assets/cards/10D.svg?react'
import H10 from '@/assets/cards/10H.svg?react'
import C10 from '@/assets/cards/10C.svg?react'
import SJ from '@/assets/cards/JS.svg?react'
import DJ from '@/assets/cards/JD.svg?react'
import HJ from '@/assets/cards/JH.svg?react'
import CJ from '@/assets/cards/JC.svg?react'
import SQ from '@/assets/cards/QS.svg?react'
import DQ from '@/assets/cards/QD.svg?react'
import HQ from '@/assets/cards/QH.svg?react'
import CQ from '@/assets/cards/QC.svg?react'
import SK from '@/assets/cards/KS.svg?react'
import DK from '@/assets/cards/KD.svg?react'
import HK from '@/assets/cards/KH.svg?react'
import CK from '@/assets/cards/KC.svg?react'
import SA from '@/assets/cards/AS.svg?react'
import DA from '@/assets/cards/AD.svg?react'
import HA from '@/assets/cards/AH.svg?react'
import CA from '@/assets/cards/AC.svg?react'
import JJoker from '@/assets/cards/JokerJ.svg?react'
import JCut from '@/assets/cards/CutJ.svg?react'

type CardProps = {
  card: Card,
  cnt_hs: number,
  idx_hs: number
}

export default function CardComponent({ card, idx_hs }: CardProps) {

  const getCard = () => {
    switch (card.id) {
        case "2S": {
          return <S2 preserveAspectRatio="xMinYMin meet"/>
        }
        case "2D": {
          return <D2 preserveAspectRatio="xMinYMin meet" />
        }
        case "2H": {
          return <H2 preserveAspectRatio="xMinYMin meet" />
        }
        case "2C": {
          return <C2 preserveAspectRatio="xMinYMin meet" />
        }
        case "3S": {
          return <S3 preserveAspectRatio="xMinYMin meet" />
        }
        case "3D": {
          return <D3 preserveAspectRatio="xMinYMin meet" />
        }
        case "3H": {
          return <H3 preserveAspectRatio="xMinYMin meet" />
        }
        case "3C": {
          return <C3 preserveAspectRatio="xMinYMin meet" />
        }
        case "4S": {
          return <S4 preserveAspectRatio="xMinYMin meet" />
        }
        case "4D": {
          return <D4 preserveAspectRatio="xMinYMin meet" />
        }
        case "4H": {
          return <H4 preserveAspectRatio="xMinYMin meet" />
        }
        case "4C": {
          return <C4 preserveAspectRatio="xMinYMin meet" />
        }
        case "5S": {
          return <S5 preserveAspectRatio="xMinYMin meet" />
        }
        case "5D": {
          return <D5 preserveAspectRatio="xMinYMin meet" />
        }
        case "5H": {
          return <H5 preserveAspectRatio="xMinYMin meet" />
        }
        case "5C": {
          return <C5 preserveAspectRatio="xMinYMin meet" />
        }
        case "6S": {
          return <S6 preserveAspectRatio="xMinYMin meet" />
        }
        case "6D": {
          return <D6 preserveAspectRatio="xMinYMin meet" />
        }
        case "6H": {
          return <H6 preserveAspectRatio="xMinYMin meet" />
        }
        case "6C": {
          return <C6 preserveAspectRatio="xMinYMin meet" />
        }
        case "7S": {
          return <S7 preserveAspectRatio="xMinYMin meet" />
        }
        case "7D": {
          return <D7 preserveAspectRatio="xMinYMin meet" />
        }
        case "7H": {
          return <H7 preserveAspectRatio="xMinYMin meet" />
        }
        case "7C": {
          return <C7 preserveAspectRatio="xMinYMin meet" />
        }
        case "8S": {
          return <S8 preserveAspectRatio="xMinYMin meet" />
        }
        case "8D": {
          return <D8 preserveAspectRatio="xMinYMin meet" />
        }
        case "8H": {
          return <H8 preserveAspectRatio="xMinYMin meet" />
        }
        case "8C": {
          return <C8 preserveAspectRatio="xMinYMin meet" />
        }
        case "9S": {
          return <S9 preserveAspectRatio="xMinYMin meet" />
        }
        case "9D": {
          return <D9 preserveAspectRatio="xMinYMin meet" />
        }
        case "9H": {
          return <H9 preserveAspectRatio="xMinYMin meet" />
        }
        case "9C": {
          return <C9 preserveAspectRatio="xMinYMin meet" />
        }
        case "10S": {
          return <S10 preserveAspectRatio="xMinYMin meet" />
        }
        case "10D": {
          return <D10 preserveAspectRatio="xMinYMin meet" />
        }
        case "10H": {
          return <H10 preserveAspectRatio="xMinYMin meet" />
        }
        case "10C": {
          return <C10 preserveAspectRatio="xMinYMin meet" />
        }
        case "JS": {
          return <SJ preserveAspectRatio="xMinYMin meet" />
        }
        case "JD": {
          return <DJ preserveAspectRatio="xMinYMin meet" />
        }
        case "JH": {
          return <HJ preserveAspectRatio="xMinYMin meet" />
        }
        case "JC": {
          return <CJ preserveAspectRatio="xMinYMin meet" />
        }
        case "QS": {
          return <SQ preserveAspectRatio="xMinYMin meet" />
        }
        case "QD": {
          return <DQ preserveAspectRatio="xMinYMin meet" />
        }
        case "QH": {
          return <HQ preserveAspectRatio="xMinYMin meet" />
        }
        case "QC": {
          return <CQ preserveAspectRatio="xMinYMin meet" />
        }
        case "KS": {
          return <SK preserveAspectRatio="xMinYMin meet" />
        }
        case "KD": {
          return <DK preserveAspectRatio="xMinYMin meet" />
        }
        case "KH": {
          return <HK preserveAspectRatio="xMinYMin meet" />
        }
        case "KC": {
          return <CK preserveAspectRatio="xMinYMin meet" />
        }
        case "AS": {
          return <SA preserveAspectRatio="xMinYMin meet" />
        }
        case "AD": {
          return <DA preserveAspectRatio="xMinYMin meet" />
        }
        case "AH": {
          return <HA preserveAspectRatio="xMinYMin meet" />
        }
        case "AC": {
          return <CA preserveAspectRatio="xMinYMin meet" />
        }
        case "JokerJ": {
          return <JJoker preserveAspectRatio="xMinYMin meet" />
        }
        case "CutJ": {
          return <JCut preserveAspectRatio="xMinYMin meet" />
        }
    }
  }

  return (
    <div className="drop-shadow-lg absolute card" data-idx={idx_hs}>
      {getCard()}
    </div>
  )
}
