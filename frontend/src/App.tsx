import './App.css'

function App() {
  return (
    <main className="app-shell">
      <section className="card">
        <p className="eyebrow">Loyalty App</p>
        <h1>Points Exchange & Redemption</h1>
        <p className="summary">
          A clean frontend foundation for checking balances, exchanging partner
          points, and redeeming rewards in one place.
        </p>
        <div className="pill-row" aria-label="planned modules">
          <span>Balances</span>
          <span>Exchange</span>
          <span>Redemptions</span>
        </div>
      </section>
    </main>
  )
}

export default App
