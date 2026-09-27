import { useState, type FormEvent } from 'react';
import { write } from '../../api/client';
import type {
  Member,
  Priority,
  Project,
  Role,
  Status,
  Task,
  TaskInput,
  User,
} from '../../api/types';
import { useRefresh } from '../../api/queries';
import { Modal } from '../../components/Modal';
import { ResourceSelect } from '../../components/ResourceSelect';
import { ErrorNotice } from '../../components/Feedback';
import { useAction } from '../../components/useAction';
import { canEdit, localDateTime, priorities, statuses } from '../../lib/format';
import { TagPicker } from './TagPicker';

export function TaskDialog({
  workspace,
  user,
  role,
  task,
  projectId = '',
  onClose,
}: {
  workspace: string;
  user: User;
  role: Role;
  task?: Task;
  projectId?: string;
  onClose: () => void;
}) {
  const [project, setProject] = useState(task?.project_id ?? projectId);
  const [assignee, setAssignee] = useState(task?.assignee_id ?? '');
  const [tags, setTags] = useState(task?.tag_ids ?? []);
  const [confirm, setConfirm] = useState(false);
  const action = useAction();
  const refresh = useRefresh();
  const editable = task ? canEdit(task, role, user.id) : role !== 'Viewer';
  const base = `/workspaces/${workspace}`;
  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const fields = new FormData(event.currentTarget);
    const due = String(fields.get('due_at'));
    const data: TaskInput = {
      title: String(fields.get('title')),
      description: String(fields.get('description')),
      status: fields.get('status') as Status,
      priority: fields.get('priority') as Priority,
      due_at: due ? new Date(due).toISOString() : null,
      assignee_id: assignee || null,
      tag_ids: tags,
    };
    void action.run(async () => {
      await write(
        task ? `${base}/tasks/${task.id}` : `${base}/projects/${project}/tasks`,
        task ? 'PATCH' : 'POST',
        data,
      );
      await refresh();
      onClose();
    });
  }
  return (
    <Modal
      title={task ? 'Детали задачи' : 'Новая задача'}
      onClose={() => {
        if (!action.pending) onClose();
      }}
    >
      <form onSubmit={submit} className="form-stack">
        {!editable && (
          <p className="read-only-note">
            Вы можете просматривать эту задачу. Для изменения нужны права автора, исполнителя или
            менеджера.
          </p>
        )}
        <fieldset disabled={!editable || action.pending} className="form-stack">
          <label>
            Название задачи
            <input
              name="title"
              defaultValue={task?.title}
              placeholder="Что нужно сделать?"
              required
              maxLength={200}
              autoFocus
            />
          </label>
          <label>
            Описание
            <textarea
              name="description"
              defaultValue={task?.description}
              placeholder="Детали, ссылки и ожидаемый результат"
              rows={3}
              maxLength={10000}
            />
          </label>
          <fieldset disabled={Boolean(task)}>
            <ResourceSelect<Project>
              path={`${base}/projects`}
              label="Проект"
              required
              value={project}
              onChange={setProject}
              option={(item) => ({ value: item.id, label: item.name })}
              empty="Выберите проект"
            />
          </fieldset>
          <div className="form-grid">
            <label>
              Статус
              <select name="status" defaultValue={task?.status ?? 'todo'}>
                {Object.entries(statuses).map(([key, text]) => (
                  <option key={key} value={key}>
                    {text}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Приоритет
              <select name="priority" defaultValue={task?.priority ?? 'medium'}>
                {Object.entries(priorities).map(([key, text]) => (
                  <option key={key} value={key}>
                    {text}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <div className="form-grid">
            <label>
              Срок <small>местное время</small>
              <input
                type="datetime-local"
                name="due_at"
                defaultValue={localDateTime(task?.due_at ?? null)}
              />
            </label>
            <ResourceSelect<Member>
              path={`${base}/members`}
              label="Исполнитель"
              value={assignee}
              onChange={setAssignee}
              option={(item) =>
                item.role === 'Viewer' ? null : { value: item.user_id, label: item.name }
              }
              empty="Не назначен"
            />
          </div>
          <TagPicker workspace={workspace} selected={tags} onChange={setTags} />
        </fieldset>
        {action.error && <ErrorNotice error={action.error} />}
        {confirm && (
          <div className="danger-box">
            <p>Удалить задачу «{task?.title}»? Это действие нельзя отменить.</p>
            <button
              type="button"
              className="danger"
              disabled={action.pending}
              onClick={() =>
                void action.run(async () => {
                  await write(`${base}/tasks/${task?.id}`, 'DELETE');
                  await refresh();
                  onClose();
                })
              }
            >
              Подтвердить удаление
            </button>
            <button className="text-button" type="button" onClick={() => setConfirm(false)}>
              Отмена
            </button>
          </div>
        )}
        {editable && (
          <footer className="form-footer">
            {task && (
              <button
                className="text-button danger-text"
                type="button"
                onClick={() => setConfirm(true)}
              >
                Удалить задачу
              </button>
            )}
            <button className="primary" disabled={action.pending || !project}>
              {action.pending ? 'Сохраняем…' : task ? 'Сохранить изменения' : 'Создать задачу'}
            </button>
          </footer>
        )}
      </form>
    </Modal>
  );
}
