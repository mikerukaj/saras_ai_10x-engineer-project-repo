import { BrowserRouter, Route, Routes } from 'react-router-dom'

import { AppShell } from './components/AppShell'
import { CollectionsPage } from './pages/CollectionsPage'
import { NotFoundPage } from './pages/NotFoundPage'
import { PromptCreatePage } from './pages/PromptCreatePage'
import { PromptDetailPage } from './pages/PromptDetailPage'
import { PromptEditPage } from './pages/PromptEditPage'
import { PromptListPage } from './pages/PromptListPage'
import { TagsPage } from './pages/TagsPage'

/** App routing shell: every route renders inside AppShell's nav + content
 * layout. Route list matches specs/frontend.md's Screens table. */
function App() {
  return (
    <BrowserRouter>
      <AppShell>
        <Routes>
          <Route path="/" element={<PromptListPage />} />
          <Route path="/prompts/new" element={<PromptCreatePage />} />
          <Route path="/prompts/:promptId" element={<PromptDetailPage />} />
          <Route path="/prompts/:promptId/edit" element={<PromptEditPage />} />
          <Route path="/collections" element={<CollectionsPage />} />
          <Route path="/tags" element={<TagsPage />} />
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </AppShell>
    </BrowserRouter>
  )
}

export default App
