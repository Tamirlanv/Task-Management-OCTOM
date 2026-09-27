import { useState, type FormEvent } from 'react';
import { write } from '../../api/client';
import { useRefresh } from '../../api/queries';
import type { Member } from '../../api/types';
import { Modal } from '../../components/Modal';
import { ErrorNotice } from '../../components/Feedback';
import { useAction } from '../../components/useAction';
import { roles } from '../../lib/format';

export function MemberDialog({
  workspace,
  member,
  onClose,
}: {
  workspace: string;
  member?: Member;
  onClose: () => void;
}) {
  const action = useAction();
  const refresh = useRefresh();
  const [confirm, setConfirm] = useState(false);
  const path = `/workspaces/${workspace}/members${member ? `/${member.user_id}` : ''}`;
  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = new FormData(event.currentTarget);
    void action.run(async () => {
      await write(path, member ? 'PATCH' : 'POST', {
        role: data.get('role'),
        ...(member ? {} : { email: data.get('email') }),
      });
      await refresh();
      onClose();
    });
  }
  return (
    <Modal
      title={member ? `Права: ${member.name}` : 'Добавить участника'}
      onClose={() => {
        if (!action.pending) onClose();
      }}
    >
      <form className="form-stack" onSubmit={submit}>
        {!member && (
          <>
            <p className="muted">Добавьте человека по email его зарегистрированного аккаунта.</p>
            <label>
              Email
              <input
                type="email"
                name="email"
                required
                placeholder="colleague@company.com"
                autoFocus
              />
            </label>
          </>
        )}
        <label>
          Роль
          <select name="role" defaultValue={member?.role ?? 'Member'}>
            {Object.entries(roles).map(([role, name]) => (
              <option key={role} value={role}>
                {name}
              </option>
            ))}
          </select>
        </label>
        <p className="field-help">
          Администратор управляет пространством и людьми. Менеджер — проектами и всеми задачами.
          Участник — своими и назначенными задачами. Наблюдатель только читает.
        </p>
        {action.error && <ErrorNotice error={action.error} />}
        {confirm && (
          <div className="danger-box">
            <p>Участник потеряет доступ, его назначения на задачи будут сняты.</p>
            <button
              type="button"
              className="danger"
              disabled={action.pending}
              onClick={() =>
                void action.run(async () => {
                  await write(path, 'DELETE');
                  await refresh();
                  onClose();
                })
              }
            >
              Удалить из команды
            </button>
            <button className="text-button" type="button" onClick={() => setConfirm(false)}>
              Отмена
            </button>
          </div>
        )}
        <footer className="form-footer">
          {member && (
            <button
              className="text-button danger-text"
              type="button"
              onClick={() => setConfirm(true)}
            >
              Удалить участника
            </button>
          )}
          <button className="primary" disabled={action.pending}>
            {action.pending ? 'Сохраняем…' : member ? 'Сохранить' : 'Добавить'}
          </button>
        </footer>
      </form>
    </Modal>
  );
}
