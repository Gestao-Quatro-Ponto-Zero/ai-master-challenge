import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Home from './pages/Home'
import SellerPage from './pages/SellerPage'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,
      retry: 1,
    },
  },
})

function Placeholder({ name }: { name: string }) {
  return (
    <div className="flex items-center justify-center h-64 text-muted-foreground text-sm">
      {name} — em construção
    </div>
  )
}

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Navigate to="/home" replace />} />
          <Route path="/home"               element={<Home />} />
          <Route path="/sellers/:name"      element={<SellerPage />} />
          <Route path="/macro"              element={<Placeholder name="Macro" />} />
          <Route path="/deals"              element={<Placeholder name="Deals" />} />
          <Route path="/accounts"           element={<Placeholder name="Accounts" />} />
          <Route path="/products"           element={<Placeholder name="Products" />} />
          <Route path="/sellers"            element={<Placeholder name="Sellers" />} />
          <Route path="/analysis/actions"   element={<Placeholder name="Action Analysis" />} />
          <Route path="/analysis/transfers" element={<Placeholder name="Transfer Analysis" />} />
          <Route path="*"                   element={<Navigate to="/home" replace />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
