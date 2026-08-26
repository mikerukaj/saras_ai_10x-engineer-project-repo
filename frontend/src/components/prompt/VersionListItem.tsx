import type { PromptVersion } from '../../api/client'

interface VersionListItemProps {
  version: PromptVersion
  onView: () => void
}

/** One entry in the version history list: number, timestamp, label. */
export function VersionListItem({ version, onView }: VersionListItemProps) {
  return (
    <li>
      <button
        type="button"
        onClick={onView}
        className="flex w-full items-center justify-between rounded-md px-3 py-2 text-left text-sm hover:bg-slate-50"
      >
        <span className="font-medium text-slate-800">
          Version {version.version_number}
          {version.label && <span className="ml-2 font-normal text-slate-500">— {version.label}</span>}
        </span>
        <time className="text-xs text-slate-400" dateTime={version.created_at}>
          {new Date(version.created_at).toLocaleString()}
        </time>
      </button>
    </li>
  )
}
