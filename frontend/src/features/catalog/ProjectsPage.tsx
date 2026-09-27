import { useState } from 'react';
import { ArrowUpRight, FolderKanban, Pencil, Plus } from 'lucide-react';
import { useResource } from '../../api/queries';
import type { Page, Project, Role } from '../../api/types';
import { Empty, ErrorNotice, Loading } from '../../components/Feedback';
import { Pagination } from '../../components/Pagination';
import { canManage } from '../../lib/format';
import { NameDialog } from './NameDialog';

export function ProjectsPage({
  workspace,
  role,
  openProject,
}: {
  workspace: string;
  role: Role;
  openProject: (id: string) => void;
}) {
  const [offset, setOffset] = useState(0);
  const [editing, setEditing] = useState<Project | 'new' | null>(null);
  const path = `/workspaces/${workspace}/projects`;
  const query = useResource<Page<Project>>(`${path}?limit=12&offset=${offset}`);
  return (
    <>
      <header className="page-heading">
        <div>
          <span className="eyebrow">БОЛЬШИЕ ПЛАНЫ — ПОНЯТНЫЕ ШАГИ</span>
          <h1>Проекты</h1>
          <p>Объедините связанные задачи вокруг общей цели.</p>
        </div>
        {canManage(role) && (
          <button className="primary" onClick={() => setEditing('new')}>
            <Plus size={18} />
            Новый проект
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
            <div className="project-grid">
              {query.data.items.map((project, index) => (
                <article className="card project-card" key={project.id}>
                  <div className="project-card-top">
                    <span className={`stat-icon ${['purple', 'cyan', 'orange'][index % 3]}`}>
                      <FolderKanban size={22} />
                    </span>
                    {canManage(role) && (
                      <button
                        className="icon-button"
                        aria-label={`Изменить проект ${project.name}`}
                        onClick={() => setEditing(project)}
                      >
                        <Pencil size={16} />
                      </button>
                    )}
                  </div>
                  <h2>{project.name}</h2>
                  <p>
                    {project.description || 'Каждый большой результат начинается с первой задачи.'}
                  </p>
                  <button className="text-button" onClick={() => openProject(project.id)}>
                    Открыть задачи
                    <ArrowUpRight size={16} />
                  </button>
                </article>
              ))}
            </div>
          ) : (
            <section className="card">
              <Empty
                title="Дайте идее своё пространство"
                text={
                  canManage(role)
                    ? 'Создайте первый проект — например, «Запуск продукта».'
                    : 'Менеджер или администратор может создать первый проект.'
                }
              />
            </section>
          )}
          <Pagination offset={offset} limit={12} total={query.data.total} onChange={setOffset} />
        </>
      )}
      {editing && (
        <NameDialog
          title={editing === 'new' ? 'Новый проект' : 'Изменить проект'}
          path={editing === 'new' ? path : `${path}/${editing.id}`}
          item={editing === 'new' ? undefined : editing}
          deletable
          onClose={() => setEditing(null)}
          onSaved={() => setOffset(0)}
        />
      )}
    </>
  );
}
