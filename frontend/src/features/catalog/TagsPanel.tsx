import { useState } from 'react';
import { Pencil, Plus } from 'lucide-react';
import { useResource } from '../../api/queries';
import type { Page, Role, Tag } from '../../api/types';
import { Empty, ErrorNotice, Loading } from '../../components/Feedback';
import { Pagination } from '../../components/Pagination';
import { canManage } from '../../lib/format';
import { TagDialog } from './TagDialog';

export function TagsPanel({ workspace, role }: { workspace: string; role: Role }) {
  const [editing, setEditing] = useState<Tag | 'new' | null>(null);
  const [offset, setOffset] = useState(0);
  const query = useResource<Page<Tag>>(`/workspaces/${workspace}/tags?limit=12&offset=${offset}`);
  return (
    <section className="card settings-card">
      <header className="section-heading">
        <div>
          <h2>Теги пространства</h2>
          <p>Помогают быстрее находить нужные задачи</p>
        </div>
        {canManage(role) && (
          <button className="secondary" onClick={() => setEditing('new')}>
            <Plus size={16} />
            Добавить тег
          </button>
        )}
      </header>
      {query.isPending ? (
        <Loading />
      ) : query.error ? (
        <ErrorNotice error={query.error} retry={() => void query.refetch()} />
      ) : (
        <>
          {query.data.items.length ? (
            <div className="tag-catalog">
              {query.data.items.map((tag) => (
                <div className="tag-catalog-item" key={tag.id}>
                  <i style={{ backgroundColor: tag.color ?? '#8271f5' }} />
                  <strong>{tag.name}</strong>
                  {canManage(role) && (
                    <button
                      className="icon-button"
                      aria-label={`Изменить тег ${tag.name}`}
                      onClick={() => setEditing(tag)}
                    >
                      <Pencil size={15} />
                    </button>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <Empty
              title="Наведём порядок"
              text="Добавьте теги вроде «Дизайн», «Разработка» или «Важно»."
            />
          )}
          <Pagination offset={offset} limit={12} total={query.data.total} onChange={setOffset} />
        </>
      )}
      {editing && (
        <TagDialog
          workspace={workspace}
          tag={editing === 'new' ? undefined : editing}
          onClose={() => {
            setEditing(null);
            setOffset(0);
          }}
        />
      )}
    </section>
  );
}
