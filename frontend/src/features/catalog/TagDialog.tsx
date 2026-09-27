import { useState, type FormEvent } from 'react';
import { write } from '../../api/client';
import { useRefresh } from '../../api/queries';
import type { Tag } from '../../api/types';
import { Modal } from '../../components/Modal';
import { ErrorNotice } from '../../components/Feedback';
import { useAction } from '../../components/useAction';

export function TagDialog({
  workspace,
  tag,
  onClose,
}: {
  workspace: string;
  tag?: Tag;
  onClose: () => void;
}) {
  const action = useAction();
  const refresh = useRefresh();
  const [confirm, setConfirm] = useState(false);
  const path = `/workspaces/${workspace}/tags${tag ? `/${tag.id}` : ''}`;
  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    void action.run(async () => {
      await write(path, tag ? 'PATCH' : 'POST', {
        name: data.get('name'),
        color: data.get('color'),
      });
      await refresh();
      onClose();
    });
  }
  return (
    <Modal
      title={tag ? 'Изменить тег' : 'Новый тег'}
      onClose={() => {
        if (!action.pending) onClose();
      }}
    >
      <form className="form-stack" onSubmit={submit}>
        <label>
          Название тега
          <input name="name" required maxLength={50} defaultValue={tag?.name} autoFocus />
        </label>
        <label>
          Цвет
          <input type="color" name="color" defaultValue={tag?.color ?? '#8271f5'} />
        </label>
        {action.error && <ErrorNotice error={action.error} />}
        {confirm && (
          <div className="danger-box">
            <p>Удалить тег со всех задач? Сами задачи сохранятся.</p>
            <button
              className="danger"
              type="button"
              disabled={action.pending}
              onClick={() =>
                void action.run(async () => {
                  await write(path, 'DELETE');
                  await refresh();
                  onClose();
                })
              }
            >
              Подтвердить удаление
            </button>
            <button type="button" className="text-button" onClick={() => setConfirm(false)}>
              Отмена
            </button>
          </div>
        )}
        <footer className="form-footer">
          {tag && (
            <button
              type="button"
              className="text-button danger-text"
              onClick={() => setConfirm(true)}
            >
              Удалить тег
            </button>
          )}
          <button className="primary" disabled={action.pending}>
            {action.pending ? 'Сохраняем…' : 'Сохранить'}
          </button>
        </footer>
      </form>
    </Modal>
  );
}
