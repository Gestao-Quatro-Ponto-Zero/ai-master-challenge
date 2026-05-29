"""
Popula a knowledge base (support_tickets_kb) com FAQ real do G4 Educação.

Conteúdo baseado na Base de Conhecimento oficial do G4 Educação (seção 7 — Suporte
Operacional) mais informações dos programas presenciais, G4 Pass e G4 Tools.

Uso:
  cd submissions/pedro-henrique-silva/solution
  source .venv312/bin/activate
  python scripts/populate_kb.py --replace
"""

from __future__ import annotations

import os
import sys
from typing import Any

from openai import OpenAI
from supabase import create_client

TABLE       = "support_tickets_kb"
EMBED_MODEL = "text-embedding-3-small"

KB_ARTICLES: list[dict[str, Any]] = [

    # ── 7.1 Pagamento e Faturamento ──────────────────────────────────────────
    {
        "source_ticket_id": "g4-pay-001",
        "description": "Realizei o pagamento do curso mas não recebi a confirmação ou acesso",
        "resolution": (
            "Verifique sua caixa de entrada e a pasta de spam/lixo eletrônico para "
            "e-mails de confirmação do G4 Educação. Certifique-se de que o e-mail "
            "utilizado na compra está correto. Pagamentos via boleto podem levar até "
            "3 dias úteis para processar. Pagamentos via cartão de crédito ou PIX são "
            "processados em minutos — se o acesso não foi liberado, entre em contato "
            "com o suporte informando o e-mail de compra e o comprovante de pagamento."
        ),
        "category": "Purchase", "priority": "high", "channel": "Web",
    },
    {
        "source_ticket_id": "g4-pay-002",
        "description": "Pagamento recusado mas o valor foi debitado do cartão",
        "resolution": (
            "Isso ocorre quando a operadora do cartão faz uma reserva de limite, mas a "
            "transação não foi concluída no sistema G4. O valor é estornado "
            "automaticamente em alguns dias úteis. Se não aparecer na próxima fatura, "
            "entre em contato com o suporte enviando o comprovante do débito. Para "
            "concluir a compra, use outro método de pagamento (PIX ou outro cartão)."
        ),
        "category": "Purchase", "priority": "medium", "channel": "Web",
    },
    {
        "source_ticket_id": "g4-pay-003",
        "description": "Como alterar a forma de pagamento da assinatura do G4 Pass",
        "resolution": (
            "Acesse a área do aluno, vá em 'Minha Conta' ou 'Assinaturas' e selecione "
            "'Atualizar método de pagamento'. Você pode trocar o cartão de crédito ou "
            "a forma de pagamento diretamente na plataforma. Se encontrar dificuldades, "
            "o suporte pode enviar um link seguro para atualização dos dados. O G4 Pass "
            "custa R$2.997 à vista ou 12x de R$249,75 e dá acesso vitalício a mais de "
            "100 cursos e 400 horas de conteúdo."
        ),
        "category": "Purchase", "priority": "medium", "channel": "Web",
    },
    {
        "source_ticket_id": "g4-pay-004",
        "description": "Não recebi a nota fiscal da minha compra no G4 Educação",
        "resolution": (
            "As notas fiscais são emitidas automaticamente e enviadas ao e-mail "
            "cadastrado na compra, geralmente alguns dias após a confirmação do "
            "pagamento. Verifique a pasta de spam. Se ainda assim não encontrar, "
            "solicite a segunda via ao suporte informando o CPF/CNPJ utilizado na "
            "compra."
        ),
        "category": "Purchase", "priority": "low", "channel": "Email",
    },

    # ── 7.2 Acesso a Cursos e Plataforma ────────────────────────────────────
    {
        "source_ticket_id": "g4-access-001",
        "description": "Comprei um curso mas não consigo acessar a plataforma ou os materiais",
        "resolution": (
            "Após a confirmação do pagamento, você receberá um e-mail com as instruções "
            "de acesso à plataforma. Se as credenciais não funcionarem, use a opção "
            "'Esqueci minha senha' na página de login com o mesmo e-mail da compra. "
            "Verifique spam e caixa de entrada. Se o problema persistir após redefinição "
            "de senha, entre em contato com o suporte informando o e-mail e comprovante "
            "de compra."
        ),
        "category": "Access", "priority": "high", "channel": "Web",
    },
    {
        "source_ticket_id": "g4-access-002",
        "description": "Vídeo não carrega, erro no PDF ou material do curso incompleto",
        "resolution": (
            "Tente: (1) Limpar o cache do navegador e recarregar a página. "
            "(2) Acessar por uma aba anônima. (3) Usar um navegador diferente (Chrome, "
            "Firefox, Edge). (4) Verificar sua conexão com a internet. Se o problema "
            "for em uma aula específica, informe ao suporte o nome do curso, o módulo "
            "e a aula exata para que a equipe técnica corrija."
        ),
        "category": "Access", "priority": "medium", "channel": "Web",
    },
    {
        "source_ticket_id": "g4-access-003",
        "description": "Acesso ao curso expirou e ainda não terminei o conteúdo",
        "resolution": (
            "O tempo de acesso varia por programa: 6 meses para G4 Gestão e Estratégia "
            "e G4 Sales, 12 meses para G4 Gestão de Pessoas, acesso vitalício para o "
            "G4 Pass. Após o término, o acesso é bloqueado automaticamente. Para "
            "extensão de prazo, consulte as políticas do seu curso ou entre em contato "
            "com o suporte para verificar a possibilidade de renovação ou upgrade para "
            "o G4 Pass (acesso vitalício)."
        ),
        "category": "Access", "priority": "medium", "channel": "Web",
    },
    {
        "source_ticket_id": "g4-access-004",
        "description": "Como acessar a comunidade de alunos Alumni do G4",
        "resolution": (
            "O acesso à comunidade Alumni é concedido aos alunos dos programas "
            "presenciais e online elegíveis. As instruções (geralmente via plataforma "
            "específica, WhatsApp ou Telegram) são enviadas por e-mail após a conclusão "
            "do programa ou durante o onboarding. Caso não tenha recebido, solicite o "
            "link de acesso ao suporte informando o programa que você cursou."
        ),
        "category": "Access", "priority": "low", "channel": "Web",
    },

    # ── 7.3 Reembolsos e Cancelamentos ──────────────────────────────────────
    {
        "source_ticket_id": "g4-refund-001",
        "description": "Como solicitar reembolso de um curso do G4 Educação",
        "resolution": (
            "O G4 Educação segue o Código de Defesa do Consumidor: direito de "
            "arrependimento em até 7 dias após a compra para cursos online. Para "
            "solicitar reembolso dentro deste prazo, entre em contato com o suporte "
            "informando o e-mail de compra e o motivo do cancelamento. O estorno será "
            "processado de acordo com a forma de pagamento original."
        ),
        "category": "Purchase", "priority": "high", "channel": "Web",
    },
    {
        "source_ticket_id": "g4-refund-002",
        "description": "Como cancelar a assinatura do G4 Pass e parar cobranças",
        "resolution": (
            "O cancelamento da renovação automática do G4 Pass pode ser feito "
            "diretamente na área do aluno, na seção 'Assinaturas'. O cancelamento "
            "evita cobranças futuras, mas você mantém o acesso até o fim do período "
            "já pago. Para dúvidas sobre cancelamento imediato com estorno proporcional, "
            "consulte os termos de uso ou entre em contato com o suporte."
        ),
        "category": "Purchase", "priority": "medium", "channel": "Web",
    },
    {
        "source_ticket_id": "g4-refund-003",
        "description": "Comprei ingresso presencial mas não poderei comparecer — transferência ou remarcação",
        "resolution": (
            "Transferências de titularidade e remarcações para turmas futuras são "
            "geralmente permitidas, desde que solicitadas com antecedência mínima "
            "conforme os termos do contrato do programa específico. Entre em contato "
            "com o suporte o mais breve possível para verificar condições e taxas "
            "aplicáveis. Os programas presenciais incluem G4 Gestão e Estratégia (4 dias), "
            "G4 Traction (3 dias), G4 Sales (3 dias) e G4 Gestão de Pessoas (3 dias)."
        ),
        "category": "Purchase", "priority": "medium", "channel": "Phone",
    },

    # ── 7.4 Certificados e Dúvidas Gerais ───────────────────────────────────
    {
        "source_ticket_id": "g4-cert-001",
        "description": "Concluí o curso mas meu certificado do G4 não foi emitido",
        "resolution": (
            "Certifique-se de que todas as aulas e módulos foram marcados como "
            "concluídos na plataforma. O certificado é gerado automaticamente após "
            "100% de progresso. Se você completou tudo e o certificado não está "
            "disponível na área do aluno, entre em contato com o suporte para emissão "
            "manual, informando o nome do curso e o e-mail cadastrado."
        ),
        "category": "Other", "priority": "medium", "channel": "Web",
    },
    {
        "source_ticket_id": "g4-cert-002",
        "description": "Nome incorreto no certificado do G4 Educação",
        "resolution": (
            "O nome no certificado é gerado com base nos dados do seu perfil na "
            "plataforma. Acesse 'Minha Conta', corrija seu nome completo e salve as "
            "alterações. Em seguida, tente gerar o certificado novamente. Se o erro "
            "persistir, o suporte pode fazer a correção manual. Os certificados do G4 "
            "são reconhecidos pelo mercado."
        ),
        "category": "Other", "priority": "low", "channel": "Web",
    },
    {
        "source_ticket_id": "g4-cert-003",
        "description": "G4 Educação oferece descontos corporativos ou compras em grupo",
        "resolution": (
            "Sim, o G4 Educação possui condições especiais para empresas que desejam "
            "treinar suas equipes. Para pacotes corporativos, entre em contato com a "
            "equipe comercial através do site ou solicite atendimento especializado ao "
            "suporte. O G4 já impactou mais de 19.000 alunos e 15.000 empresas com "
            "seus programas de gestão e liderança."
        ),
        "category": "Other", "priority": "low", "channel": "Web",
    },

    # ── Informações de Programas (para deflexão rápida) ──────────────────────
    {
        "source_ticket_id": "g4-prog-pass",
        "description": "O que é o G4 Pass e o que está incluído",
        "resolution": (
            "O G4 Pass é o acesso vitalício a todos os cursos online do G4 (atuais e "
            "futuros). Inclui: +100 cursos, +400 horas de conteúdo, +100 ferramentas. "
            "Valor: R$2.997 à vista ou 12x de R$249,75. Áreas cobertas: Inteligência "
            "Artificial, Marketing, Vendas, Gestão, Finanças, Liderança. Exemplos: "
            "G4 Marketing Estratégico, Fundamentos em Vendas, OKRs na Prática, "
            "Transformação Digital, Introdução à IA para negócios."
        ),
        "category": "Other", "priority": "low", "channel": "Web",
    },
    {
        "source_ticket_id": "g4-prog-gestao",
        "description": "Como funciona o programa G4 Gestão e Estratégia",
        "resolution": (
            "O G4 Gestão e Estratégia é um programa presencial de 4 dias para "
            "fundadores e C-levels de empresas com faturamento acima de R$10 milhões. "
            "NPS: 91/100. Metodologia em 5 pilares: Estratégia e Gestão, Comando, "
            "Escala, Legado e Aliança. Inclui 6 meses de acesso Alumni. Foco em "
            "transformar visão em crescimento previsível e sustentável. Cases: GMPR "
            "dobrou crescimento em 6 meses, GEOvendas dobrou faturamento em 1 ano."
        ),
        "category": "Other", "priority": "low", "channel": "Web",
    },
    {
        "source_ticket_id": "g4-prog-traction",
        "description": "Como funciona o programa G4 Traction",
        "resolution": (
            "O G4 Traction é uma imersão presencial de 3 dias para donos e C-levels "
            "com faturamento entre R$1MM e R$10MM. NPS: 82/100. Cobre 7 pilares: "
            "Gestão Financeira, Gestão e Execução, Operações e Processos, Marketing e "
            "Aquisição, Vendas Estratégicas, Experiência do Cliente, e Cultura e "
            "Liderança. Inclui 6 meses de acesso Alumni. Ideal para sair do operacional "
            "e estruturar o negócio para escalar."
        ),
        "category": "Other", "priority": "low", "channel": "Web",
    },
    {
        "source_ticket_id": "g4-prog-sales",
        "description": "Como funciona o programa G4 Sales",
        "resolution": (
            "O G4 Sales é um programa presencial de 3 dias para fundadores e C-levels "
            "com faturamento acima de R$10 milhões. NPS: 89/100. Metodologia: "
            "Arquitetura de Receita, Atração e Qualificação de Leads, Gestão de "
            "Pipeline e Gestão de Carteira. Inclui mentoria em grupo, networking de "
            "alto nível e suporte contínuo. Case: PDV Print Embalagens saiu de R$80k "
            "para R$3M em vendas pelo WhatsApp após o programa."
        ),
        "category": "Other", "priority": "low", "channel": "Web",
    },
    {
        "source_ticket_id": "g4-prog-tools",
        "description": "O que é o G4 Tools e quais soluções oferece",
        "resolution": (
            "O G4 Tools é um marketplace com curadoria de serviços e tecnologia "
            "exclusivo do G4 Educação. Conecta a base de clientes do G4 com as "
            "melhores soluções do mercado em: CRM (gestão de clientes), ERP "
            "(sistemas integrados), Marketing, Vendas e Gestão. Diferenciais: "
            "negociações exclusivas com grandes players, curadoria especializada e "
            "confiança respaldada por mais de 55 mil clientes do grupo."
        ),
        "category": "Other", "priority": "low", "channel": "Web",
    },
    {
        "source_ticket_id": "g4-prog-online",
        "description": "Programas online e híbridos disponíveis no G4 Educação",
        "resolution": (
            "Programas online: G4 Mentoring (até 12 meses, sessões individuais mensais, "
            "NPS 8.9), G4 Marketing Estratégico (20h, 100% online, NPS 9.1), G4 "
            "Startups (8 semanas, NPS 9.3). Programas híbridos (G4 Sprints): "
            "Implementação em IA (3 dias em SP, NPS 8.9), Planejamento Estratégico "
            "(NPS 8.2), Planejamento Tático (NPS 9.1), Finanças (NPS 9.1). Todos com "
            "acesso à plataforma exclusiva para alunos."
        ),
        "category": "Other", "priority": "low", "channel": "Web",
    },
]


def main() -> None:
    url        = os.getenv("NEXT_PUBLIC_SUPABASE_URL")
    svc_key    = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    missing = [k for k, v in {
        "NEXT_PUBLIC_SUPABASE_URL": url,
        "SUPABASE_SERVICE_ROLE_KEY": svc_key,
        "OPENAI_API_KEY": openai_key,
    }.items() if not v]
    if missing:
        sys.exit(f"[kb] Variáveis ausentes: {', '.join(missing)}")

    replace = "--replace" in sys.argv
    supabase = create_client(url, svc_key)      # type: ignore[arg-type]
    openai   = OpenAI(api_key=openai_key)

    if replace:
        print("[kb] --replace: removendo todos os artigos existentes…")
        supabase.table(TABLE).delete().neq("id", 0).execute()
        to_insert = KB_ARTICLES
    else:
        existing = supabase.table(TABLE).select("source_ticket_id").execute()
        existing_ids: set[str] = {r["source_ticket_id"] for r in (existing.data or [])}
        to_insert = [a for a in KB_ARTICLES if a["source_ticket_id"] not in existing_ids]
        print(f"[kb] Artigos existentes: {len(existing_ids)} | Novos: {len(to_insert)}")

    if not to_insert:
        print("[kb] Nada a inserir.")
        return

    for i, article in enumerate(to_insert, 1):
        embed_text = f"{article['description']}\n{article['resolution']}"
        embedding = openai.embeddings.create(
            model=EMBED_MODEL,
            input=embed_text,
        ).data[0].embedding

        supabase.table(TABLE).upsert(
            {**article, "embedding": embedding},
            on_conflict="source_ticket_id",
        ).execute()

        print(f"  [{i:02d}/{len(to_insert)}] {article['source_ticket_id']}")

    print(f"\n[kb] Concluído — {len(to_insert)} artigos inseridos em '{TABLE}'.")


if __name__ == "__main__":
    main()
