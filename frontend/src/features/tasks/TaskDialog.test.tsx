import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { setSession } from '../../api/client';
import type { Task } from '../../api/types';
import { TaskDialog } from './TaskDialog';

const user = { id: 'author', name: 'Test', email: 'test@example.com' };
const task: Task = {
  id: 'task',
  workspace_id: 'space',
  project_id: 'project',
  title: 'Existing task',
  description: 'Details',
  status: 'todo',
  priority: 'medium',
  due_at: null,
  assignee_id: null,
  created_by: 'author',
  created_at: '',
  updated_at: '',
  tag_ids: [],
};
const fetchMock = vi.fn(async (url: string, init?: RequestInit) => {
  if (init?.method === 'DELETE') return new Response(null, { status: 204 });
  if (init?.method === 'PATCH') return new Response(JSON.stringify(task));
  const items = url.includes('/projects')
    ? [{ id: 'project', name: 'Project' }]
    : url.includes('/members')
      ? [
          { user_id: 'author', name: 'Author', role: 'Member' },
          { user_id: 'viewer', name: 'Viewer', role: 'Viewer' },
        ]
      : [{ id: 'tag', name: 'Design', color: '#ffffff' }];
  return new Response(JSON.stringify({ items, total: items.length, limit: 50, offset: 0 }));
});

it('deletes only after explicit confirmation', async () => {
  const close = mount('Member');
  const actor = userEvent.setup();
  await actor.click(screen.getByRole('button', { name: 'Удалить задачу' }));
  expect(fetchMock.mock.calls.some(([, init]) => init?.method === 'DELETE')).toBe(false);
  await actor.click(screen.getByRole('button', { name: 'Подтвердить удаление' }));
  await waitFor(() => expect(close).toHaveBeenCalledOnce());
  expect(fetchMock.mock.calls.filter(([, init]) => init?.method === 'DELETE')).toHaveLength(1);
});
beforeEach(() => {
  vi.stubGlobal('fetch', fetchMock);
  fetchMock.mockClear();
  HTMLDialogElement.prototype.showModal = function () {
    this.setAttribute('open', '');
  };
  HTMLDialogElement.prototype.close = function () {
    this.removeAttribute('open');
  };
  setSession({ access_token: 'access', refresh_token: 'refresh', expires_in: 900 });
});
afterEach(() => {
  setSession(null);
  vi.unstubAllGlobals();
});

function mount(role: 'Member' | 'Viewer', value = task) {
  const cache = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const close = vi.fn();
  render(
    <QueryClientProvider client={cache}>
      <TaskDialog workspace="space" user={user} role={role} task={value} onClose={close} />
    </QueryClientProvider>,
  );
  return close;
}

it('keeps Viewer and non-owning Member read-only', async () => {
  mount('Member', { ...task, created_by: 'another-person' });
  expect(screen.getByLabelText('Название задачи')).toBeDisabled();
  expect(screen.queryByRole('button', { name: 'Сохранить изменения' })).not.toBeInTheDocument();
  await screen.findByRole('option', { name: 'Author' });
  expect(screen.queryByRole('option', { name: 'Viewer' })).not.toBeInTheDocument();
});

it('never allows a Viewer to edit even a formerly authored task', () => {
  mount('Viewer');
  expect(screen.getByLabelText('Название задачи')).toBeDisabled();
  expect(screen.queryByRole('button', { name: 'Удалить задачу' })).not.toBeInTheDocument();
});

it('saves a task with explicit nullable fields and tags without changing its project', async () => {
  const close = mount('Member');
  const actor = userEvent.setup();
  await screen.findByRole('option', { name: 'Author' });
  await actor.clear(screen.getByLabelText('Название задачи'));
  await actor.type(screen.getByLabelText('Название задачи'), 'Updated task');
  await actor.selectOptions(screen.getByLabelText('Статус'), 'done');
  await actor.click(screen.getByLabelText('Design'));
  await actor.click(screen.getByRole('button', { name: 'Сохранить изменения' }));
  await waitFor(() => expect(close).toHaveBeenCalledOnce());
  const mutation = fetchMock.mock.calls.find(([, init]) => init?.method === 'PATCH');
  expect(JSON.parse(String(mutation?.[1]?.body))).toEqual({
    title: 'Updated task',
    description: 'Details',
    status: 'done',
    priority: 'medium',
    due_at: null,
    assignee_id: null,
    tag_ids: ['tag'],
  });
});
