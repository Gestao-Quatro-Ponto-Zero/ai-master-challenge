import { useState } from "react";
import { useSettings, CLevel, AppUser } from "@/contexts/SettingsContext";
import { MetricTooltip } from "@/components/MetricTooltip";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Settings as SettingsIcon, Plus, Pencil, UserCheck, UserX, Users, Briefcase } from "lucide-react";
import { toast } from "sonner";

const emptyExecForm = { nome: "", cargo: "", email: "", whatsapp: "", ativo: true };
const emptyUserForm: Omit<AppUser, "id"> = { nome: "", email: "", perfil: "", status: "ativo", senha: "" };

const Settings = () => {
  const { cLevels, addCLevel, updateCLevel, toggleCLevel, users, addUser, updateUser, toggleUser } = useSettings();

  // Executives state
  const [execForm, setExecForm] = useState(emptyExecForm);
  const [execEditId, setExecEditId] = useState<string | null>(null);

  // Users state
  const [userForm, setUserForm] = useState(emptyUserForm);
  const [userEditId, setUserEditId] = useState<string | null>(null);

  const handleExecSubmit = () => {
    if (!execForm.nome.trim() || !execForm.cargo.trim()) {
      toast.error("Nome e cargo são obrigatórios.");
      return;
    }
    if (execEditId) {
      updateCLevel(execEditId, execForm);
      toast.success("Executivo atualizado.");
      setExecEditId(null);
    } else {
      addCLevel(execForm);
      toast.success("Executivo cadastrado.");
    }
    setExecForm(emptyExecForm);
  };

  const handleUserSubmit = () => {
    if (!userForm.nome.trim() || !userForm.email.trim()) {
      toast.error("Nome e email são obrigatórios.");
      return;
    }
    if (userEditId) {
      updateUser(userEditId, userForm);
      toast.success("Usuário atualizado.");
      setUserEditId(null);
    } else {
      addUser(userForm);
      toast.success("Usuário cadastrado.");
    }
    setUserForm(emptyUserForm);
  };

  const startExecEdit = (c: CLevel) => {
    setExecEditId(c.id);
    setExecForm({ nome: c.nome, cargo: c.cargo, email: c.email, whatsapp: c.whatsapp, ativo: c.ativo });
  };

  const startUserEdit = (u: AppUser) => {
    setUserEditId(u.id);
    setUserForm({ nome: u.nome, email: u.email, perfil: u.perfil, status: u.status, senha: "" });
  };

  return (
    <div className="space-y-6">
      <MetricTooltip tip="Permite cadastrar executivos e manter a base de contatos usada no fluxo de aprovação.">
        <div className="cursor-default">
          <h1 className="text-2xl font-bold tracking-tight">Configurações</h1>
          <p className="text-muted-foreground text-sm mt-1">Cadastro de usuários e executivos para operação e aprovação</p>
        </div>
      </MetricTooltip>

      <Tabs defaultValue="executivos" className="w-full">
        <TabsList>
          <TabsTrigger value="usuarios" className="gap-1.5">
            <Users className="h-3.5 w-3.5" /> Usuários
          </TabsTrigger>
          <TabsTrigger value="executivos" className="gap-1.5">
            <Briefcase className="h-3.5 w-3.5" /> Executivos
          </TabsTrigger>
        </TabsList>

        {/* USUÁRIOS TAB */}
        <TabsContent value="usuarios" className="space-y-4 mt-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-semibold flex items-center gap-2">
                <SettingsIcon className="h-4 w-4 text-primary" />
                {userEditId ? "Editar Usuário" : "Novo Usuário"}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="grid gap-3 sm:grid-cols-2">
                <div className="space-y-1">
                  <Label className="text-xs">Nome *</Label>
                  <Input placeholder="Ex: Maria Santos" value={userForm.nome} onChange={(e) => setUserForm({ ...userForm, nome: e.target.value })} />
                </div>
                <div className="space-y-1">
                  <Label className="text-xs">Email *</Label>
                  <Input placeholder="email@empresa.com" value={userForm.email} onChange={(e) => setUserForm({ ...userForm, email: e.target.value })} />
                </div>
                <div className="space-y-1">
                  <Label className="text-xs">Perfil</Label>
                  <Input placeholder="Ex: Analista, Admin" value={userForm.perfil} onChange={(e) => setUserForm({ ...userForm, perfil: e.target.value })} />
                </div>
                <div className="space-y-1">
                  <Label className="text-xs">Senha</Label>
                  <Input type="password" placeholder="••••••" value={userForm.senha} onChange={(e) => setUserForm({ ...userForm, senha: e.target.value })} />
                </div>
              </div>
              <div className="flex gap-2">
                <Button onClick={handleUserSubmit} size="sm" className="gap-1.5">
                  <Plus className="h-3.5 w-3.5" />
                  {userEditId ? "Salvar" : "Adicionar"}
                </Button>
                {userEditId && (
                  <Button variant="outline" size="sm" onClick={() => { setUserEditId(null); setUserForm(emptyUserForm); }}>
                    Cancelar
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>

          {users.length === 0 ? (
            <div className="flex items-center justify-center h-24 text-muted-foreground text-sm">
              Nenhum registro encontrado.
            </div>
          ) : (
            <Card>
              <CardContent className="pt-4">
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-border text-muted-foreground">
                        <th className="text-left py-2 px-3 font-medium">Nome</th>
                        <th className="text-left py-2 px-3 font-medium">Email</th>
                        <th className="text-left py-2 px-3 font-medium">Perfil</th>
                        <th className="text-center py-2 px-3 font-medium">Status</th>
                        <th className="text-center py-2 px-3 font-medium">Ações</th>
                      </tr>
                    </thead>
                    <tbody>
                      {users.map((u) => (
                        <tr key={u.id} className="border-b border-border/50 hover:bg-muted/30 transition-colors">
                          <td className="py-2 px-3 font-medium">{u.nome}</td>
                          <td className="py-2 px-3 text-xs">{u.email}</td>
                          <td className="py-2 px-3 text-xs">{u.perfil || "—"}</td>
                          <td className="py-2 px-3 text-center">
                            <Badge variant={u.status === "ativo" ? "default" : "secondary"} className="text-xs">
                              {u.status === "ativo" ? "Ativo" : "Inativo"}
                            </Badge>
                          </td>
                          <td className="py-2 px-3 text-center">
                            <div className="flex items-center justify-center gap-1">
                              <Button variant="ghost" size="sm" className="h-7 w-7 p-0" onClick={() => startUserEdit(u)}>
                                <Pencil className="h-3.5 w-3.5" />
                              </Button>
                              <Button variant="ghost" size="sm" className="h-7 w-7 p-0" onClick={() => toggleUser(u.id)}>
                                {u.status === "ativo" ? <UserX className="h-3.5 w-3.5 text-destructive" /> : <UserCheck className="h-3.5 w-3.5 text-[hsl(var(--chart-up))]" />}
                              </Button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* EXECUTIVOS TAB */}
        <TabsContent value="executivos" className="space-y-4 mt-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-semibold flex items-center gap-2">
                <SettingsIcon className="h-4 w-4 text-primary" />
                {execEditId ? "Editar Executivo" : "Novo Executivo C-Level"}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="grid gap-3 sm:grid-cols-2">
                <div className="space-y-1">
                  <Label className="text-xs">Nome *</Label>
                  <Input placeholder="Ex: João Silva" value={execForm.nome} onChange={(e) => setExecForm({ ...execForm, nome: e.target.value })} />
                </div>
                <div className="space-y-1">
                  <Label className="text-xs">Cargo *</Label>
                  <Input placeholder="Ex: CEO" value={execForm.cargo} onChange={(e) => setExecForm({ ...execForm, cargo: e.target.value })} />
                </div>
                <div className="space-y-1">
                  <Label className="text-xs">Email</Label>
                  <Input placeholder="email@empresa.com" value={execForm.email} onChange={(e) => setExecForm({ ...execForm, email: e.target.value })} />
                </div>
                <div className="space-y-1">
                  <Label className="text-xs">WhatsApp</Label>
                  <Input placeholder="+55 11 99999-9999" value={execForm.whatsapp} onChange={(e) => setExecForm({ ...execForm, whatsapp: e.target.value })} />
                </div>
              </div>
              <div className="flex gap-2">
                <Button onClick={handleExecSubmit} size="sm" className="gap-1.5">
                  <Plus className="h-3.5 w-3.5" />
                  {execEditId ? "Salvar" : "Adicionar"}
                </Button>
                {execEditId && (
                  <Button variant="outline" size="sm" onClick={() => { setExecEditId(null); setExecForm(emptyExecForm); }}>
                    Cancelar
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>

          {cLevels.length === 0 ? (
            <div className="flex items-center justify-center h-24 text-muted-foreground text-sm">
              Nenhum registro encontrado.
            </div>
          ) : (
            <Card>
              <CardContent className="pt-4">
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-border text-muted-foreground">
                        <th className="text-left py-2 px-3 font-medium">Nome</th>
                        <th className="text-left py-2 px-3 font-medium">Cargo</th>
                        <th className="text-left py-2 px-3 font-medium">Email</th>
                        <th className="text-left py-2 px-3 font-medium">WhatsApp</th>
                        <th className="text-center py-2 px-3 font-medium">Status</th>
                        <th className="text-center py-2 px-3 font-medium">Ações</th>
                      </tr>
                    </thead>
                    <tbody>
                      {cLevels.map((c) => (
                        <tr key={c.id} className="border-b border-border/50 hover:bg-muted/30 transition-colors">
                          <td className="py-2 px-3 font-medium">{c.nome}</td>
                          <td className="py-2 px-3">{c.cargo}</td>
                          <td className="py-2 px-3 text-xs">{c.email || "—"}</td>
                          <td className="py-2 px-3 text-xs">{c.whatsapp || "—"}</td>
                          <td className="py-2 px-3 text-center">
                            <Badge variant={c.ativo ? "default" : "secondary"} className="text-xs">
                              {c.ativo ? "Ativo" : "Inativo"}
                            </Badge>
                          </td>
                          <td className="py-2 px-3 text-center">
                            <div className="flex items-center justify-center gap-1">
                              <Button variant="ghost" size="sm" className="h-7 w-7 p-0" onClick={() => startExecEdit(c)}>
                                <Pencil className="h-3.5 w-3.5" />
                              </Button>
                              <Button variant="ghost" size="sm" className="h-7 w-7 p-0" onClick={() => toggleCLevel(c.id)}>
                                {c.ativo ? <UserX className="h-3.5 w-3.5 text-destructive" /> : <UserCheck className="h-3.5 w-3.5 text-[hsl(var(--chart-up))]" />}
                              </Button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default Settings;
