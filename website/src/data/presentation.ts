export const repository = "https://github.com/nelsonfrugeri-tech/oh-my-harness";
export const revision = "23fa006da40133bf1abeb90cb23df42716c61f63";
export const sourceFile = (path: string): string =>
  `${repository}/blob/${revision}/${path}`;

interface Reference {
  readonly label: string;
  readonly href: string;
}

export interface Scene {
  readonly id: string;
  readonly label: string;
  readonly chapter: string;
  readonly title: string;
  readonly accent?: string;
  readonly lead: string;
  readonly takeaway: string;
  readonly references: readonly Reference[];
  readonly files: readonly string[];
  readonly note?: string;
}

export const scenes: readonly Scene[] = [
  {
    id: "a-engenharia-permanece",
    label: "A engenharia permanece",
    chapter: "Um método que acompanha você",
    title: "Modelos mudam.\nHarnesses também.",
    accent: "A engenharia permanece.",
    lead: "Conhecimento, critérios e um time de agentes que acompanham seu jeito de construir software.",
    takeaway:
      "oh-my-harness · três problemas do dia a dia, um core compartilhado.",
    references: [],
    files: ["README.md"],
  },
  {
    id: "contexto",
    label: "O contexto ficou preso",
    chapter: "01 / O problema da continuidade",
    title: "Quando o conhecimento\nfica preso à conversa.",
    lead: "A sessão muda. A ferramenta muda. As decisões e o conhecimento precisam acompanhar o trabalho.",
    takeaway:
      "Histórico disponível não significa conhecimento organizado e reutilizável.",
    references: [],
    files: [
      "core/skills/kb-session/SKILL.md",
      "core/skills/kb-retrieval/SKILL.md",
    ],
  },
  {
    id: "convergencia",
    label: "Uma discussão compartilhada",
    chapter: "O mercado também encontra essa dor",
    title: "Como o mercado tem tratado\nmemória e contexto.",
    lead: "Context engineering, harness engineering e conhecimento persistente: três publicações que ajudam a situar essa conversa.",
    takeaway:
      "Contexto, ambiente de execução e conhecimento persistente são problemas relacionados — e diferentes.",
    references: [
      {
        label: "Anthropic · Context engineering",
        href: "https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents",
      },
      {
        label: "OpenAI · Harness engineering",
        href: "https://openai.com/index/harness-engineering/",
      },
      {
        label: "Andrej Karpathy · LLM Wiki",
        href: "https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f",
      },
    ],
    files: [],
    note: "As datas indicam a publicação das fontes citadas, não a invenção dos conceitos. O LLM Wiki é um registro de ideias de Karpathy, não um artigo científico.",
  },
  {
    id: "conhecimento",
    label: "Conhecimento durável",
    chapter: "Pilar / Conhecimento durável",
    title: "O conhecimento fica.\nA sessão pode mudar.",
    lead: "Separar o que aconteceu daquilo que merece continuar válido.",
    takeaway:
      "Markdown e JSON preservam o conhecimento. O índice pode ser reconstruído.",
    references: [],
    files: [
      "harness/claude/agents/tools/knowledge-base.md",
      "core/skills/kb-write/SKILL.md",
      "core/skills/kb-retrieval/SKILL.md",
      "core/skills/kb-infra/SKILL.md",
      "core/hooks/kb-pointer.sh",
    ],
    note: "O hook de início de sessão fornece um pointer para a KB. Ele não injeta a base inteira: retrieval e preservação são operações explícitas. Transcripts são memória episódica; notas curadas e session records mantêm funções distintas.",
  },
  {
    id: "coordenacao",
    label: "Muitas frentes, mais informação",
    chapter: "02 / O problema da coordenação",
    title: "Mais trabalho em paralelo.\nMais coisa pra entender.",
    lead: "Pesquisa, implementação e review produzem respostas que precisam ser legíveis, rastreáveis e comparáveis.",
    takeaway: "Mais frentes pedem clareza, provenance e revisão.",
    note: "A apresentação não afirma que paralelismo causa alucinações. O problema mostrado é a quantidade de afirmações, decisões e fontes que precisam ser acompanhadas.",
    references: [],
    files: [
      "core/skills/didactic-visual/SKILL.md",
      "core/skills/evidence/SKILL.md",
    ],
  },
  {
    id: "governanca",
    label: "Governança epistemológica",
    chapter: "Pilar / Governança epistemológica",
    title: "Foi verificado\nou só parece certo?",
    lead: "Tornar explícitos o status, a origem e os limites das afirmações que orientam uma decisão.",
    takeaway:
      "Um label não é uma prova. É um compromisso com fonte, teste e revisão.",
    references: [],
    files: [
      "core/policies/software-evidence-contract.md",
      "core/skills/evidence/SKILL.md",
      "core/skills/evidence/references/claim-taxonomy.md",
      "harness/claude/CLAUDE.md",
      "harness/codex/AGENTS.md",
    ],
  },
  {
    id: "portabilidade",
    label: "Um operating model portátil",
    chapter: "Pilar / Operating model portátil",
    title: "Trocar de ferramenta.\nPreservar o método.",
    lead: "Papéis, responsabilidades, skills e handoffs evoluem versionados. Cada harness recebe sua representação nativa.",
    takeaway:
      "Os agentes evoluem. A continuidade está nos contratos, não na imutabilidade dos arquivos.",
    references: [],
    files: [
      "core/agents/routing.json",
      ".claude-plugin/plugin.json",
      ".codex-plugin/plugin.json",
    ],
  },
  {
    id: "arquitetura",
    label: "Por dentro do OMH",
    chapter: "Do conceito ao repositório",
    title: "Um core compartilhado.\nAdapters específicos.",
    lead: "A separação entre contrato, integração e estado local organiza a arquitetura do projeto.",
    takeaway:
      "O produto versiona os contratos. A máquina mantém suas configurações e sua knowledge base.",
    references: [],
    files: [
      "core/agents/routing.json",
      "README.md",
      ".claude-plugin/plugin.json",
      ".codex-plugin/plugin.json",
    ],
  },
  {
    id: "adapters",
    label: "O mesmo agente, dois formatos",
    chapter: "Abra no editor / knowledge-base",
    title: "Muda a representação.\nO papel continua.",
    lead: "O agente knowledge-base em Markdown no Claude Code e em TOML no Codex. Trechos reduzidos dos arquivos versionados.",
    takeaway:
      "As skills usam SKILL.md nos dois adapters. Agents, instalação e integração seguem os contratos de cada harness.",
    references: [],
    files: [
      "harness/claude/agents/tools/knowledge-base.md",
      "harness/codex/agents/knowledge-base.toml",
      "core/skills/kb-write/SKILL.md",
    ],
  },
  {
    id: "fluxo",
    label: "Da intenção à entrega",
    chapter: "O fluxo que vamos demonstrar",
    title: "Código é uma etapa.\nEngenharia é o fluxo.",
    lead: "Uma mudança pequena, critérios claros e revisão independente para tornar o processo inspecionável.",
    takeaway:
      "Roteiro de demonstração a preparar: uma issue open source ou uma feature com escopo verificável.",
    references: [],
    files: [
      "core/skills/feature/SKILL.md",
      "core/skills/implement/SKILL.md",
      "core/skills/test/SKILL.md",
      "core/skills/review/SKILL.md",
      "core/hooks/quality-gate.sh",
    ],
  },
  {
    id: "o-que-permanece",
    label: "O que você preserva?",
    chapter: "A conversa continua",
    title: "Quando você troca de\nmodelo ou harness,",
    accent: "o que consegue preservar?",
    lead: "Do seu conhecimento. Dos seus critérios. Do seu jeito de construir software.",
    takeaway:
      "Explore os contratos, acompanhe o projeto e contribua com os problemas que você encontra.",
    references: [],
    files: ["README.md"],
  },
];
