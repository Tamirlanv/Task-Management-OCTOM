import {
  CheckCheck,
  FolderKanban,
  LayoutDashboard,
  Layers3,
  LogOut,
  Settings2,
  UsersRound,
  Sparkles,
} from 'lucide-react';
export type Screen = 'dashboard' | 'tasks' | 'projects' | 'team' | 'settings';
const items = [
  { id: 'dashboard', label: 'Обзор', icon: LayoutDashboard },
  { id: 'tasks', label: 'Задачи', icon: CheckCheck },
  { id: 'projects', label: 'Проекты', icon: FolderKanban },
  { id: 'team', label: 'Команда', icon: UsersRound },
  { id: 'settings', label: 'Настройки', icon: Settings2 },
] as const;
export function Sidebar({
  screen,
  navigate,
  onLogout,
}: {
  screen: Screen;
  navigate: (screen: Screen) => void;
  onLogout: () => void;
}) {
  return (
    <aside className="sidebar">
      <a
        className="brand"
        href="#"
        onClick={(event) => {
          event.preventDefault();
          navigate('dashboard');
        }}
      >
        <span className="brand-symbol">
          <Layers3 size={23} />
        </span>
        OCTOM<span className="brand-dot">.</span>
      </a>
      <span className="sidebar-caption">РАБОЧЕЕ ПРОСТРАНСТВО</span>
      <nav aria-label="Основная навигация">
        {items.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            aria-label={label}
            className={screen === id ? 'nav-item active' : 'nav-item'}
            aria-current={screen === id ? 'page' : undefined}
            onClick={() => navigate(id)}
          >
            <Icon size={20} />
            <span>{label}</span>
            {screen === id && <i />}
          </button>
        ))}
      </nav>
      <div className="sidebar-bottom">
        <div className="focus-card">
          <span className="focus-icon">
            <Sparkles size={23} />
          </span>
          <strong>
            Маленькие шаги.
            <br />
            Большие результаты.
          </strong>
          <p>
            Выберите главное
            <br />и начните с одной задачи.
          </p>
        </div>
        <button className="nav-item logout" onClick={onLogout}>
          <LogOut size={19} />
          <span>Выйти</span>
        </button>
        <small className="sidebar-footnote">Место для хороших идей</small>
      </div>
    </aside>
  );
}
