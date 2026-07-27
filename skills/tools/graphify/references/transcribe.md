# graphify reference: transcrever vídeo e áudio

Carregue isto apenas quando `detect` reportou um ou mais arquivos `video`. Um corpus sem vídeo nunca lê isto.

### Step 2.5 - Transcrever arquivos de vídeo / áudio (só se arquivos de vídeo detectados)

Pule este passo inteiramente se `detect` retornou zero arquivos `video`.

Arquivos de vídeo e áudio não podem ser lidos diretamente. Transcreva-os para texto primeiro, então trate os transcripts como arquivos doc no Step 3.

**Estratégia:** Leia os god nodes de `graphify-out/.graphify_detect.json` (ou o analysis file se ele existir de uma run anterior). Você já é um language model — escreva você mesmo um one-sentence domain hint a partir desses labels. Então passe-o ao Whisper como o initial prompt. Nenhuma API call separada necessária.

**Contudo**, se o corpus tem *apenas* arquivos de vídeo e nenhum outro doc/código, use o generic fallback prompt: `"Use proper punctuation and paragraph breaks."`

**Step 1 - Escreva você mesmo o Whisper prompt.**

Leia os top god node labels do detect output ou analysis, então componha uma short domain hint sentence, por exemplo:

- Labels: `transformer, attention, encoder, decoder` → `"Machine learning research on transformer architectures and attention mechanisms. Use proper punctuation and paragraph breaks."`
- Labels: `kubernetes, deployment, pod, helm` → `"DevOps discussion about Kubernetes deployments and Helm charts. Use proper punctuation and paragraph breaks."`

**Export** it as `GRAPHIFY_WHISPER_PROMPT` (o nome exato que o transcriber lê — e ele deve ser `export`ado para que o child Python process o veja) para o próximo comando.

**Step 2 - Transcreva:**

```bash
export GRAPHIFY_WHISPER_MODEL=base  # or whatever --whisper-model the user passed (must be exported)
export GRAPHIFY_WHISPER_PROMPT="<the one-sentence domain hint you composed in Step 1>"
$(cat graphify-out/.graphify_python) -c "
import json, os, sys
from pathlib import Path
from graphify.transcribe import transcribe_all

detect = json.loads(Path('graphify-out/.graphify_detect.json').read_text(encoding=\"utf-8\"))
video_files = detect.get('files', {}).get('video', [])
prompt = os.environ.get('GRAPHIFY_WHISPER_PROMPT', 'Use proper punctuation and paragraph breaks.')

transcript_paths = transcribe_all(video_files, initial_prompt=prompt)
# Write the JSON from Python (NOT a shell '>' redirect): transcribe_all/Whisper
# print progress to stdout, which would otherwise corrupt the JSON file (#1392).
Path('graphify-out/.graphify_transcripts.json').write_text(json.dumps(transcript_paths, ensure_ascii=False), encoding=\"utf-8\")
print(f'Transcribed {len(transcript_paths)} file(s)', file=sys.stderr)
"
```

Depois da transcrição:
- Leia os transcript paths de `graphify-out/.graphify_transcripts.json`
- Adicione-os à docs list antes de despachar os semantic subagents no Step 3B
- Imprima quantos transcripts foram criados: `Transcribed N video file(s) -> treating as docs`
- Se a transcrição falhar para um arquivo, imprima um warning e continue com o resto

**Whisper model:** Default é `base`. Se o usuário passou `--whisper-model <name>`, `export GRAPHIFY_WHISPER_MODEL=<name>` (ele deve ser exportado, não apenas atribuído) antes de rodar o comando acima.
