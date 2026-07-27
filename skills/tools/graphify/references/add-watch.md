# graphify reference: adicionar uma URL e observar uma pasta

Carregue isto quando o usuário rodou `/graphify add <url>` ou passou `--watch`. Nenhum dos dois faz parte do build default.

## Para /graphify add

Busque uma URL e adicione-a ao corpus, então atualize o grafo.

```bash
$(cat graphify-out/.graphify_python) -c "
import sys
from graphify.ingest import ingest
from pathlib import Path

try:
    out = ingest('URL', Path('./raw'), author='AUTHOR', contributor='CONTRIBUTOR')
    print(f'Saved to {out}')
except ValueError as e:
    print(f'error: {e}', file=sys.stderr)
    sys.exit(1)
except RuntimeError as e:
    print(f'error: {e}', file=sys.stderr)
    sys.exit(1)
"
```

Substitua `URL` pela URL real, `AUTHOR` pelo nome do usuário se fornecido, `CONTRIBUTOR` idem. Se o comando sair com erro, diga ao usuário o que deu errado — não continue silenciosamente. Depois de um save bem-sucedido, rode automaticamente o pipeline `--update` sobre `./raw` para fazer o merge do novo arquivo no grafo existente.

Tipos de URL suportados (auto-detectados):
- YouTube / qualquer video URL → áudio baixado via yt-dlp, transcrito para `.txt` na próxima run (requer `pip install 'graphifyy[video]'`)
- Twitter/X → buscado via oEmbed, salvo como `.md` com o texto do tweet e autor
- arXiv → abstract + metadata salvos como `.md`
- PDF → baixado como `.pdf`
- Imagens (.png/.jpg/.webp) → baixadas, Claude vision extrai na próxima run
- Qualquer webpage → convertida para markdown via html2text

---

## Para --watch

Inicie um background watcher que monitora uma pasta e auto-atualiza o grafo quando arquivos mudam.

```bash
$(cat graphify-out/.graphify_python) -m graphify.watch INPUT_PATH --debounce 3
```

Substitua INPUT_PATH pela pasta a observar. O comportamento depende do que mudou:

- **Só arquivos de código (.py, .ts, .go, etc.):** re-roda AST extraction + rebuild + cluster imediatamente, sem LLM necessário. `graph.json` e `GRAPH_REPORT.md` são atualizados automaticamente.
- **Docs, papers, ou imagens:** escreve uma flag `graphify-out/needs_update` e imprime uma notificação para rodar `/graphify --update` (LLM semantic re-extraction requerida).

Debounce (default 3s): espera até a atividade de arquivos parar antes de disparar, para que uma onda de writes paralelos de agents não dispare um rebuild por arquivo.

Pressione Ctrl+C para parar.

Para workflows agênticos: rode `--watch` num terminal em background. Mudanças de código de ondas de agents são pegas automaticamente entre ondas. Se os agents também estão escrevendo docs ou notas, você vai precisar de um `/graphify --update` manual depois dessas ondas.
