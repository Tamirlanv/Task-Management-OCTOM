import { useEffect, useState } from 'react';
import { Plus } from 'lucide-react';
import { useResource } from '../../api/queries';
import type { Page, Role, Task, User } from '../../api/types';
import { Empty, ErrorNotice, Loading } from '../../components/Feedback';
import { Pagination } from '../../components/Pagination';
import { TaskFilters } from './TaskFilters';
import { initialFilters } from './filters';
import { TaskDialog } from './TaskDialog';
import { TaskRow } from './TaskRow';

export function TasksPage({
  workspace,
  user,
  role,
  initialProject,
}: {
  workspace: string;
  user: User;
  role: Role;
  initialProject: string;
}) {
  const [filters, setFilters] = useState({ ...initialFilters, project: initialProject });
  const [search, setSearch] = useState('');
  const [offset, setOffset] = useState(0);
  const [editing, setEditing] = useState<Task | 'new' | null>(null);
  useEffect(() => {
    const timer = setTimeout(() => setSearch(filters.q.trim()), 350);
    return () => clearTimeout(timer);
  }, [filters.q]);
  const [sort, direction] = filters.sort.split(':');
  const params = new URLSearchParams({ limit: '12', offset: String(offset), sort, direction });
  const values = {
    q: search,
    statuses: filters.status,
    priorities: filters.priority,
    project_id: filters.project,
    assignee_id: filters.assignee,
    tag_ids: filters.tag,
    overdue: filters.overdue ? 'true' : '',
  };
  Object.entries(values).forEach(([key, value]) => {
    if (value) params.set(key, value);
  });
  const query = useResource<Page<Task>>(`/workspaces/${workspace}/tasks?${params}`);
  return (
    <>
      <header className="page-heading">
        <div>
          <span className="eyebrow">ОТ ИДЕИ К РЕЗУЛЬТАТУ</span>
          <h1>Задачи</h1>
          <p>У каждого дела есть своё место и следующий шаг.</p>
        </div>
        {role !== 'Viewer' && (
          <button className="primary" onClick={() => setEditing('new')}>
            <Plus size={18} />
            Новая задача
          </button>
        )}
      </header>
      <section className="card">
        <TaskFilters
          workspace={workspace}
          value={filters}
          onChange={(value) => {
            setFilters(value);
            setOffset(0);
          }}
        />
        {query.isPending ? (
          <Loading />
        ) : query.error ? (
          <ErrorNotice error={query.error} retry={() => void query.refetch()} />
        ) : (
          <>
            {query.data.items.length ? (
              <div className="task-list">
                {query.data.items.map((task) => (
                  <TaskRow key={task.id} task={task} onOpen={() => setEditing(task)} />
                ))}
              </div>
            ) : (
              <Empty
                title="Пока ничего не найдено"
                text="Попробуйте изменить фильтры или создать новую задачу."
              />
            )}
            <Pagination offset={offset} limit={12} total={query.data.total} onChange={setOffset} />
          </>
        )}
      </section>
      {editing && (
        <TaskDialog
          workspace={workspace}
          user={user}
          role={role}
          task={editing === 'new' ? undefined : editing}
          projectId={filters.project}
          onClose={() => setEditing(null)}
        />
      )}
    </>
  );
}
