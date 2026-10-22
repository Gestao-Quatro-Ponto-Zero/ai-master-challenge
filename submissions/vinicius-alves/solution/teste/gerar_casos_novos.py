"""Gera 30 tickets NOVOS pra medir o motor de verdade.

O motor foi escrito olhando os 80 tickets de casos_teste.csv, então acertar
eles não prova nada. Estes 30 foram escritos depois do motor pronto, com
frases diferentes das que as regras conhecem, e o motor não foi ajustado
olhando eles. O gabarito é do Paulo Vinicius, dado às cegas.

Saídas: casos_novos.csv e armadilhas_novos.csv (abrir só depois do gabarito).

Uso (da pasta submissions/vinicius-alves):
    .venv/bin/python solution/teste/gerar_casos_novos.py
"""
import csv

from gerar_casos import AQUI, TIPO_D1, confere_com_d1

# Mesmo formato de gerar_casos.CASOS.
CASOS_NOVOS = [
    # ---------------- REEMBOLSO ----------------
    ("N01", "Reembolso", "Delivery problem", "Chat", "Google Pixel", 4299, 3, "Entregue", 0,
     "Pedi o Pixel preto e veio branco. Quero devolver e receber o dinheiro.",
     "Produto diferente do pedido, mas dentro dos 7 dias. Arrependimento ou apurar o erro?"),
    ("N02", "Reembolso", "Refund request", "Email", "Sony 4K HDR TV", 3999, 6, "Entregue", 0,
     "Bom dia. A TV é maior do que eu imaginava e não coube na parede. Ainda dá tempo de devolver?",
     "Arrependimento simples, sem defeito, dentro dos 7 dias."),
    ("N03", "Reembolso", "Refund request", "Social media", "Nintendo Switch", 2199, 25, "Devolvido ao estoque", 2,
     "Vocês são uma piada. Devolvi faz três semanas e nada. Absurdo.",
     "Irritação com palavras que o leitor não conhece (piada, absurdo)."),
    ("N04", "Reembolso", "Refund request", "Chat", "Dell XPS", 8999, 12, "Entregue", 0,
     "Minha mãe está internada e eu preciso do dinheiro do notebook pra pagar o hospital. Comprei há 12 dias, dá pra devolver?",
     "Momento difícil escrito de outro jeito, fora dos 7 dias."),
    ("N05", "Reembolso", "Delivery problem", "Email", "Canon EOS", 5499, 2, "Entregue", 0,
     "A caixa chegou amassada e a lente veio rachada. Tenho foto. Quero meu dinheiro.",
     "Avaria no transporte com prova, dentro dos 7 dias."),
    ("N06", "Reembolso", "Refund request", "Chat", "Apple AirPods", 1899, 15, "Devolvido ao estoque", 1,
     "Já devolvi os fones. Quanto tempo leva pro estorno aparecer?",
     "Dúvida de prazo de estorno. A IA não pode dar data."),

    # ---------------- PROBLEMA TÉCNICO ----------------
    ("N07", "Problema técnico", "Hardware issue", "Chat", "Samsung Galaxy", 1199, 120, "Entregue", 0,
     "O carregador do celular ficou muito quente e derreteu a ponta. Tá com um cheiro estranho.",
     "Risco físico escrito com palavras que o leitor não conhece (derreteu, muito quente)."),
    ("N08", "Problema técnico", "Hardware issue", "Email", "HP Pavilion", 3299, 4, "Entregue", 0,
     "O notebook não reconhece o carregador, a luz nem acende. Chegou segunda.",
     "Defeito em até 7 dias, escrito de outro jeito."),
    ("N09", "Problema técnico", "Product setup", "Chat", "Philips Hue Lights", 699, 20, "Entregue", 0,
     "Como eu faço pra configurar as lâmpadas pelo aplicativo?",
     "Dúvida simples."),
    ("N10", "Problema técnico", "Data loss", "Phone", "Amazon Kindle", 549, 60, "Entregue", 0,
     "Meu Kindle apagou todos os livros que eu tinha baixado. Perdi tudo, tô muito chateada.",
     "Perda de dados, cliente triste mas não irritado. Assunto que nenhum processo cobre."),
    ("N11", "Problema técnico", "Display issue", "Chat", "Microsoft Surface", 6999, 30, "Entregue", 3,
     "De novo isso. Terceiro chamado e a tela continua piscando. Me passa pra alguém que resolva.",
     "Pede pessoa com outras palavras, recorrente."),
    ("N12", "Problema técnico", "Software bug", "Email", "Garmin Forerunner", 1899, 200, "Entregue", 0,
     "Meu relógio está mostrando batimento de 40 durante a corrida. Isso tá certo?",
     "Saúde escrita de outro jeito (batimento no singular)."),

    # ---------------- CANCELAMENTO ----------------
    ("N13", "Cancelamento", "Cancellation request", "Chat", "Bose SoundLink Speaker", 1299, 0, "Pagamento aprovado, não enviado", 0,
     "Comprei errado, era pra ser a azul. Cancela pra mim que eu compro de novo?",
     "Caso claro: não enviado."),
    ("N14", "Cancelamento", "Cancellation request", "Email", "MacBook Pro", 15999, 3, "Enviado", 0,
     "Desisti da compra. Como faço pra cancelar?",
     "Já enviado."),
    ("N15", "Cancelamento", "Cancellation request", "Chat", "Adobe Photoshop", 109, 90, "Assinatura mensal ativa", 0,
     "Quero cancelar o Photoshop, não uso mais.",
     "Cancelamento simples de assinatura. Testa se o motor tem o processo."),
    ("N16", "Cancelamento", "Delivery problem", "Social media", "iPhone", 2999, 15, "Atrasado (prazo vencido há 5 dias)", 2,
     "Cancela essa compra agora, tô cansado de esperar e ninguém resolve nada.",
     "Irritação com outras palavras, pedido atrasado."),
    ("N17", "Cancelamento", "Account access", "Email", "", 0, None, "Conta ativa", 0,
     "Quero excluir meu cadastro e que vocês parem de me mandar e-mail.",
     "LGPD sem falar LGPD."),
    ("N18", "Cancelamento", "Cancellation request", "Chat", "Xbox", 3999, 1, "Pagamento aprovado, não enviado", 0,
     "Pode cancelar? Minha esposa disse que se eu comprar esse videogame ela me mata kkkk",
     "Brincadeira com palavra pesada. Não pode virar luto nem ameaça."),

    # ---------------- COBRANÇA ----------------
    ("N19", "Cobrança", "Payment issue", "Chat", "", 0, None, "Sem pedido identificado", 0,
     "Tem uma compra de 899 reais no meu cartão que não fui eu que fiz.",
     "Fraude escrita de outro jeito."),
    ("N20", "Cobrança", "Payment issue", "Email", "Samsung Soundbar", 1999, 10, "Entregue", 0,
     "Preciso da nota fiscal no CNPJ da minha empresa, saiu no meu CPF.",
     "Correção de nota fiscal. Nenhum processo cobre."),
    ("N21", "Cobrança", "Payment issue", "Chat", "Amazon Echo", 499, 0, "Carrinho", 0,
     "Esse cupom de 10% que vocês mandaram por e-mail não está funcionando.",
     "Cupom da própria loja que não funciona. Exceção ou regra escrita?"),
    ("N22", "Cobrança", "Payment issue", "Social media", "Microsoft Office", 45.9, 40, "Assinatura mensal ativa", 1,
     "Me cobraram duas vezes a assinatura esse mês. Já mandei o print ontem e nada.",
     "Cobrança duplicada, segundo contato, um pouco impaciente, em público."),
    ("N23", "Cobrança", "Payment issue", "Email", "Lenovo ThinkPad", 6599, 20, "Entregue", 0,
     "Vou no Procon se não resolverem a cobrança do frete que não era pra ter.",
     "Ameaça."),
    ("N24", "Cobrança", "Payment issue", "Chat", "Sony PlayStation", 3499, 5, "Entregue", 0,
     "Paguei no Pix e ainda aparece como pendente, mas o produto já chegou. Tá tudo certo?",
     "Dúvida simples de pagamento."),

    # ---------------- DÚVIDA DE PRODUTO ----------------
    ("N25", "Dúvida de produto", "Product compatibility", "Chat", "LG OLED", 7999, None, "Pré-venda", 0,
     "Essa TV tem entrada pra antena digital?",
     "Ficha técnica."),
    ("N26", "Dúvida de produto", "Product compatibility", "Chat", "Nintendo Switch Pro Controller", 449, None, "Pré-venda", 0,
     "Funciona no PC?",
     "Pergunta curta, mas com produto claro. Não é falta de informação."),
    ("N27", "Dúvida de produto", "Product recommendation", "Email", "Roomba Robot Vacuum", 2899, None, "Pré-venda", 0,
     "Tenho dois gatos. O robô aspira pelo de gato direitinho? Se não aspirar, vocês aceitam devolver?",
     "Informação + política de devolução."),
    ("N28", "Dúvida de produto", "Product recommendation", "Chat", "Fitbit Charge", 899, None, "Pré-venda", 0,
     "Meu médico pediu pra eu controlar a pressão. Esse relógio mede pressão?",
     "Pergunta de recurso do produto com contexto de saúde."),
    ("N29", "Dúvida de produto", "Product recommendation", "Chat", "Samsung Galaxy", 4999, None, "Pré-venda", 0,
     "Vocês parcelam em 24x? Se fizer em 24x eu fecho agora.",
     "Pede condição que pode não existir."),
    ("N30", "Dúvida de produto", "Product recommendation", "Social media", "GoPro Hero", 2599, None, "Pré-venda", 1,
     "Mandei mensagem ontem perguntando se tem estoque e ninguém respondeu. Assim fica difícil comprar de vocês.",
     "Irritação leve e venda em risco, sem palavra forte."),
]


def main():
    confere_com_d1(CASOS_NOVOS)
    cab = ["id", "tipo", "tipo_d1", "assunto_d1", "canal", "produto", "valor_rs", "dias_desde_compra",
           "status_pedido", "contatos_anteriores", "mensagem_do_cliente"]
    with open(AQUI / "casos_novos.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(cab)
        for c in CASOS_NOVOS:
            id_, tipo, assunto, canal, prod, valor, dias, status, contatos, texto, _ = c
            w.writerow([id_, tipo, TIPO_D1[tipo], assunto, canal, prod, valor or "",
                        "" if dias is None else dias, status, contatos, texto])
    with open(AQUI / "armadilhas_novos.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["id", "o_que_o_ticket_tenta_testar"])
        for c in CASOS_NOVOS:
            w.writerow([c[0], c[-1]])
    print(f"{len(CASOS_NOVOS)} casos novos gerados")


if __name__ == "__main__":
    main()
