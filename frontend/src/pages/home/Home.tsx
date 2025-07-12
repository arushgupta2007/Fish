import { NavLink } from 'react-router'
import './Home.css'
import { Button } from '@/components/ui/button'

export default function Home() {
  return (
    <div className="w-[100vw] h-[100vh] flex items-center justify-center">
      <NavLink to="/game">
        <Button>Start Fishing!</Button>
      </NavLink>
    </div>
  )
}
