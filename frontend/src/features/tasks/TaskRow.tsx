import { ArrowUpRight, CalendarDays, Check, Circle, Pause, Play } from 'lucide-react';
import type { Task } from '../../api/types';
import { date, priorities, statuses } from '../../lib/format';

export function TaskRow({ task, onOpen }: { task: Task; onOpen: () => void }) {
  const Icon = { todo: Circle, in_progress: Play, done: Check, cancelled: Pause }[task.status];
  const overdue =
    task.due_at &&
    new Date(task.due_at) < new Date() &&
    !['done', 'cancelled'].includes(task.status);
  return (
    <button className="task-row" onClick={onOpen}>
      <span className={`task-symbol ${task.status}`}>
        <Icon size={19} />
      </span>
      <span className="task-title">
        <strong>{task.title}</strong>
        <small>{task.description || 'Добавьте детали — команде будет проще начать'}</small>
      </span>
      <span className={`priority-label ${task.priority}`}>
        <i />
        {priorities[task.priority]}
      </span>
      <span className={`status-label ${task.status}`}>{statuses[task.status]}</span>
      <span className={overdue ? 'task-date danger-text' : 'task-date'}>
        <CalendarDays size={14} />
        {date(task.due_at)}
      </span>
      <ArrowUpRight className="task-arrow" size={17} />
    </button>
  );
}
