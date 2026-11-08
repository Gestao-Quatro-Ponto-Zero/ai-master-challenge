import React from 'react';
import type { CurrentUser } from '../api/types';
import { ROLE_LABELS } from '../lib/constants';
import { initialsOf } from '../lib/format';

interface Props {
  user: CurrentUser | null;
}

export default class AppHeader extends React.Component<Props> {
  render() {
    const { user } = this.props;
    return (
      <header className="topbar">
        <div className="topbar__inner">
          <div className="brand">
            <img className="brand__logo" src="/logo.png" alt="" width="28" height="28" />
            <strong className="brand__name">G4 - Sales Priority</strong>
          </div>
          {user && (
            <div className="usercard">
              <span className="usercard__avatar" aria-hidden="true">
                {initialsOf(user.name)}
              </span>
              <span className="usercard__text">
                <span className="usercard__name">{user.name}</span>
                <span className="usercard__role">
                  {ROLE_LABELS[user.role] ?? user.role} · {user.region}
                </span>
              </span>
            </div>
          )}
        </div>
      </header>
    );
  }
}
