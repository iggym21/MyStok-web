export default function CertaintyBadge({ certainty }) {
  return (
    <div
      className="text-center px-4 py-3 rounded-xl"
      style={{
        background: 'rgba(255,255,255,0.2)',
        border: '1px solid rgba(255,255,255,0.35)',
      }}
    >
      <div className="text-white font-extrabold text-2xl leading-none">
        {Math.round(certainty)}%
      </div>
      <div className="text-white/65 text-[9px] uppercase tracking-widest mt-1">
        Certainty
      </div>
    </div>
  )
}
