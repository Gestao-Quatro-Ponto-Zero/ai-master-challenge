import { useState, useRef } from 'react';
import { User, Lock, Camera, Check, AlertCircle, Eye, EyeOff } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { updateProfile, updateAvatar } from '../services/profileService';
import { changePassword } from '../services/authService';

const TIMEZONES = [
  'UTC',
  'America/New_York',
  'America/Chicago',
  'America/Denver',
  'America/Los_Angeles',
  'America/Sao_Paulo',
  'Europe/London',
  'Europe/Paris',
  'Europe/Berlin',
  'Asia/Tokyo',
  'Asia/Shanghai',
  'Asia/Kolkata',
  'Australia/Sydney',
];

type AlertState = { type: 'success' | 'error'; message: string } | null;

function Alert({ alert }: { alert: AlertState }) {
  if (!alert) return null;
  const isSuccess = alert.type === 'success';
  return (
    <div
      className={`flex items-center gap-2.5 px-4 py-3 rounded-xl text-sm ${
        isSuccess
          ? 'bg-green-50 text-green-700 border border-green-100'
          : 'bg-red-50 text-red-700 border border-red-100'
      }`}
    >
      {isSuccess ? <Check className="w-4 h-4 shrink-0" /> : <AlertCircle className="w-4 h-4 shrink-0" />}
      {alert.message}
    </div>
  );
}

function UserInitials({ name, email }: { name?: string; email: string }) {
  const initials = name
    ? name.split(' ').map((n) => n[0]).join('').toUpperCase().slice(0, 2)
    : email[0].toUpperCase();
  return (
    <div className="w-full h-full flex items-center justify-center text-2xl font-bold text-blue-700 bg-blue-100 rounded-full">
      {initials}
    </div>
  );
}

export default function Profile() {
  const { user, profile, refreshAuth } = useAuth();

  const [fullName, setFullName] = useState(profile?.full_name || '');
  const [phone, setPhone] = useState(profile?.phone || '');
  const [department, setDepartment] = useState(profile?.department || '');
  const [timezone, setTimezone] = useState(profile?.timezone || 'UTC');
  const [infoLoading, setInfoLoading] = useState(false);
  const [infoAlert, setInfoAlert] = useState<AlertState>(null);

  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showCurrent, setShowCurrent] = useState(false);
  const [showNew, setShowNew] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [pwLoading, setPwLoading] = useState(false);
  const [pwAlert, setPwAlert] = useState<AlertState>(null);

  const [avatarLoading, setAvatarLoading] = useState(false);
  const [avatarAlert, setAvatarAlert] = useState<AlertState>(null);
  const [avatarPreview, setAvatarPreview] = useState<string | null>(profile?.avatar_url || null);
  const fileRef = useRef<HTMLInputElement>(null);

  async function handleInfoSave(e: React.FormEvent) {
    e.preventDefault();
    if (!user) return;
    setInfoLoading(true);
    setInfoAlert(null);
    try {
      await updateProfile(user.id, { full_name: fullName, phone, department, timezone });
      await refreshAuth();
      setInfoAlert({ type: 'success', message: 'Perfil atualizado com sucesso.' });
    } catch (err) {
      setInfoAlert({ type: 'error', message: err instanceof Error ? err.message : 'Falha ao atualizar.' });
    } finally {
      setInfoLoading(false);
    }
  }

  async function handlePasswordSave(e: React.FormEvent) {
    e.preventDefault();
    setPwAlert(null);
    if (newPassword !== confirmPassword) {
      setPwAlert({ type: 'error', message: 'As senhas não coincidem.' });
      return;
    }
    setPwLoading(true);
    try {
      await changePassword(currentPassword, newPassword);
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
      setPwAlert({ type: 'success', message: 'Senha alterada com sucesso.' });
    } catch (err) {
      setPwAlert({ type: 'error', message: err instanceof Error ? err.message : 'Falha ao alterar a senha.' });
    } finally {
      setPwLoading(false);
    }
  }

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = async (ev) => {
      const dataUrl = ev.target?.result as string;
      setAvatarPreview(dataUrl);
      if (!user) return;
      setAvatarLoading(true);
      setAvatarAlert(null);
      try {
        await updateAvatar(user.id, dataUrl);
        await refreshAuth();
        setAvatarAlert({ type: 'success', message: 'Avatar atualizado com sucesso.' });
      } catch (err) {
        setAvatarAlert({ type: 'error', message: err instanceof Error ? err.message : 'Falha ao atualizar o avatar.' });
      } finally {
        setAvatarLoading(false);
      }
    };
    reader.readAsDataURL(file);
  }

  const passwordStrength = () => {
    if (!newPassword) return null;
    const hasLength = newPassword.length >= 8;
    const hasNumber = /\d/.test(newPassword);
    const hasLetter = /[a-zA-Z]/.test(newPassword);
    const score = [hasLength, hasNumber, hasLetter].filter(Boolean).length;
    if (score === 3) return { label: 'Forte', color: 'bg-green-500', width: 'w-full' };
    if (score === 2) return { label: 'Regular', color: 'bg-amber-400', width: 'w-2/3' };
    return { label: 'Fraca', color: 'bg-red-400', width: 'w-1/3' };
  };

  const strength = passwordStrength();
  const displayName = profile?.full_name || user?.email || 'User';

  return (
    <div className="flex flex-col h-full overflow-auto">
      <div className="px-8 py-6 border-b border-gray-100 bg-white">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-blue-50 flex items-center justify-center">
            <User className="w-5 h-5 text-blue-600" />
          </div>
          <div>
            <h1 className="text-xl font-semibold text-gray-900">Meu Perfil</h1>
            <p className="text-sm text-gray-400">Gerencie suas informações pessoais e segurança</p>
          </div>
        </div>
      </div>

      <div className="flex-1 px-8 py-6 space-y-6 max-w-2xl">

        {/* Avatar Section */}
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
          <h2 className="text-sm font-semibold text-gray-900 mb-4">Foto de Perfil</h2>
          <div className="flex items-center gap-5">
            <div className="relative w-20 h-20 rounded-full overflow-hidden shrink-0 ring-2 ring-gray-100">
              {avatarPreview ? (
                <img src={avatarPreview} alt="Avatar" className="w-full h-full object-cover" />
              ) : (
                <UserInitials name={profile?.full_name} email={user?.email || ''} />
              )}
              {avatarLoading && (
                <div className="absolute inset-0 bg-black/30 flex items-center justify-center rounded-full">
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                </div>
              )}
            </div>

            <div className="flex-1">
              <p className="text-sm font-medium text-gray-900">{displayName}</p>
              <p className="text-xs text-gray-400 mt-0.5">{user?.email}</p>
              <button
                onClick={() => fileRef.current?.click()}
                disabled={avatarLoading}
                className="mt-3 flex items-center gap-2 px-3.5 py-2 rounded-lg border border-gray-200 text-xs font-medium text-gray-600 hover:border-blue-300 hover:text-blue-600 hover:bg-blue-50 transition-all disabled:opacity-50"
              >
                <Camera className="w-3.5 h-3.5" />
                {avatarLoading ? 'Enviando...' : 'Alterar Foto'}
              </button>
              <input
                ref={fileRef}
                type="file"
                accept="image/*"
                className="hidden"
                onChange={handleFileChange}
              />
            </div>
          </div>
          {avatarAlert && (
            <div className="mt-4">
              <Alert alert={avatarAlert} />
            </div>
          )}
        </div>

        {/* Basic Info Section */}
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
          <h2 className="text-sm font-semibold text-gray-900 mb-4">Informações Básicas</h2>
          <form onSubmit={handleInfoSave} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="col-span-2">
                <label className="block text-xs font-medium text-gray-600 mb-1.5">Nome Completo</label>
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="João Silva"
                  className="w-full px-3.5 py-2.5 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all placeholder:text-gray-400"
                />
              </div>

              <div className="col-span-2">
                <label className="block text-xs font-medium text-gray-600 mb-1.5">
                  E-mail
                  <span className="ml-2 text-gray-400 font-normal">(somente leitura)</span>
                </label>
                <input
                  type="email"
                  value={user?.email || ''}
                  disabled
                  className="w-full px-3.5 py-2.5 rounded-xl border border-gray-100 bg-gray-50 text-sm text-gray-500 cursor-not-allowed"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1.5">Telefone</label>
                <input
                  type="tel"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="+55 11 90000-0000"
                  className="w-full px-3.5 py-2.5 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all placeholder:text-gray-400"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1.5">Departamento</label>
                <input
                  type="text"
                  value={department}
                  onChange={(e) => setDepartment(e.target.value)}
                  placeholder="Engenharia"
                  className="w-full px-3.5 py-2.5 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all placeholder:text-gray-400"
                />
              </div>

              <div className="col-span-2">
                <label className="block text-xs font-medium text-gray-600 mb-1.5">Fuso Horário</label>
                <select
                  value={timezone}
                  onChange={(e) => setTimezone(e.target.value)}
                  className="w-full px-3.5 py-2.5 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all bg-white"
                >
                  {TIMEZONES.map((tz) => (
                    <option key={tz} value={tz}>{tz}</option>
                  ))}
                </select>
              </div>
            </div>

            {infoAlert && <Alert alert={infoAlert} />}

            <div className="flex justify-end pt-1">
              <button
                type="submit"
                disabled={infoLoading}
                className="px-5 py-2.5 rounded-xl bg-blue-600 text-white text-sm font-semibold hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {infoLoading ? 'Salvando...' : 'Salvar Alterações'}
              </button>
            </div>
          </form>
        </div>

        {/* Change Password Section */}
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
          <div className="flex items-center gap-2.5 mb-4">
            <Lock className="w-4 h-4 text-gray-500" />
            <h2 className="text-sm font-semibold text-gray-900">Alterar Senha</h2>
          </div>
          <form onSubmit={handlePasswordSave} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1.5">Senha Atual</label>
              <div className="relative">
                <input
                  type={showCurrent ? 'text' : 'password'}
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  required
                  placeholder="Digite a senha atual"
                  className="w-full px-3.5 py-2.5 pr-10 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all placeholder:text-gray-400"
                />
                <button
                  type="button"
                  onClick={() => setShowCurrent((v) => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  {showCurrent ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1.5">Nova Senha</label>
              <div className="relative">
                <input
                  type={showNew ? 'text' : 'password'}
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  required
                  placeholder="Mín. 8 caracteres, 1 letra, 1 número"
                  className="w-full px-3.5 py-2.5 pr-10 rounded-xl border border-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all placeholder:text-gray-400"
                />
                <button
                  type="button"
                  onClick={() => setShowNew((v) => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  {showNew ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              {strength && (
                <div className="mt-2">
                  <div className="h-1.5 w-full bg-gray-100 rounded-full overflow-hidden">
                    <div className={`h-full rounded-full transition-all ${strength.color} ${strength.width}`} />
                  </div>
                  <p className="text-xs text-gray-400 mt-1">senha {strength.label.toLowerCase()}</p>
                </div>
              )}
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1.5">Confirmar Nova Senha</label>
              <div className="relative">
                <input
                  type={showConfirm ? 'text' : 'password'}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                  placeholder="Repita a nova senha"
                  className={`w-full px-3.5 py-2.5 pr-10 rounded-xl border text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all placeholder:text-gray-400 ${
                    confirmPassword && confirmPassword !== newPassword
                      ? 'border-red-300 bg-red-50/30'
                      : 'border-gray-200'
                  }`}
                />
                <button
                  type="button"
                  onClick={() => setShowConfirm((v) => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  {showConfirm ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
              {confirmPassword && confirmPassword !== newPassword && (
                <p className="text-xs text-red-500 mt-1">As senhas não coincidem</p>
              )}
            </div>

            {pwAlert && <Alert alert={pwAlert} />}

            <div className="flex justify-end pt-1">
              <button
                type="submit"
                disabled={pwLoading || !currentPassword || !newPassword || !confirmPassword}
                className="px-5 py-2.5 rounded-xl bg-blue-600 text-white text-sm font-semibold hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {pwLoading ? 'Atualizando...' : 'Alterar Senha'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
