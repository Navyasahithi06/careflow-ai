interface EmptyStateProps {
  title: string
  description: string
  icon?: string
}

export default function EmptyState({ title, description, icon = '📋' }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-4">
      <span className="text-5xl mb-4">{icon}</span>
      <h3 className="text-lg font-semibold text-gray-900 mb-2">{title}</h3>
      <p className="text-gray-500 text-center max-w-md">{description}</p>
      <p className="mt-4 text-sm text-gray-400 border border-dashed border-gray-300 rounded-lg px-4 py-2">
        Coming in Phase 2
      </p>
    </div>
  )
}
