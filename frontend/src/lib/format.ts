import type { Priority, Role, Status, Task } from '../api/types';
export const statuses: Record<Status, string> = {
  todo: 'К выполнению',
  in_progress: 'В работе',
  done: 'Готово',
  cancelled: 'Отменено',
};
export const priorities: Record<Priority, string> = {
  low: 'Низкий',
  medium: 'Средний',
  high: 'Высокий',
  urgent: 'Срочный',
};
export const roles: Record<Role, string> = {
  Admin: 'Администратор',
  Manager: 'Менеджер',
  Member: 'Участник',
  Viewer: 'Наблюдатель',
};
export const date = (value: string | null) =>
  value
    ? new Intl.DateTimeFormat('ru', { day: 'numeric', month: 'short' }).format(new Date(value))
    : 'Без срока';
export const calendarDate = (value: string) =>
  new Intl.DateTimeFormat('ru', { day: 'numeric', month: 'short', timeZone: 'UTC' }).format(
    new Date(value),
  );
export const initials = (name: string) =>
  name
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((word) => word[0])
    .join('')
    .toUpperCase();
export const canManage = (role: Role) => role === 'Admin' || role === 'Manager';
export const canEdit = (task: Task, role: Role, user: string) =>
  canManage(role) || (role === 'Member' && (task.created_by === user || task.assignee_id === user));
export function localDateTime(value: string | null) {
  if (!value) return '';
  const instant = new Date(value);
  return new Date(instant.getTime() - instant.getTimezoneOffset() * 60000)
    .toISOString()
    .slice(0, 16);
}
