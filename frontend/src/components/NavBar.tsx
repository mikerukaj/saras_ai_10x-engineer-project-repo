import { NavLink } from 'react-router-dom'

const links = [
  { to: '/', label: 'Prompts', end: true },
  { to: '/collections', label: 'Collections', end: false },
  { to: '/tags', label: 'Tags', end: false },
]

/** Top navigation links: Prompts, Collections, Tags. */
export function NavBar() {
  return (
    <nav className="border-b border-slate-200 bg-white">
      <div className="mx-auto flex max-w-4xl items-center gap-1 px-4 py-3 sm:px-6">
        <span className="mr-4 text-sm font-semibold text-slate-900">PromptLab</span>
        {links.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            end={link.end}
            className={({ isActive }) =>
              `rounded-md px-3 py-1.5 text-sm font-medium ${
                isActive ? 'bg-blue-50 text-blue-700' : 'text-slate-600 hover:bg-slate-50'
              }`
            }
          >
            {link.label}
          </NavLink>
        ))}
      </div>
    </nav>
  )
}
