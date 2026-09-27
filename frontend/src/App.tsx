import { useEffect, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { LogOut, Plus } from 'lucide-react';
import { logout, onSessionExpired } from './api/client';
import type { User, Workspace } from './api/types';
import { AuthScreen } from './auth/AuthScreen';
import { Sidebar, type Screen } from './components/Sidebar';
import { ResourceSelect } from './components/ResourceSelect';
import { NameDialog } from './features/catalog/NameDialog';
import { WorkspaceView } from './features/WorkspaceView';
import { initials } from './lib/format';
import { Loading } from './components/Feedback';

export function App() {
  const [user, setUser] = useState<User | null>(null);
  const [workspace, setWorkspace] = useState('');
  const [screen, setScreen] = useState<Screen>('dashboard');
  const [create, setCreate] = useState(false);
  const [notice, setNotice] = useState('');
  const [signingOut, setSigningOut] = useState(false);
  const cache = useQueryClient();
  useEffect(() => {
    onSessionExpired(() => {
      setUser(null);
      setWorkspace('');
      cache.clear();
      setNotice('Сессия завершилась. Войдите снова.');
    });
    return () => onSessionExpired(() => {});
  }, [cache]);
  async function signOut() {
    setSigningOut(true);
    setUser(null);
    setWorkspace('');
    cache.clear();
    try {
      await logout();
    } catch {
      setNotice('Вы вышли на этом устройстве. Сервер недоступен: отзыв сессии не подтверждён.');
    } finally {
      setSigningOut(false);
    }
  }
  if (signingOut) return <Loading />;
  if (!user)
    return (
      <>
        {notice && (
          <div className="global-notice" role="status">
            {notice}
          </div>
        )}
        <AuthScreen
          onLogin={(value) => {
            cache.clear();
            setUser(value);
            setNotice('');
            setScreen('dashboard');
          }}
        />
      </>
    );
  return (
    <div className="app-shell">
      <a className="skip-link" href="#main">
        К содержимому
      </a>
      <Sidebar screen={screen} navigate={setScreen} onLogout={() => void signOut()} />
      <div className="main-shell">
        <header className="topbar">
          <div className="workspace-picker">
            <ResourceSelect<Workspace>
              path="/workspaces"
              label="Пространство"
              value={workspace}
              onChange={(value) => {
                setWorkspace(value);
                setScreen('dashboard');
              }}
              option={(item) => ({ value: item.id, label: item.name })}
              empty="Выберите пространство"
            />
            <button
              className="icon-button"
              aria-label="Создать пространство"
              title="Создать пространство"
              onClick={() => setCreate(true)}
            >
              <Plus size={19} />
            </button>
          </div>
          <div className="profile">
            <div>
              <strong>{user.name}</strong>
              <span>{user.email}</span>
            </div>
            <span className="avatar">{initials(user.name)}</span>
            <button
              className="icon-button mobile-logout"
              aria-label="Выйти из аккаунта"
              onClick={() => void signOut()}
            >
              <LogOut size={17} />
            </button>
          </div>
        </header>
        <main id="main" className="page-content">
          {workspace ? (
            <WorkspaceView
              key={workspace}
              workspace={workspace}
              user={user}
              screen={screen}
              navigate={setScreen}
              onUser={setUser}
              onDeleted={() => setWorkspace('')}
            />
          ) : (
            <section className="welcome card">
              <span className="eyebrow">ВСЁ НАЧИНАЕТСЯ С ИДЕИ</span>
              <h1>
                Ваш следующий большой проект
                <br />
                начинается здесь.
              </h1>
              <p>
                Выберите пространство вверху или создайте новое.
                <br />
                Затем добавьте проект, задачи и свою команду.
              </p>
              <button className="primary" onClick={() => setCreate(true)}>
                <Plus size={18} />
                Создать пространство
              </button>
              <div className="welcome-steps">
                <span>
                  <b>01</b>Пространство
                </span>
                <i />
                <span>
                  <b>02</b>Проект
                </span>
                <i />
                <span>
                  <b>03</b>Первая задача
                </span>
              </div>
            </section>
          )}
        </main>
      </div>
      {create && (
        <NameDialog
          title="Новое пространство"
          path="/workspaces"
          onClose={() => setCreate(false)}
          onSaved={(item) => {
            if (item) setWorkspace(item.id);
          }}
        />
      )}
    </div>
  );
}
