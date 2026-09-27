import { useState } from 'react';
import { Plus, ShieldCheck } from 'lucide-react';
import type { Member, Page, Role, User } from '../../api/types';
import { useResource } from '../../api/queries';
import { ErrorNotice, Loading } from '../../components/Feedback';
import { Pagination } from '../../components/Pagination';
import { initials, roles } from '../../lib/format';
import { MemberDialog } from './MemberDialog';

export function TeamPage({ workspace, user, role }: { workspace: string; user: User; role: Role }) {
  const [offset, setOffset] = useState(0);
  const [editing, setEditing] = useState<Member | 'new' | null>(null);
  const query = useResource<Page<Member>>(
    `/workspaces/${workspace}/members?limit=12&offset=${offset}`,
  );
  return (
    <>
      <header className="page-heading">
        <div>
          <span className="eyebrow">ЛУЧШЕ ПОЛУЧАЕТСЯ ВМЕСТЕ</span>
          <h1>Команда</h1>
          <p>Люди, с которыми идеи становятся результатами.</p>
        </div>
        {role === 'Admin' && (
          <button className="primary" onClick={() => setEditing('new')}>
            <Plus size={18} />
            Добавить участника
          </button>
        )}
      </header>
      <section className="card">
        {query.isPending ? (
          <Loading />
        ) : query.error ? (
          <ErrorNotice error={query.error} retry={() => void query.refetch()} />
        ) : (
          <>
            <div className="member-list">
              {query.data.items.map((member) => (
                <div className="member-row" key={member.user_id}>
                  <span className="avatar">{initials(member.name)}</span>
                  <strong>
                    {member.name}
                    {member.user_id === user.id && <small> · это вы</small>}
                  </strong>
                  <span className="member-role">
                    <ShieldCheck size={15} />
                    {roles[member.role]}
                  </span>
                  {role === 'Admin' && (
                    <button
                      className="text-button"
                      onClick={() => setEditing(member)}
                      aria-label={`Изменить права ${member.name}`}
                    >
                      Изменить
                    </button>
                  )}
                </div>
              ))}
            </div>
            <Pagination offset={offset} limit={12} total={query.data.total} onChange={setOffset} />
          </>
        )}
      </section>
      {editing && (
        <MemberDialog
          workspace={workspace}
          member={editing === 'new' ? undefined : editing}
          onClose={() => {
            setEditing(null);
            setOffset(0);
          }}
        />
      )}
    </>
  );
}
