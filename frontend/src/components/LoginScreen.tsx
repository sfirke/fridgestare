import { FormEvent, useState } from 'react';

type LoginScreenProps = {
  errorMessage: string;
  onLogin: (email: string, password: string) => void;
};

export function LoginScreen({ errorMessage, onLogin }: LoginScreenProps) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    onLogin(email, password);
  }

  return (
    <main className="app-shell login-shell">
      <section className="hero-panel">
        <p className="eyebrow">Fridgestare</p>
        <h1>Dinners, remembered.</h1>
        <p className="lede">
          Plan a week, drag meals around, reroll a slot, ask for soup on Tuesday, and send
          yourself a tidy summary before the store run.
        </p>
      </section>
      <section className="status-panel auth-card">
        <h2>Sign in</h2>
        <form className="stacked-form" onSubmit={handleSubmit}>
          <label>
            <span>Email</span>
            <input
              type="email"
              autoComplete="username"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
            />
          </label>
          <label>
            <span>Password</span>
            <input
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
            />
          </label>
          <button type="submit">Enter the pantry</button>
        </form>
        {errorMessage ? (
          <p className="error-banner" role="alert">
            {errorMessage}
          </p>
        ) : null}
      </section>
    </main>
  );
}
