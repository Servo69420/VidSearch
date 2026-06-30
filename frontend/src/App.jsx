import { useHashRouter } from './router'
import WatchPage from './pages/dashboard/WatchPage'

import './styles/variables.css'
import './styles/global.css'

const ROUTES = [
  { path: '/', component: WatchPage },
  { path: '/watch', component: WatchPage },
  { path: '/watch/:id', component: WatchPage },
]

export default function App() {
  const { current, params } = useHashRouter(ROUTES)
  const Page = current.component

  return (
    <div className="app app-barebones">
      <main className="main-content barebones-main">
        <Page params={params} />
      </main>
    </div>
  )
}
