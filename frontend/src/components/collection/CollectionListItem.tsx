import type { Collection } from '../../api/client'
import { Button } from '../Button'
import { Card } from '../Card'

interface CollectionListItemProps {
  collection: Collection
  onDelete: () => void
}

/** One row on CollectionsPage: name, description, delete action. */
export function CollectionListItem({ collection, onDelete }: CollectionListItemProps) {
  return (
    <Card className="flex items-center justify-between gap-3">
      <div>
        <h2 className="text-sm font-semibold text-slate-900">{collection.name}</h2>
        {collection.description && <p className="mt-0.5 text-sm text-slate-600">{collection.description}</p>}
      </div>
      <Button variant="danger" onClick={onDelete}>
        Delete
      </Button>
    </Card>
  )
}
