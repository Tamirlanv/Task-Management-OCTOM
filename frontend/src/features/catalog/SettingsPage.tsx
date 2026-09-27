import { useState, type FormEvent } from 'react';
import { Pencil } from 'lucide-react';
import { write } from '../../api/client';
import { useResource } from '../../api/queries';
import type { Role, User, Workspace } from '../../api/types';
import { ErrorNotice, Loading } from '../../components/Feedback';
import { useAction } from '../../components/useAction';
import { NameDialog } from './NameDialog';
import { TagsPanel } from './TagsPanel';

export function SettingsPage({
  workspace,
  role,
  user,
  onUser,
  onDeleted,
}: {
  workspace: string;
  role: Role;
  user: User;
  onUser: (user: User) => void;
  onDeleted: () => void;
}) {
  const [editing, setEditing] = useState(false);
  const [saved, setSaved] = useState(false);
  const query = useResource<Workspace>(`/workspaces/${workspace}`);
  const action = useAction();
  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaved(false);
    const data = new FormData(event.currentTarget);
    void action.run(async () => {
      onUser(await write<User>('/users/me', 'PATCH', { name: data.get('name') }));
      setSaved(true);
    });
  }
  return (
    <>
      <header className="page-heading">
        <div>
          <span className="eyebrow">ПУСТЬ ВСЁ БУДЕТ НА СВОИХ МЕСТАХ</span>
          <h1>Настройки</h1>
          <p>Ваш профиль и правила пространства.</p>
        </div>
      </header>
      <div className="settings-grid">
        <section className="card settings-card">
          <h2>Ваш профиль</h2>
          <form className="form-stack" onSubmit={submit}>
            <label>
              Имя
              <input name="name" required maxLength={200} defaultValue={user.name} />
            </label>
            <label>
              Email
              <input value={user.email} disabled />
            </label>
            {action.error && <ErrorNotice error={action.error} />}
            {saved && (
              <p className="success-note" role="status">
                Профиль обновлён.
              </p>
            )}
            <button className="primary" disabled={action.pending}>
              Сохранить профиль
            </button>
          </form>
        </section>
        <section className="card settings-card">
          <header className="section-heading">
            <h2>Пространство</h2>
            {role === 'Admin' && query.data && (
              <button
                className="icon-button"
                aria-label="Изменить пространство"
                onClick={() => setEditing(true)}
              >
                <Pencil size={18} />
              </button>
            )}
          </header>
          {query.isPending ? (
            <Loading />
          ) : query.error ? (
            <ErrorNotice error={query.error} retry={() => void query.refetch()} />
          ) : (
            <div className="workspace-description">
              <h3>{query.data.name}</h3>
              <p>{query.data.description || 'Общее место для проектов, задач и команды.'}</p>
              <span className="small muted">Название и описание доступны всей команде.</span>
            </div>
          )}
        </section>
      </div>
      <TagsPanel workspace={workspace} role={role} />
      {editing && query.data && (
        <NameDialog
          title="Изменить пространство"
          path={`/workspaces/${workspace}`}
          item={query.data}
          deletable
          onClose={() => setEditing(false)}
          onSaved={(value) => {
            if (!value) onDeleted();
          }}
        />
      )}
    </>
  );
}
