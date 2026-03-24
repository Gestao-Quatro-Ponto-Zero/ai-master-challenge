import { useState } from "react";
import { AppLayout } from "@/components/layout/app-layout";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Search, Book, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";

const mockArticles = [
  { id: 1, title: "Como resetar credenciais da VPN", category: "Acesso", views: 1205 },
  { id: 2, title: "Configurar novo notebook corporativo", category: "Hardware", views: 843 },
  { id: 3, title: "Solucionar falhas de build Docker", category: "Projeto Interno", views: 650 },
  { id: 4, title: "Checklist de onboarding de RH", category: "Suporte RH", views: 420 },
  { id: 5, title: "Solução de problemas de papel AWS IAM", category: "Acesso", views: 390 },
  { id: 6, title: "Diagrama da rede do escritório", category: "Hardware", views: 215 },
  { id: 7, title: "Solicitar compra de equipamentos", category: "Compra", views: 198 },
  { id: 8, title: "Gerenciar permissões administrativas", category: "Direitos Administrativos", views: 175 },
  { id: 9, title: "Configurar armazenamento em nuvem", category: "Armazenamento", views: 132 },
];

export default function KnowledgeBase() {
  const [search, setSearch] = useState("");

  const filtered = mockArticles.filter(a =>
    !search || a.title.toLowerCase().includes(search.toLowerCase()) || a.category.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <AppLayout>
      <div className="flex flex-col items-center justify-center mb-12 mt-4">
        <h1 className="text-4xl font-display font-bold text-foreground mb-4 text-center" data-testid="text-page-title">Biblioteca Atena</h1>
        <p className="text-muted-foreground text-lg text-center max-w-2xl mb-8">
          Repositório centralizado de conhecimento operacional. A IA sugere automaticamente estes artigos para resolver chamados.
        </p>
        
        <div className="relative w-full max-w-2xl">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-muted-foreground w-5 h-5" />
          <Input 
            placeholder="Buscar nos arquivos..." 
            className="pl-12 h-14 text-lg border-border/50 bg-card/80 backdrop-blur-sm rounded-full focus-visible:ring-secondary"
            value={search}
            onChange={e => setSearch(e.target.value)}
            data-testid="input-search-knowledge"
          />
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filtered.map((article) => (
          <Card key={article.id} className="group hover-elevate transition-colors cursor-pointer border-border/50 bg-card" data-testid={`card-article-${article.id}`}>
            <CardHeader className="pb-3">
              <div className="flex justify-between items-start gap-2 mb-2 flex-wrap">
                <span className="text-[10px] font-semibold uppercase tracking-widest text-secondary bg-secondary/10 px-2 py-1 rounded-md" data-testid={`text-article-category-${article.id}`}>
                  {article.category}
                </span>
                <Book className="w-4 h-4 text-muted-foreground" />
              </div>
              <CardTitle className="text-lg leading-tight" data-testid={`text-article-title-${article.id}`}>
                {article.title}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex justify-between items-center mt-2 gap-2">
                <span className="text-sm text-muted-foreground" data-testid={`text-article-views-${article.id}`}>{article.views} visualizações</span>
                <ArrowRight className="w-4 h-4 text-muted-foreground invisible group-hover:visible text-secondary" />
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </AppLayout>
  );
}
