# Design System do HubSpot

Baseado na análise completa do site, aqui está o Design System extraído:

## 🎨 **PALETA DE CORES**

### Cores Primárias
- **Orange (Laranja Vibrante)**: `#FF5630` - Cor principal da marca
  - Usado em: Logo, botões primários, destaques, CTA principal
  - Aplicações: "Get a demo", Links de ação principais

- **Branco**: `#FFFFFF` - Fundo padrão
  - Espaço negativo, cards, backgrounds

- **Preto/Cinza Escuro**: `#1F2937` / `#111111` - Texto principal
  - Headlines, corpo de texto, elementos de alta legibilidade

### Cores Secundárias
- **Cinza Claro**: `#F3F4F6` / `#E5E7EB` - Fundos alternativos
  - Seções, cards, divisores sutis

- **Rosa Pastel**: `#FCE7D5` - Fundos de destaque suave
  - Seções de chamada (ex: "Built-in AI agents")

- **Ícones Coloridos**: Ícones em tons de laranja `#FF5630` com variações

## 📝 **TIPOGRAFIA**

### Fontes
- **Sans-Serif Moderna** (aparenta ser similar a Inter, Segoe UI ou system fonts)
- Peso: 400 (Regular), 600 (Semi-bold), 700 (Bold)

### Hierarquia

| Elemento | Tamanho | Peso | Uso |
|----------|---------|------|-----|
| **Hero Headline** | ~56-64px | 700 Bold | "Where go-to-market teams go to..." |
| **Section Title** | ~40px | 700 Bold | "The HubSpot Customer Platform" |
| **Hub Names** | ~28-32px | 700 Bold | "Marketing Hub®", "Sales Hub®" |
| **Body Copy** | 16-18px | 400 Regular | Descrições, subtítulos |
| **Small Text** | 14px | 400 Regular | Labels, metadata |
| **Button Text** | 16px | 600 Semi-bold | "Get a demo", "Learn more" |

## 🔘 **COMPONENTES PRINCIPAIS**

### 1. **Buttons (Botões)**

**Botão Primário (Filled)**
- Background: `#FF5630` (Laranja)
- Text: Branco, bold
- Padding: `16px 32px` (aproximadamente)
- Border-radius: `6-8px`
- Exemplo: "Get a demo"

**Botão Secundário (Outlined)**
- Background: Transparente/Branco
- Border: `2px solid #FF5630`
- Text: `#FF5630`
- Padding: `14px 30px`
- Border-radius: `6-8px`
- Exemplo: "Get started free"

**Botão Tertiary (Text)**
- Background: Transparente
- Text: `#FF5630`
- Underline ou arrow: `→`
- Exemplo: "Learn more"

### 2. **Cards**

**Product Hub Cards**
- Background: Branco com border subtil
- Border: `1px solid #E5E7EB`
- Border-radius: `12px`
- Padding: `24px`
- Shadow: Sutil (elevação baixa)
- Layout: 2 colunas em desktop

**Card Interior**
- Ícone: Colorido (laranja/multicolor)
- Título: 24px, bold
- Lista com checkmarks: Preto, 16px
- Link "Learn more": Laranja com arrow

### 3. **Navigation / Header**

**Header**
- Background: Branco
- Height: ~60-70px
- Logo: HubSpot com "S" estilizado em laranja
- Menu Button: Ícone hambúrguer (desktop/tablet)

**Navigation Items**
- Texto preto
- Espaçamento horizontal generoso
- Estilo simples, sem destaque visual até hover

### 4. **Hero Section**

**Layout**
- Full-width com imagem de fundo
- Overlay escuro subtil (rgba)
- Texto branco
- CTA duplo (Primário + Secundário)

**Elementos**
- Super-headline: "HUBSPOT CUSTOMER PLATFORM"
- Headline principal: Large, bold, white
- Subheadline: 18px, white, 60% opacity
- Dois botões lado a lado

### 5. **Carousels/Sliders**

- Previous/Next buttons com setas
- Dot indicators (círculos pretos/cinzas)
- Auto-play com pause button
- Smooth transitions

### 6. **Testimonials**

- Quote text: Itálico
- Author name: Bold, preto
- Company/Title: 14px, cinza
- Grid layout: Tabulação por segmento (Enterprise/Mid-Market/Small)

### 7. **Badges/Labels**

**AI Badge**
- Icon: Spark/lightning laranja
- Text: "Powered by AI"
- Background: Branco/transparente
- Border: Subtil

**Product Badges**
- Trademark symbols: ®, ™
- Ícones específicos por hub (lightning, star, etc.)

## 📐 **LAYOUT & SPACING**

### Grid System
- **Desktop**: 12 colunas
- **Tablet**: 8 colunas
- **Mobile**: 4 colunas

### Espaçamento (Padding/Margin)
- Seções: 80px vertical (desktop), 40px (mobile)
- Cards: 24px interno
- Elementos inline: 8px, 12px, 16px, 24px, 32px
- Gap entre colunas: 24px

### Width
- Max-width container: ~1200-1280px
- Margens laterais: 24px (desktop), 16px (tablet), 16px (mobile)

## 🎭 **PADRÕES DE DESIGN**

### 1. **Alternância de Seções**
- Seções alternadas: Branco ↔️ Cinza claro
- Cria ritmo visual e hierarquia

### 2. **Iconografia**
- Ícones coloridos (laranja, multicolor)
- Checkmarks em listas (laranja)
- Setas para CTAs
- Tamanho: 24-48px conforme contexto

### 3. **Chamadas de Ação (CTAs)**

**Padrão de CTA Duplo**
- Botão primário (laranja) + Botão secundário (outlined)
- Sempre na mesma altura
- Repetido em múltiplas seções

### 4. **Animações**
- Hover effects em links: Subtle color change
- Carousels: Smooth fade/slide transitions
- Chat widget: Pulse animation do avatar

### 5. **Consistência de Conteúdo**

**Product Listing Pattern**
- Ícone + Título (com ® ou ™)
- 2-3 bullet points de benefícios
- Link "Learn more" com arrow
- Mantém consistência visual

### 6. **Social Proof**
- Logos de clientes (eBay, DoorDash, Reddit)
- Números destacados (288,000 customers)
- G2 Awards com badges específicas
- Testimonials com contexto (empresa/cargo)

## 🎯 **COMPONENTES INTERATIVOS**

### Chat Widget
- Avatar circular com ícone HubBot
- Background preto escuro
- Float bottom-right
- Mensagem de apresentação
- Botões de ação predefinidos

### Tabs
- Background branco
- Texto preto/cinza
- Selected tab: Texto preto, bold
- No underline visível (apenas mudança de peso)

### Form Elements
- Inputs com border subtil
- Placeholder: Cinza claro
- Focus state: Border laranja

## 📱 **RESPONSIVIDADE**

- **Desktop**: Multi-coluna, espaçamento generoso
- **Tablet**: 2 colunas, espaçamento reduzido
- **Mobile**: Stack vertical, espaçamento comprimido
- Carousels se adaptam em mobile com swipe

## 🎨 **TONE & VOICE VISUAL**

- **Moderno e Profissional**: Sans-serif limpo, espaçamento airy
- **Confiável**: Cores sólidas, tipografia legível
- **Dinâmico**: Laranja vibrante cria energia
- **Acessível**: Alto contraste, texto grande nas seções principais

***

Este design system reflete uma abordagem **clean, scalable e component-based** típica de enterprise SaaS moderno, com forte ênfase em hierarquia visual, CTAs claros e experiência user-centric.