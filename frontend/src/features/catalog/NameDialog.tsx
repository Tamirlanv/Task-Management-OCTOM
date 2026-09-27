import { useState, type FormEvent } from 'react';
import { write } from '../../api/client';
import { useRefresh } from '../../api/queries';
import type { Workspace } from '../../api/types';
import { Modal } from '../../components/Modal';
import { ErrorNotice } from '../../components/Feedback';
import { useAction } from '../../components/useAction';

export function NameDialog({
  title,
  path,
  item,
  onClose,
  onSaved,
  deletable = false,
}: {
  title: string;
  path: string;
  item?: Workspace;
  onClose: () => void;
  onSaved?: (item: Workspace | null) => void;
  deletable?: boolean;
}) {
  const action = useAction();
  const refresh = useRefresh();
  const [confirm, setConfirm] = useState(false);
  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const fields = new FormData(event.currentTarget);
    void action.run(async () => {
      const result = await write<Workspace>(path, item ? 'PATCH' : 'POST', {
        name: fields.get('name'),
        description: fields.get('description'),
      });
      await refresh();
      onSaved?.(result);
      onClose();
    });
  }
  return (
    <Modal
      title={title}
      onClose={() => {
        if (!action.pending) onClose();
      }}
    >
      <form className="form-stack" onSubmit={submit}>
        <label>
          Название
          <input
            name="name"
            defaultValue={item?.name}
            placeholder="Например, запуск нового продукта"
            required
            maxLength={200}
            autoFocus
          />
        </label>
        <label>
          Описание
          <textarea
            name="description"
            defaultValue={item?.description}
            placeholder="Что важно знать команде?"
            maxLength={10000}
            rows={3}
          />
        </label>
        {action.error && <ErrorNotice error={action.error} />}
        {confirm && (
          <div className="danger-box">
            <p>Удалить «{item?.name}» и все вложенные задачи? Восстановить их нельзя.</p>
            <button
              type="button"
              className="danger"
              disabled={action.pending}
              onClick={() =>
                void action.run(async () => {
                  await write(path, 'DELETE');
                  await refresh();
                  onSaved?.(null);
                  onClose();
                })
              }
            >
              Да, удалить всё
            </button>
            <button type="button" className="text-button" onClick={() => setConfirm(false)}>
              Отмена
            </button>
          </div>
        )}
        <footer className="form-footer">
          {deletable && item && (
            <button
              type="button"
              className="text-button danger-text"
              onClick={() => setConfirm(true)}
            >
              Удалить
            </button>
          )}
          <button className="primary" disabled={action.pending}>
            {action.pending ? 'Сохраняем…' : item ? 'Сохранить' : 'Создать'}
          </button>
        </footer>
      </form>
    </Modal>
  );
}
