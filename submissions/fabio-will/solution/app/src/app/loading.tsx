/** Route skeleton. Pages are prefetched, so this only shows when a page was not fetched ahead (slow or flaky network). */
export default function Loading() {
  return (
    <div role="status" aria-label="Carregando a página">
      <section className="hero">
        <div className="wrap loading-hero">
          <span className="bone loading-eyebrow" />
          <span className="bone loading-title" />
          <span className="bone loading-title short" />
          <span className="bone loading-lede" />
          <span className="bone loading-lede short" />
        </div>
      </section>
      <section className="section">
        <div className="wrap grid-3">
          {[0, 1, 2].map((i) => (
            <div key={i} className="card">
              <span className="bone loading-number" />
              <span className="bone loading-line" />
              <span className="bone loading-line short" />
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}
