import { useState } from 'react';
import { ArrowRight, CheckCheck, Clock3, FolderKanban, Plus, Zap } from 'lucide-react';
import type { Overview, Page, Role, Task, User } from '../../api/types';
import { useResource } from '../../api/queries';
import type { Screen } from '../../components/Sidebar';
import { Empty, ErrorNotice, Loading } from '../../components/Feedback';
import { ActivityChart } from './ActivityChart';
import { TaskDialog } from '../tasks/TaskDialog';
import { TaskRow } from '../tasks/TaskRow';
import { date } from '../../lib/format';

export function Dashboard({
  workspace,
  user,
  role,
  overview,
  navigate,
}: {
  workspace: string;
  user: User;
  role: Role;
  overview: Overview;
  navigate: (screen: Screen) => void;
}) {
  const [editing, setEditing] = useState<Task | 'new' | null>(null);
  const tasks = useResource<Page<Task>>(
    `/workspaces/${workspace}/tasks?limit=4&sort=updated_at&direction=desc`,
  );
  const due = useResource<Page<Task>>(
    `/workspaces/${workspace}/tasks?limit=3&sort=due_at&direction=asc&statuses=todo&statuses=in_progress`,
  );
  const stats = overview.statistics;
  const cards = [
    {
      name: 'Завершено задач',
      value: stats.done,
      caption: `из ${stats.total} задач пространства`,
      icon: CheckCheck,
      color: 'purple',
    },
    {
      name: 'Сейчас в работе',
      value: stats.in_progress,
      caption: 'Шаг за шагом к результату',
      icon: Zap,
      color: 'cyan',
    },
    {
      name: 'Всего проектов',
      value: stats.projects,
      caption: 'Идей, которые обретают форму',
      icon: FolderKanban,
      color: 'orange',
    },
  ];
  return (
    <>
      <header className="page-heading">
        <div>
          <span className="eyebrow">ВАШ ДЕНЬ ПОД КОНТРОЛЕМ</span>
          <h1>
            Привет, {user.name.split(' ')[0]} <span className="greeting-dot">✦</span>
          </h1>
          <p>Всё важное — здесь. Давайте сделаем следующий шаг.</p>
        </div>
        <button
          className="primary"
          disabled={role === 'Viewer' || stats.projects === 0}
          onClick={() => setEditing('new')}
        >
          <Plus size={18} />
          Новая задача
        </button>
      </header>
      <div className="stats-grid">
        {cards.map(({ name, value, caption, icon: Icon, color }) => (
          <section className="card stat-card" key={name}>
            <span className={`stat-icon ${color}`}>
              <Icon size={23} />
            </span>
            <div>
              <p>{name}</p>
              <strong>{String(value).padStart(2, '0')}</strong>
            </div>
            <small>{caption}</small>
            <div className={`stat-decoration ${color}`} aria-hidden="true">
              <i />
              <i />
              <i />
              <i />
              <i />
              <i />
              <i />
            </div>
          </section>
        ))}
      </div>
      <div className="dashboard-grid">
        <ActivityChart days={stats.days} />
        <section className="card deadlines-card">
          <header className="section-heading">
            <div>
              <h2>Ближайшие сроки</h2>
              <p>Держим фокус на главном</p>
            </div>
            <Clock3 size={20} className="muted" />
          </header>
          {due.isPending ? (
            <Loading />
          ) : due.error ? (
            <ErrorNotice error={due.error} retry={() => void due.refetch()} />
          ) : due.data.items.filter((task) => task.due_at).length ? (
            <div className="deadline-list">
              {due.data.items
                .filter((task) => task.due_at)
                .map((task) => (
                  <button className="deadline-item" key={task.id} onClick={() => setEditing(task)}>
                    <span className={`deadline-dot ${task.priority}`} />
                    <span>
                      <strong>{task.title}</strong>
                      <small>{date(task.due_at)}</small>
                    </span>
                    <ArrowRight size={15} />
                  </button>
                ))}
            </div>
          ) : (
            <Empty title="Можно выдохнуть" text="Предстоящих сроков пока нет." />
          )}
          <div className={stats.overdue ? 'deadline-summary overdue' : 'deadline-summary'}>
            <span>Просрочено задач</span>
            <strong>{stats.overdue}</strong>
          </div>
        </section>
      </div>
      <section className="card tasks-card">
        <header className="section-heading">
          <div>
            <h2>Последние задачи</h2>
            <p>То, над чем работает ваша команда</p>
          </div>
          <button className="text-button" onClick={() => navigate('tasks')}>
            Все задачи
            <ArrowRight size={16} />
          </button>
        </header>
        {tasks.isPending ? (
          <Loading />
        ) : tasks.error ? (
          <ErrorNotice error={tasks.error} retry={() => void tasks.refetch()} />
        ) : tasks.data.items.length ? (
          <div className="task-list">
            {tasks.data.items.map((task) => (
              <TaskRow key={task.id} task={task} onOpen={() => setEditing(task)} />
            ))}
          </div>
        ) : (
          <Empty
            title="Здесь начнётся прогресс"
            text={
              stats.projects
                ? 'Добавьте первую задачу, чтобы перейти от планов к делу.'
                : 'Создайте проект во вкладке «Проекты», а затем добавьте первую задачу.'
            }
          />
        )}
      </section>
      {editing && (
        <TaskDialog
          workspace={workspace}
          role={role}
          user={user}
          task={editing === 'new' ? undefined : editing}
          onClose={() => setEditing(null)}
        />
      )}
    </>
  );
}
