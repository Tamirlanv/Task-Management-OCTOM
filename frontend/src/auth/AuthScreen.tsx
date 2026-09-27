import { useState, type FormEvent } from 'react';
import { ArrowRight, Check, Layers3 } from 'lucide-react';
import { publicRequest, request, setSession } from '../api/client';
import type { Tokens, User } from '../api/types';
import { ErrorNotice } from '../components/Feedback';
import { useAction } from '../components/useAction';

export function AuthScreen({ onLogin }: { onLogin: (user: User) => void }) {
  const [register, setRegister] = useState(false);
  const [registered, setRegistered] = useState(false);
  const action = useAction();
  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const fields = new FormData(event.currentTarget);
    const credentials = {
      email: String(fields.get('email')),
      password: String(fields.get('password')),
    };
    void action.run(async () => {
      if (register && !registered) {
        await publicRequest<User>('/auth/register', { ...credentials, name: fields.get('name') });
        setRegistered(true);
      }
      const tokens = await publicRequest<Tokens>('/auth/login', credentials);
      setSession(tokens);
      onLogin(await request<User>('/users/me'));
    });
  }
  return (
    <main className="auth-layout">
      <section className="auth-story">
        <a className="brand" href="#">
          <span className="brand-symbol">
            <Layers3 size={24} />
          </span>{' '}
          OCTOM<span className="brand-dot">.</span>
        </a>
        <div className="auth-copy">
          <span className="eyebrow">МЕНЬШЕ ХАОСА. БОЛЬШЕ ФОКУСА.</span>
          <h1>
            Хорошие идеи
            <br />
            становятся
            <br />
            <em>готовыми делами.</em>
          </h1>
          <p>Проекты, задачи и команда — в одном спокойном пространстве.</p>
          <div className="auth-preview" aria-hidden="true">
            <div className="preview-top">
              <span className="tiny-avatar">O</span>
              <div>
                <b>Сегодня — отличный день</b>
                <small>Двигайтесь в своём ритме</small>
              </div>
              <span className="preview-dots">•••</span>
            </div>
            {[
              'Собрать идеи для проекта',
              'Обсудить главное с командой',
              'Сделать следующий шаг',
            ].map((text, index) => (
              <div className="preview-task" key={text}>
                <span className={index < 2 ? 'preview-check checked' : 'preview-check'}>
                  {index < 2 && <Check size={13} />}
                </span>
                <span>{text}</span>
                <span className={`preview-tag tag-${index}`}>
                  {['Готово', 'Готово', 'В работе'][index]}
                </span>
              </div>
            ))}
            <div className="preview-progress">
              <span>Каждый шаг имеет значение</span>
              <b>2 / 3</b>
            </div>
            <div className="progress-track">
              <i style={{ width: '67%' }} />
            </div>
          </div>
        </div>
        <span className="auth-footer">СОЗДАВАЙТЕ ВМЕСТЕ. ДВИГАЙТЕСЬ ВПЕРЁД.</span>
      </section>
      <section className="auth-panel">
        <div className="auth-form-wrap">
          <span className="eyebrow">ВАШЕ РАБОЧЕЕ ПРОСТРАНСТВО</span>
          <h2>{register ? 'Начнём с знакомства' : 'С возвращением'}</h2>
          <p className="muted">
            {register
              ? 'Создайте аккаунт и соберите свою команду.'
              : 'Войдите, чтобы продолжить с того же места.'}
          </p>
          <form onSubmit={submit} className="form-stack">
            {register && (
              <label>
                Ваше имя
                <input
                  name="name"
                  autoComplete="name"
                  placeholder="Как к вам обращаться?"
                  required
                  maxLength={200}
                  disabled={registered}
                />
              </label>
            )}
            <label>
              Email
              <input
                name="email"
                type="email"
                autoComplete="email"
                placeholder="you@company.com"
                required
              />
            </label>
            <label>
              Пароль
              <input
                name="password"
                type="password"
                autoComplete={register ? 'new-password' : 'current-password'}
                placeholder={register ? 'Не менее 12 символов' : 'Введите пароль'}
                required
                minLength={register ? 12 : 1}
                maxLength={128}
              />
            </label>
            {registered && (
              <p className="success-note">Аккаунт создан. При ошибке входа повторите вход ниже.</p>
            )}
            {action.error && <ErrorNotice error={action.error} />}
            <button className="primary large" disabled={action.pending}>
              {action.pending
                ? 'Подождите…'
                : register
                  ? 'Создать аккаунт'
                  : 'Войти в пространство'}
              <ArrowRight size={18} />
            </button>
          </form>
          <p className="auth-switch">
            {register ? 'Уже с нами?' : 'Впервые здесь?'}{' '}
            <button
              className="text-button"
              onClick={() => {
                setRegister(!register);
                setRegistered(false);
              }}
            >
              {register ? 'Войти' : 'Создать аккаунт'}
            </button>
          </p>
          <p className="session-note">
            Сессия хранится только на этой странице. После её обновления потребуется войти снова.
          </p>
        </div>
      </section>
    </main>
  );
}
