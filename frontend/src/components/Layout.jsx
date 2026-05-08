export default function Layout({ children }) {
  return (
    <div
      className="min-h-screen w-full"
      style={{
        background: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #06b6d4 100%)',
      }}
    >
      <header className="flex items-center justify-between px-6 py-4">
        <span className="text-white font-extrabold text-xl tracking-tight">MyStok</span>
      </header>
      <main className="px-4 pb-12 max-w-lg mx-auto">{children}</main>
    </div>
  )
}
